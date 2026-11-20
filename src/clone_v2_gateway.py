"""Clone-only B2: fail-closed, key-authenticated Oracle gateway connection probe.

This is a NEW clone V2 endpoint contract, not an alias of legacy /dhan routes
or any previous V2 pilot. No Dhan token or trading order is handled by phone.
The server must independently implement and authorize /clone-v2/status before
the clone may claim it is connected. No fallback to original V1 server paths.
"""
from __future__ import annotations

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
            if exc.code == 429:
                raise FeedError("Clone Dhan quote lane paced; retry later") from None
            raise FeedError("Clone market route not ready (HTTP " + str(exc.code) + ")") from None
        except (URLError, OSError, TimeoutError, ValueError, UnicodeError):
            raise FeedError("Clone market data unavailable") from None
        if (not isinstance(payload, dict) or payload.get("source") != "dhan"
                or payload.get("live_orders_enabled") is not False
                or payload.get("freshness") != "unverified"
                or not isinstance(payload.get("quotes"), dict)
                or not isinstance(payload.get("unavailable"), list)):
            raise FeedError("Clone market contract invalid")
        validated = {}
        for name, item in payload["quotes"].items():
            if (name not in symbols or not isinstance(item, dict)
                    or item.get("symbol") != name or item.get("source") != "dhan"
                    or item.get("freshness") != "unverified"):
                raise FeedError("Clone market symbol/source mismatch")
            price = item.get("ltp")
            if type(price) not in (int, float) or not math.isfinite(price) or price <= 0:
                raise FeedError("Clone market invalid quote")
            validated[name] = float(price)
        if (not validated or len(payload["unavailable"]) != len(set(payload["unavailable"]))
                or any(not isinstance(x, str) or x not in symbols for x in payload["unavailable"])
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


class CloneDhanReadOnly:
    """B3 market-data bridge. No legacy /dhan or /v2 endpoint ever contacted."""

    def __init__(self, gateway):
        self.gateway = gateway
        self._verified_dynamic_equities = set()
        self._selected_batch_missing = False
        self._historical_only = False
        self._cooldowns = {}

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
        if not self.gateway.connected or type(quote) is not dict or not quote:
            raise FeedError("Clone Dhan quote proof missing")
        self._market_verified = True

    def cooldown_remaining(self, path):
        import time
        return max(0, self._cooldowns.get(path, 0.0) - time.monotonic())

    def _fetch(self, symbols):
        import time
        try:
            return self.gateway.market_quotes(list(symbols))
        except FeedError as exc:
            if "paced" in str(exc):
                self._cooldowns["/dhan/selected-ltp-batch"] = time.monotonic() + 2
                self._cooldowns["/dhan/index-ltp-batch"] = time.monotonic() + 2
            raise

    def quote(self, symbol):
        result = self._fetch([symbol])
        if symbol not in result:
            raise FeedError("Verified Clone Dhan symbol unavailable")
        return {"symbol": symbol, "price": result[symbol],
                "source": "Dhan", "freshness": "unverified", "quote_timestamp": None}

    def index_batch_quotes(self):
        names = ("NIFTY", "BANKNIFTY", "SENSEX")
        prices = self._fetch(names)
        return {s: {"symbol": s, "price": p, "source": "Dhan",
                    "quote_timestamp": None, "freshness": "unverified",
                    "live_verified": False}
                for s, p in prices.items() if s in names}

    def selected_equity_quotes(self, symbols):
        if (not isinstance(symbols, (list, tuple)) or not 1 <= len(symbols) <= 70
                or any(not isinstance(x, str) or x in ("NIFTY", "BANKNIFTY", "SENSEX")
                       for x in symbols) or len(set(symbols)) != len(symbols)):
            raise FeedError("Invalid Clone selected equity symbols")
        prices = self._fetch(symbols)
        return {s: {"symbol": s, "price": p, "source": "Dhan",
                    "quote_timestamp": None, "freshness": "unverified",
                    "live_verified": False}
                for s, p in prices.items()}

    def equity_quotes_for_watchlist(self, symbols):
        if not symbols:
            return {}
        return self.selected_equity_quotes(symbols)

    def verified_equity_symbol(self, symbol):
        # Dynamic symbols MUST be established by a separate trusted registry
        # endpoint; do not claim verification merely from local app spelling.
        raise FeedError("Clone instrument registry verification not connected")

    def batch_quotes(self):
        raise FeedError("Clone snapshot API not configured; use selected roster")

    def intraday(self, symbol, interval, from_date, to_date):
        raise FeedError("Clone Dhan historical candle API not connected")

    def assessment(self, symbol, *, timeframe=None, expiry=None):
        raise FeedError("Clone assessment evidence API not connected")

    def option_expiries(self, symbol):
        raise FeedError("Clone Dhan option expiry API not connected")

    def option_chain_metrics(self, symbol, expiry):
        raise FeedError("Clone Dhan option chain API not connected")

    def server_readiness(self):
        return {"orders": {"broker_submission_allowed": False,
                           "live_orders_enabled": False},
                "live_orders_enabled": False}
