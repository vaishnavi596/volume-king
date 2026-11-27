"""Clone-only B2: fail-closed, key-authenticated Oracle gateway connection probe.

This is a NEW clone V2 endpoint contract, not an alias of legacy /dhan routes
or any previous V2 pilot. No Dhan token or trading order is handled by phone.
The server must independently implement and authorize /clone-v2/status before
the clone may claim it is connected. No fallback to original V1 server paths.
"""
from __future__ import annotations
import time

import json
import math
import urllib.error
from urllib.error import HTTPError, URLError
from urllib.request import Request

from server_feed import FeedError, server_origin, checked_pairing_key, direct_https_opener

STATUS_PATH = "/clone-v2/status"
EXPECTED_PROTOCOL = "botking-clone-v2"
MAX_STATUS_BYTES = 2048


class CloneV2Gateway:
    """One validated read-only handshake; key stays in memory, not preferences."""

    def __init__(self, *, opener=None):
        self._opener = opener
        self._origin = ""
        self._key = ""

    @property
    def connected(self):
        return bool(self._origin and self._key)

    def disconnect(self):
        self._origin = ""
        self._key = ""



    def renewal_health(self):
        """Authenticated metadata-only read; old deployments remain unverified."""
        if not self.connected:
            return {"state":"UNVERIFIED","reason":"DISCONNECTED"}
        origin,key=self._origin,self._key
        url=origin+"/clone-v2/renewal-health"
        request=Request(url,method="GET",headers={"X-BotKing-Key":key,
            "Accept":"application/json","Cache-Control":"no-store"})
        try:
            with (self._opener or direct_https_opener()).open(request,timeout=8) as response:
                if (response.status!=200 or response.geturl()!=url
                        or response.headers.get_content_type()!="application/json"):
                    raise ValueError("Untrusted renewal response")
                raw=response.read(2049)
                if len(raw)>2048:raise ValueError("Oversized renewal response")
                data=json.loads(raw.decode("utf-8"))
            if (self._origin,self._key)!=(origin,key):
                raise ValueError("Connection changed")
            if (not isinstance(data,dict) or set(data)!={"protocol","state","metadata_verified",
                    "renewal_observed","timer_verified","provider_requests","orders_sent"}
                    or data["protocol"]!="clone-renewal-health-v1"
                    or data["state"] not in ("UNVERIFIED","VALID","RENEWAL_DUE","EXPIRED")
                    or data["metadata_verified"] is not (data["state"]!="UNVERIFIED")
                    or data["renewal_observed"] is not False or data["timer_verified"] is not False
                    or type(data["provider_requests"]) is not int or data["provider_requests"]!=0
                    or type(data["orders_sent"]) is not int or data["orders_sent"]!=0):
                raise ValueError("Invalid renewal contract")
            if data["state"]=="UNVERIFIED":
                return dict(data,reason="SERVER_METADATA_UNVERIFIED")
            return data
        except HTTPError as exc:
            reason={401:"RENEWAL_ROUTE_AUTH_REJECTED",403:"RENEWAL_ROUTE_AUTH_REJECTED",404:"RENEWAL_ROUTE_NOT_DEPLOYED",405:"RENEWAL_ROUTE_NOT_DEPLOYED",502:"RENEWAL_GATEWAY_UNAVAILABLE",503:"RENEWAL_GATEWAY_UNAVAILABLE",504:"RENEWAL_GATEWAY_UNAVAILABLE"}.get(exc.code,"RENEWAL_ROUTE_HTTP_ERROR")
            return {"state":"UNVERIFIED","reason":reason}
        except (OSError,URLError,ValueError,UnicodeError,RecursionError):
            return {"state":"UNVERIFIED","reason":"ROUTE_OR_METADATA_UNAVAILABLE"}

    def paper_heartbeat(self):
        """B244: read-only server paper-engine heartbeat (no orders, no Dhan call)."""
        if not self.connected:
            return {"reachable":False,"reason":"DISCONNECTED"}
        origin,key=self._origin,self._key
        url=origin+"/clone-v2/paper/heartbeat"
        request=Request(url,method="GET",headers={"X-BotKing-Key":key,
            "Accept":"application/json","Cache-Control":"no-store"})
        try:
            with (self._opener or direct_https_opener()).open(request,timeout=8) as response:
                if (response.status!=200 or response.geturl()!=url
                        or response.headers.get_content_type()!="application/json"):
                    raise ValueError("Untrusted heartbeat response")
                raw=response.read(4097)
                if len(raw)>4096:raise ValueError("Oversized heartbeat")
                data=json.loads(raw.decode("utf-8"))
            if (not isinstance(data,dict) or data.get("mode")!="PAPER"
                    or data.get("live_orders_enabled") is not False):
                raise ValueError("Invalid heartbeat contract")
            keep=("mode","uptime_seconds","last_eval_age_seconds","open_count","closed_count","open_symbols","last_error")
            return dict({k:data.get(k) for k in keep},reachable=True,live_orders_enabled=False)
        except HTTPError as exc:
            return {"reachable":False,"reason":"HEARTBEAT_ROUTE_HTTP_"+str(exc.code)}
        except (OSError,URLError,ValueError,UnicodeError,RecursionError):
            return {"reachable":False,"reason":"HEARTBEAT_UNAVAILABLE"}

    def start_dhan_browser_login(self, endpoint, access_key):
        """Request Clone-only browser consent; return trusted official Dhan URL."""
        from urllib.parse import urlsplit, parse_qs
        origin = server_origin(endpoint)
        key = checked_pairing_key(access_key)
        url = origin + "/clone-v2/dhan/start"
        request = Request(url, data=b"", method="POST",
                          headers={"X-BotKing-Key": key,
                                   "Accept": "application/json",
                                   "Cache-Control": "no-store"})
        try:
            with (self._opener or direct_https_opener()).open(request, timeout=16) as response:
                if (response.status != 200 or response.geturl() != url or
                        response.headers.get_content_type() != "application/json"):
                    raise FeedError("Clone Dhan consent response not trusted")
                raw = response.read(8193)
                if len(raw) > 8192:
                    raise FeedError("Clone Dhan consent response too large")
                result = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                raise FeedError("Clone SSK access denied; check server key") from None
            if exc.code == 409:
                raise FeedError("Clone Dhan browser login already pending") from None
            if exc.code == 429:
                raise FeedError("Clone Dhan consent cooldown; retry later") from None
            if exc.code == 503:
                raise FeedError("Clone Dhan browser login not configured on Oracle") from None
            raise FeedError("Clone Dhan browser login HTTP " + str(exc.code)) from None
        except (OSError, URLError, TimeoutError, ValueError, UnicodeError):
            raise FeedError("Clone Dhan browser authorization unavailable") from None
        if not isinstance(result, dict) or result.get("live_orders_enabled") is not False:
            raise FeedError("Clone Dhan browser response invalid")
        link = result.get("login_url")
        if not isinstance(link, str) or len(link) > 1000:
            raise FeedError("Clone Dhan login link invalid")
        parsed = urlsplit(link)
        params = parse_qs(parsed.query)
        if (parsed.scheme != "https" or parsed.hostname != "auth.dhan.co" or
                parsed.path != "/login/consentApp-login" or parsed.username or
                parsed.password or parsed.port or parsed.fragment or
                set(params) != {"consentAppId"} or len(params["consentAppId"]) != 1):
            raise FeedError("Clone Dhan login link not trusted")
        return link

    def post_market(self, route, selection):
        if not self.connected:
            raise FeedError("Clone SSK connection required")
        if route not in ("candles", "verify", "options/expiries", "options/chain",
                         "futures/context"):
            raise FeedError("Unsupported Clone Dhan read-only route")
        url = self._origin + "/clone-v2/market/" + route
        req = Request(url, data=json.dumps(selection, allow_nan=False).encode("utf-8"),
                      headers={"X-BotKing-Key": self._key,
                               "Content-Type": "application/json",
                               "Accept": "application/json",
                               "Cache-Control": "no-store"}, method="POST")
        try:
            with (self._opener or direct_https_opener()).open(req, timeout=25) as resp:
                if (resp.status != 200 or resp.geturl() != url or
                        resp.headers.get_content_type() != "application/json"):
                    raise FeedError("Clone market route response untrusted")
                content = resp.read(2000001)
                if len(content) > 2000000:
                    raise FeedError("Clone market response too large")
                output = json.loads(content.decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                self.disconnect()
                raise FeedError("Clone SSK authorization expired (HTTP " + str(exc.code) + ")") from None
            if exc.code == 424:
                raise FeedError("Clone Dhan authorization required (HTTP 424)") from None
            if exc.code == 429:
                raise FeedError("Clone Dhan rate limit; retry later (HTTP 429)") from None
            if exc.code in (502, 503, 504):
                raise FeedError("Clone Dhan upstream or gateway unavailable (HTTP " + str(exc.code) + ")") from None
            raise FeedError("Clone market " + route + " HTTP " + str(exc.code)) from None
        except (TimeoutError,):
            raise FeedError("Clone Dhan " + route + " transport timeout") from None
        except (ValueError, UnicodeError):
            raise FeedError("Clone Dhan " + route + " invalid response encoding or JSON") from None
        except (OSError, URLError):
            raise FeedError("Clone Dhan " + route + " transport unavailable") from None
        if (not isinstance(output, dict) or output.get("live_orders_enabled") is not False):
            raise FeedError("Unsafe Clone Dhan response")
        return output

    def market_quotes(self, symbols):
        """Phone→Clone→Dhan read-only request; never accepts fake broker quotes."""
        if not self.connected:
            raise FeedError("Clone SSK connection required")
        if (not isinstance(symbols, list) or not 1 <= len(symbols) <= 73
                or any(not isinstance(s, str) or not s or len(s) > 32 for s in symbols)
                or len(set(symbols)) != len(symbols)):
            raise FeedError("Invalid Clone market symbol selection")
        url = self._origin + "/clone-v2/market/quotes"
        req = Request(url, data=json.dumps({"symbols": symbols}).encode("utf-8"),
                      headers={"X-BotKing-Key": self._key,
                               "Accept": "application/json",
                               "Content-Type": "application/json",
                               "Cache-Control": "no-store"}, method="POST")
        try:
            with (self._opener or direct_https_opener()).open(req, timeout=20) as response:
                if response.status != 200 or response.geturl() != url:
                    raise FeedError("Clone market response not trusted")
                if response.headers.get_content_type() != "application/json":
                    raise FeedError("Clone market response type invalid")
                raw = response.read(1000001)
                if len(raw) > 1000000:
                    raise FeedError("Clone market response too large")
                payload = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            if exc.code in (401, 403):
                self.disconnect()
                raise FeedError("Clone market session rejected; reconnect") from None
            if exc.code == 424:
                raise FeedError("Dhan authorization required. Use Authorize Dhan in Browser (Clone), then SSK Connect") from None
            if exc.code == 429:
                # Accept only a tiny, fixed enum supplied by our Clone gateway.
                # Never surface arbitrary upstream bodies or untrusted headers.
                headers=getattr(exc,"headers",None)
                stage=headers.get("X-BotKing-429-Stage","") if headers is not None else ""
                if stage=="GATEWAY_PACING":
                    raise FeedError("Clone Dhan quote lane paced; retry later") from None
                if stage in ("PROVIDER_QUOTA","PROVIDER_COOLDOWN"):
                    raise FeedError("Clone Dhan provider rate limit; retry later") from None
                raise FeedError("Clone Dhan quote rate limit; retry later") from None
            if exc.code in (502, 503, 504):
                # A proxy-generated 502 may not have reached FastAPI at all.
                # Only our own fixed gateway stage header can distinguish it.
                stage=(exc.headers.get("X-BotKing-Quote-Failure-Stage", "")
                       if getattr(exc, "headers", None) is not None else "")
                state=(exc.headers.get("X-BotKing-Quote-Response-State", "")
                       if getattr(exc, "headers", None) is not None else "")
                if stage=="RESPONSE" and state=="EMPTY_SEGMENTS":
                    raise FeedError("Clone Dhan quote provider data empty; retry later") from None
                if stage in ("PROVIDER", "RESPONSE"):
                    raise FeedError("Clone Dhan quote upstream " + stage.lower() +
                                    " failed (HTTP " + str(exc.code) + ")") from None
                raise FeedError("Clone Oracle/quote route HTTP " + str(exc.code) +
                                " • failure stage unverified; check gateway and proxy logs") from None
            raise FeedError("Clone market route not ready (HTTP " + str(exc.code) + ")") from None
        except (URLError, OSError, TimeoutError, ValueError, UnicodeError):
            raise FeedError("Clone market data unavailable") from None
        if (not isinstance(payload, dict) or payload.get("source") != "dhan"
                or payload.get("live_orders_enabled") is not False
                or payload.get("freshness") != "unverified"
                or not isinstance(payload.get("quotes"), dict)
                or not isinstance(payload.get("unavailable"), list)):
            raise FeedError("Clone market contract invalid")
        validated = QuotePriceBatch()
        for name, item in payload["quotes"].items():
            if (name not in symbols or not isinstance(item, dict)
                    or item.get("symbol") != name or item.get("source") != "dhan"
                    or item.get("freshness") != "unverified"):
                raise FeedError("Clone market symbol/source mismatch")
            price = item.get("ltp")
            if type(price) not in (int, float) or not math.isfinite(price) or price <= 0:
                raise FeedError("Clone market invalid quote")
            validated[name] = float(price)
            stamp = item.get("exchange_trade_timestamp")
            if (item.get("timestamp_origin")=="DHAN_QUOTE_LAST_TRADE_TIME"
                    and type(stamp) in (int,float) and math.isfinite(stamp)
                    and 946684800<=stamp<=time.time()):
                validated.trade_timestamps[name]=stamp
        # Validate element types before hashing untrusted response values.
        # Existing FeedError reporting must receive a bounded, redacted error.
        if any(not isinstance(x, str) or x not in symbols for x in payload["unavailable"]):
            raise FeedError("BK-QUOTE-001: Clone market no validated quotes; invalid unavailable symbol")
        if (not validated or len(payload["unavailable"]) != len(set(payload["unavailable"]))
                or set(validated).intersection(payload["unavailable"])
                or set(validated).union(payload["unavailable"]) != set(symbols)):
            raise FeedError("Clone market no validated quotes")
        return validated

    def connect(self, endpoint, access_key):
        """Fail closed unless the NEW gateway proves its authenticated contract.

        An HTTP 200 from /health or /dhan/status never establishes clone-V2
        authorization. No market-data read, fallback or auto-login occurs here.
        """
        self.disconnect()
        origin = server_origin(endpoint)
        key = checked_pairing_key(access_key)
        url = origin + STATUS_PATH
        request = Request(url, method="GET", headers={
            "X-BotKing-Key": key,
            "Accept": "application/json",
            "Cache-Control": "no-store",
        })
        try:
            with (self._opener or direct_https_opener()).open(request, timeout=12) as response:
                if response.status != 200 or response.geturl() != url:
                    raise FeedError("Clone V2 gateway response not trusted")
                if response.headers.get_content_type() != "application/json":
                    raise FeedError("Clone V2 gateway response type invalid")
                raw = response.read(MAX_STATUS_BYTES + 1)
                if len(raw) > MAX_STATUS_BYTES:
                    raise FeedError("Clone V2 gateway response too large")
                status = json.loads(raw.decode("utf-8"))
        except HTTPError as exc:
            if exc.code == 404:
                raise FeedError("Clone V2 gateway not deployed (HTTP 404)") from None
            if exc.code in (401, 403):
                raise FeedError("Clone V2 server access denied") from None
            if exc.code == 429:
                raise FeedError("Clone V2 gateway rate limited; do not retry immediately") from None
            raise FeedError("Clone V2 gateway unavailable") from None
        except (URLError, OSError, TimeoutError, ValueError, UnicodeError):
            raise FeedError("Clone V2 gateway connection failed") from None
        if (type(status) is not dict or
                set(status) != {"protocol", "authenticated", "read_only",
                                "live_orders_enabled", "pipeline", "status"} or
                status["protocol"] != EXPECTED_PROTOCOL or
                status["authenticated"] is not True or
                status["read_only"] is not True or
                status["live_orders_enabled"] is not False or
                status["pipeline"] != "dhan-oracle-clone" or
                status["status"] != "ready"):
            raise FeedError("Clone V2 gateway authorization not verified")
        self._origin, self._key = origin, key
        return {"status": "connected_read_only", "live_market_data_verified": False}


class QuotePriceBatch(dict):
    """Keep the established symbol→float contract with per-response metadata."""
    def __init__(self):
        super().__init__()
        self.trade_timestamps = {}


def observed_quote_fields(prices, symbol):
    timestamps = getattr(prices, "trade_timestamps", {})
    stamp = timestamps.get(symbol) if isinstance(timestamps, dict) and symbol in prices else None
    if not (type(stamp) in (int,float) and math.isfinite(stamp)
            and 946684800 <= stamp <= time.time()):
        stamp = None
    return {"quote_timestamp": stamp, "freshness": "unverified",
            "live_verified": False,
            "timestamp_origin": "DHAN_QUOTE_LAST_TRADE_TIME" if stamp is not None else None}


class CloneDhanReadOnly:
    """B3 market-data bridge. No legacy /dhan or /v2 endpoint ever contacted."""

    def __init__(self, gateway):
        self.gateway = gateway
        self._verified_dynamic_equities = set()
        self._selected_batch_missing = False
        self._historical_only = False
        self._cooldowns = {}
        # All phone quote lanes share one serialized gate. Oracle needs >=1.05s
        # between provider misses; allow headroom without increasing fanout.
        import threading
        self._quote_lane_lock = threading.Lock()
        self._quote_lane_last_attempt = 0.0

    @property
    def connected(self):
        return self.gateway.connected and getattr(self, "_market_verified", False)

    @property
    def historical_only(self):
        return self.connected and self._historical_only

    def disconnect(self):
        self._market_verified = False
        self.gateway.disconnect()

    def activate_with_quote(self, quote):
        if (not self.gateway.connected or not isinstance(quote,dict) or not quote
                or any(not isinstance(symbol,str) or not symbol.strip()
                       or type(price) not in (int,float) or not math.isfinite(price) or price<=0
                       for symbol,price in quote.items())):
            self._market_verified=False
            raise FeedError("Clone Dhan quote proof missing")
        self._market_verified = True

    def cooldown_remaining(self, path):
        import time
        return max(0, self._cooldowns.get(path, 0.0) - time.monotonic())

    def paced_market_quotes(self, symbols):
        """One Dhan-only phone quote lane, including initial SSK login proof.

        A status-authenticated gateway is sufficient for the first quote proof;
        no verified market session is asserted until caller validates response.
        """
        if not self.gateway.connected:
            raise FeedError("Clone SSK connection required")
        return self._fetch(symbols)

    def _fetch(self, symbols):
        import time
        # Serialize index/equity/individual quotes within this phone, including
        # asyncio.to_thread callers. Never launch a queued request during a
        # previously observed provider-wide 429 cooldown.
        with self._quote_lane_lock:
            cooldown = max((self.cooldown_remaining(route) for route in
                ("/dhan/selected-ltp-batch", "/dhan/index-ltp-batch")), default=0)
            if cooldown > 0:
                raise FeedError("Clone Dhan quote cooldown active; retry later")
            delay = 1.15 - (time.monotonic() - self._quote_lane_last_attempt)
            if self._quote_lane_last_attempt > 0 and delay > 0:
                time.sleep(delay)
            self._quote_lane_last_attempt = time.monotonic()
            try:
                return self.gateway.market_quotes(list(symbols))
            except FeedError as exc:
                if ("paced" in str(exc) or "rate limit" in str(exc)
                        or "provider data empty" in str(exc)):
                    # Only local gateway pacing uses 2s. Actual or unknown
                    # provider quota failures retain the full 30s safety floor.
                    cooldown_seconds = 2 if "quote lane paced" in str(exc) else 30
                    until = time.monotonic() + cooldown_seconds
                    for route in ("/dhan/selected-ltp-batch", "/dhan/index-ltp-batch"):
                        self._cooldowns[route] = max(self._cooldowns.get(route, 0.0), until)
                raise

    def quote(self, symbol):
        result = self._fetch([symbol])
        if symbol not in result:
            raise FeedError("Verified Clone Dhan symbol unavailable")
        return {"symbol": symbol, "price": result[symbol],
                "source": "Dhan", **observed_quote_fields(result, symbol)}

    def index_batch_quotes(self):
        names = ("NIFTY", "BANKNIFTY", "SENSEX")
        prices = self._fetch(names)
        return {s: {"symbol": s, "price": p, "source": "Dhan",
                    **observed_quote_fields(prices, s)}
                for s, p in prices.items() if s in names}

    def selected_equity_quotes(self, symbols):
        if (not isinstance(symbols, (list, tuple)) or not 1 <= len(symbols) <= 70
                or any(not isinstance(x, str) or x in ("NIFTY", "BANKNIFTY", "SENSEX")
                       for x in symbols) or len(set(symbols)) != len(symbols)):
            raise FeedError("Invalid Clone selected equity symbols")
        prices = self._fetch(symbols)
        return {s: {"symbol": s, "price": p, "source": "Dhan",
                    **observed_quote_fields(prices, s)}
                for s, p in prices.items()}

    def equity_quotes_for_watchlist(self, symbols):
        if not symbols:
            return {}
        return self.selected_equity_quotes(symbols)

    def verified_equity_symbol(self, symbol):
        # Dynamic symbols MUST be established by a separate trusted registry
        # endpoint; do not claim verification merely from local app spelling.
        if not isinstance(symbol, str):
            raise FeedError("Invalid Clone equity symbol")
        result = self.gateway.post_market("verify", {"symbol": symbol})
        if (result.get("source") != "dhan_registry" or
                result.get("symbol") != symbol or result.get("verified") is not True):
            raise FeedError("Clone equity symbol registry unverified")
        self._verified_dynamic_equities.add(symbol)
        return True

    def batch_quotes(self):
        from server_feed import DHAN_VERIFIED_EQUITY_SYMBOLS
        return self.selected_equity_quotes(sorted(DHAN_VERIFIED_EQUITY_SYMBOLS))

    def equity_quotes_with_bootstrap(self):
        return self.batch_quotes()

    def _call(self, path, payload=None):
        # Hard stop: no Clone B3 request may fall back to V1 or old pilot.
        raise FeedError("Unsupported Clone B3 market request")

    def intraday(self, symbol, interval, from_date, to_date):
        if interval not in (1, 5, 15, 25, 60):
            raise FeedError("Clone unsupported candle interval")
        response = self.gateway.post_market("candles", {
            "symbol": symbol, "interval": interval,
            "from_date": str(from_date), "to_date": str(to_date)})
        if (response.get("source") != "dhan" or response.get("symbol") != symbol or
                response.get("interval") != str(interval) + "m" or
                not isinstance(response.get("bars"), list) or
                response.get("freshness") not in ("historical_unverified", "no_candles_available")):
            raise FeedError("Clone candle response not verified")
        # An optional digest from the updated Clone Gateway verifies that
        # normalized OHLCV arrived unchanged. Old deployments without this
        # field remain supported, but transport parity stays unverified.
        import hashlib
        digest=response.get("normalized_bars_sha256")
        if digest is not None:
            expected=hashlib.sha256(json.dumps(
                response["bars"], separators=(",",":"), allow_nan=False
            ).encode("utf-8")).hexdigest()
            if type(digest) is not str or digest != expected:
                raise FeedError("Clone candle normalized transport digest mismatch")
            response["normalized_transport_integrity"]="SHA256_MATCH"
        else:
            response["normalized_transport_integrity"]="NOT_PROVIDED"
        return response

    def assessment(self, symbol, *, timeframe=None, expiry=None):
        import re
        if (not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9&-]{1,40}", symbol)
                or timeframe not in (None, "1m", "3m", "5m")):
            raise FeedError("Invalid Clone assessment selection")
        if expiry is not None:
            from datetime import date
            try:
                if date.fromisoformat(expiry).isoformat() != expiry:
                    raise ValueError()
            except (ValueError, TypeError):
                raise FeedError("Invalid Clone assessment expiry") from None
        # No directional score until independent time/expiry evidence is verified.
        return {
            "symbol": symbol, "source": "dhan", "timeframe": timeframe,
            "expiry": expiry, "collection_status": "not_configured",
            "freshness": "unverified", "assessment_filters": [
                {"id": key, "status": "unavailable", "reason": "not_configured"}
                for key in ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")],
            "factors": {key: {"status": "unavailable", "bullish": None, "bearish": None}
                        for key in ("news", "futures", "options", "candle")},
            "bullish_score": None, "bearish_score": None,
            "signal_eligible": False, "live_orders_enabled": False}

    def option_expiries(self, symbol):
        response = self.gateway.post_market("options/expiries", {"symbol": symbol})
        dates = response.get("expiries")
        if (response.get("source") != "dhan" or response.get("symbol") != symbol or
                not isinstance(dates, list) or not dates or
                any(not isinstance(d, str) or len(d) != 10 for d in dates) or
                dates != sorted(set(dates))):
            raise FeedError("Clone listed option expiries invalid")
        return dates

    def option_chain_metrics(self, symbol, expiry):
        response = self.gateway.post_market("options/chain", {
            "symbol": symbol, "expiry": expiry})
        if (response.get("source") != "dhan" or response.get("symbol") != symbol or
                response.get("expiry") != expiry or
                response.get("freshness") != "unverified" or
                response.get("signal_eligible") is not False or
                any(type(response.get(k)) not in (int, float) for k in ("pcr", "max_pain")) or
                not math.isfinite(response["pcr"]) or response["pcr"] < 0 or
                not math.isfinite(response["max_pain"]) or response["max_pain"] <= 0):
            raise FeedError("Clone option evidence unavailable")
        return response

    def futures_context(self, symbol, expiry):
        """Read mapped Dhan NSE_FNO context; never certify a directional vote.

        Server mapping is operator-controlled. The phone supplies only the
        requested underlying and expiry, never a security ID.
        """
        from datetime import date
        if (not isinstance(symbol,str) or not symbol
                or not isinstance(expiry,str)):
            raise FeedError("Exact futures symbol and expiry required")
        try:
            parsed=date.fromisoformat(expiry)
        except ValueError:
            raise FeedError("Invalid futures expiry") from None
        if parsed.isoformat()!=expiry:
            raise FeedError("Invalid futures expiry")
        response=self.gateway.post_market("futures/context", {
            "symbol":symbol,"expiry":expiry})
        price=response.get("ltp")
        contract=response.get("contract")
        if (response.get("source")!="dhan"
                or response.get("symbol")!=symbol
                or response.get("underlying")!=symbol
                or response.get("expiry")!=expiry
                or response.get("exchange_segment")!="NSE_FNO"
                or response.get("mapping_verified") is not True
                or not isinstance(contract,str) or not contract.strip()
                or type(price) not in (int,float) or not math.isfinite(price)
                or price<=0
                or response.get("freshness")!="unverified"
                or response.get("direction_verified") is not False
                or response.get("signal_eligible") is not False
                or response.get("live_orders_enabled") is not False
                or response.get("direction") is not None):
            raise FeedError("Clone futures context provenance unavailable")
        return response

    def server_readiness(self):
        return {"orders": {"broker_submission_allowed": False,
                           "live_orders_enabled": False},
                "live_orders_enabled": False}
