"""Optional owner-operated HTTPS transport for the read-only Angel adapter."""
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from market_feed import AngelFeed, FeedError, SessionExpired


def direct_https_opener():
    """Do not route BOT KING credentials through environment-configured proxies.

    Android/Python can inherit HTTP(S)_PROXY settings. The owner-controlled
    HTTPS origin is validated by server_origin before use. TLS certificate
    validation remains enabled; redirects are refused.
    """
    return urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Never forward a credential or session to another URL.


def server_origin(value):
    value = value.strip().rstrip("/")
    try:
        url = urllib.parse.urlsplit(value)
        valid = (url.scheme == "https" and url.hostname and not url.username
                 and not url.password and url.port in (None, 443)
                 and not url.path and not url.query and not url.fragment)
    except ValueError:
        valid = False
    if not valid:
        raise FeedError("Use only your trusted server's HTTPS origin, without a path")
    return value


class ServerAngelFeed(AngelFeed):
    def __init__(self):
        super().__init__()
        self.server = ""

    @property
    def connected(self):
        return bool(self.token) if self.server else super().connected

    def _call(self, path, payload, pairing_key="", token=None, origin=None):
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        if pairing_key:
            headers["X-BotKing-Key"] = pairing_key
        else:
            headers["Authorization"] = "Bearer " + (self.token if token is None else token)
        req = urllib.request.Request((origin or self.server) + path,
                                     data=json.dumps(payload, allow_nan=False).encode(),
                                     headers=headers, method="POST")
        try:
            with direct_https_opener().open(req, timeout=45) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
                if len(raw) > 4 * 1024 * 1024:
                    raise FeedError("Server response too large")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            # Only expose a fixed, non-sensitive explanation; never echo server
            # response bodies, broker credentials, tokens or upstream traces.
            if exc.code == 401 and path != "/v1/login":
                self.disconnect()
                raise SessionExpired("Server session expired; reconnect") from None
            if exc.code == 401:
                raise FeedError("Angel One login rejected (HTTP 401): check Client Code, MPIN, API Key and current TOTP") from None
            if exc.code == 403:
                raise FeedError("Server access denied (HTTP 403): verify Server Access Key") from None
            if exc.code == 422:
                raise FeedError("Invalid login fields (HTTP 422): verify all required fields and 6-digit TOTP") from None
            if exc.code == 429:
                raise FeedError("Server busy or login rate limited (HTTP 429); wait before retrying") from None
            if exc.code in (502, 503, 504):
                raise FeedError("Gateway or upstream unavailable (HTTP " + str(exc.code) + ")") from None
            raise FeedError("Server rejected request (HTTP " + str(exc.code) + ")") from None
        except FeedError:
            raise
        except Exception:
            raise FeedError("Server connection failed; verify HTTPS and network") from None

    def connect(self, key, client, pin, totp, endpoint="", pairing_key=""):
        self.disconnect()
        if not endpoint.strip():
            self.server = ""
            return super().connect(key, client, pin, totp)
        origin = server_origin(endpoint)
        if not pairing_key.strip() or not all((key, client, pin, totp)):
            raise FeedError("Enter server access key and all Angel One login fields")
        generation = self.epoch
        result = self._call("/v1/login", {"api_key": key, "client_code": client,
                           "pin": pin, "totp": totp}, pairing_key=pairing_key.strip(), origin=origin)
        if generation != self.epoch:
            try:
                self._call("/v1/logout", {}, token=result.get("session", ""), origin=origin)
            except FeedError:
                pass
            raise FeedError("Connection cancelled")
        if not isinstance(result, dict) or not isinstance(result.get("session"), str) or not result["session"]:
            raise FeedError("Server did not return a valid session")
        self.server = origin
        self.token = result["session"]
        self.key = ""  # Broker API key/JWT stay on the server, never in the response.
        self.client = ""

    def revoke(self):
        """Use from a worker thread; local disconnect always completes."""
        try:
            if self.server and self.token:
                self._call("/v1/logout", {})
        finally:
            self.disconnect()

    def history(self, symbol, interval, period):
        if not self.server:
            return super().history(symbol, interval, period)
        return self._call("/v1/history", dict(symbol=symbol, interval=interval, period=period))

    def expiries(self, symbol):
        if not self.server:
            return super().expiries(symbol)
        return self._call("/v1/expiries", dict(symbol=symbol))

    def option_chain(self, symbol, expiry, spot):
        if not self.server:
            return super().option_chain(symbol, expiry, spot)
        return self._call("/v1/options", dict(symbol=symbol, expiry=expiry, spot=spot))

    def option_history(self, symbol, expiry, strike, side):
        if not self.server:
            return super().option_history(symbol, expiry, strike, side)
        return self._call("/v1/option-history", dict(symbol=symbol, expiry=expiry, strike=strike, side=side))


DHAN_VERIFIED_SYMBOLS = frozenset(["NIFTY","RELIANCE","HDFCBANK","ICICIBANK","TCS","INFY","BHARTIARTL","SBIN","ITC","LT","AXISBANK","KOTAKBANK","HINDUNILVR","BAJFINANCE","BAJAJFINSV","MARUTI","M&M","TITAN","SUNPHARMA","ULTRACEMCO","ASIANPAINT","NTPC","POWERGRID","TMPV","TMCV","TATASTEEL","JSWSTEEL","HCLTECH","WIPRO","TECHM","NESTLEIND","HINDALCO","ONGC","COALINDIA","ADANIENT","ADANIPORTS","BEL","TRENT","EICHERMOT","GRASIM","CIPLA","DRREDDY","APOLLOHOSP","DIVISLAB","SBILIFE","HDFCLIFE","BAJAJ-AUTO","HEROMOTOCO","BRITANNIA","INDUSINDBK","SHRIRAMFIN","BPCL"])


class ServerDhanReadOnly:
    """Ephemeral, HTTPS-only Dhan gateway session; never persists pairing keys.

    Only explicitly mapped instruments are supported by the backend.
    All other symbols fail closed rather than showing fabricated broker quotes.
    """
    def __init__(self):
        self._origin = ""
        self._pairing_key = ""
        self._historical_only = False
        self._cooldown_until = {}
        self._global_cooldown_until = 0.0
        # One Dhan HTTPS request at a time across quote polling, scanner,
        # chart and manual refresh tasks; prevents overlapping gateway calls.
        import threading
        self._request_lock = threading.Lock()

    @property
    def connected(self):
        return bool(self._origin and self._pairing_key)

    @property
    def historical_only(self):
        return self.connected and self._historical_only

    def disconnect(self):
        self._origin = ""
        self._pairing_key = ""
        self._historical_only = False
        self._cooldown_until = {}
        self._global_cooldown_until = 0.0

    def _call(self, path, payload=None):
        with self._request_lock:
            return self._call_serialized(path, payload)

    def _call_serialized(self, path, payload=None):
        if not self.connected:
            raise FeedError("Dhan server not connected; use Connect / Check in Settings")
        if path not in ("/dhan/status", "/dhan/ltp", "/dhan/ltp-batch", "/dhan/intraday", "/v2/snapshot"):
            raise FeedError("Unsupported Dhan read-only request")
        remaining = max(self._cooldown_until.get(path, 0.0), self._global_cooldown_until) - time.monotonic()
        if remaining > 0:
            raise FeedError(f"{path} cooldown: retry in {int(remaining) + 1}s (HTTP 429)")
        headers = {"X-BotKing-Key": self._pairing_key, "Accept": "application/json"}
        if payload is None:
            req = urllib.request.Request(self._origin + path, headers=headers, method="GET")
        else:
            headers["Content-Type"] = "application/json"
            req = urllib.request.Request(
                self._origin + path, data=json.dumps(payload, allow_nan=False).encode("utf-8"),
                headers=headers, method="POST")
        try:
            with direct_https_opener().open(req, timeout=30 if path == "/dhan/ltp-batch" else 15) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise FeedError("Dhan server response too large")
                result = json.loads(raw)
        except urllib.error.HTTPError as exc:
            if exc.code == 403:
                self.disconnect()
                raise FeedError("Dhan server key rejected (HTTP 403); reconnect") from None
            if exc.code == 422:
                raise FeedError("Dhan instrument or timeframe not verified (HTTP 422)") from None
            if exc.code == 429:
                try:
                    wait = int(exc.headers.get("Retry-After", "30"))
                except (TypeError, ValueError, OverflowError):
                    wait = 30
                wait = max(1, min(wait, 120))
                self._cooldown_until[path] = time.monotonic() + wait
                # A Dhan 429 may reflect an account-wide quota, not just this route.
                # Pause all read-only data routes instead of letting the chart,
                # scanner and quote poller trigger successive rate-limit errors.
                self._global_cooldown_until = max(self._global_cooldown_until, time.monotonic() + wait)
                raise FeedError(f"{path} HTTP 429; retry after {wait}s") from None
            if exc.code in (502, 503, 504):
                # Read only the server's structured, allowlisted diagnostic.
                # Never expose arbitrary upstream error bodies or credentials.
                diagnostic = ""
                try:
                    body = json.loads(exc.read(4096))
                    if isinstance(body, dict):
                        detail = body.get("detail")
                        safe_details = {
                            "Dhan token expired or market data not entitled": "Dhan token expired or market-data permission missing",
                            "Dhan rejected batch quote request; check entitlement and instruments": "Dhan batch rejected; check entitlement and instrument mapping",
                            "Dhan batch response malformed or too large": "Dhan batch response invalid or too large",
                            "Dhan batch network request failed": "Dhan batch network request failed",
                            "Dhan credentials not configured": "Dhan server credentials not configured",
                            "Dhan returned no market data for verified NSE equities": "Dhan batch returned no NSE equity quotes",
                            "Invalid Dhan batch quote response": "Dhan batch response invalid",
                            "Dhan historical data unavailable or token expired": "Dhan historical endpoint unavailable or token expired",
                            "Invalid Dhan historical response": "Dhan historical candle response invalid",
                        }
                        diagnostic = safe_details.get(detail, "") if isinstance(detail, str) else ""
                except (ValueError, TypeError, UnicodeError, OSError):
                    pass
                if diagnostic:
                    raise FeedError(diagnostic + " (HTTP " + str(exc.code) + ")") from None
                raise FeedError("Dhan upstream unavailable or token expired (HTTP " + str(exc.code) + ")") from None
            raise FeedError("Dhan server HTTP " + str(exc.code)) from None
        except FeedError:
            raise
        except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError):
            raise FeedError("Dhan HTTPS connection or response failed") from None
        if not isinstance(result, dict) or result.get("live_orders_enabled") is not False:
            raise FeedError("Unexpected Dhan read-only server response")
        return result

    def connect(self, endpoint, pairing_key):
        self.disconnect()
        origin = server_origin(endpoint)
        if not isinstance(pairing_key, str) or not pairing_key.strip():
            raise FeedError("Server Access Key required")
        self._origin, self._pairing_key = origin, pairing_key.strip()
        try:
            status = self._call("/dhan/status")
            if status.get("market_data_configured") is not True:
                raise FeedError("Dhan market-data token unavailable on server")
            if status.get("reauthentication_required") is True:
                raise FeedError("Dhan authentication expired; reconnect through Dhan")
            quote = self.quote("NIFTY")
        except Exception:
            self.disconnect()
            raise
        return quote

    def activate_verified(self, endpoint, pairing_key, quote):
        """Activate only after Settings has verified status and LTP over HTTPS.

        Avoids a second NIFTY LTP request that can fail after a valid first one.
        Credentials remain in memory and are never persisted.
        """
        import math
        origin = server_origin(endpoint)
        price = quote.get("ltp") if isinstance(quote, dict) else None
        if (not isinstance(pairing_key, str) or not pairing_key.strip()
                or not isinstance(quote, dict) or quote.get("source") != "dhan"
                or quote.get("symbol") != "NIFTY"
                or quote.get("live_orders_enabled") is not False
                or isinstance(price, bool) or not isinstance(price, (int, float))
                or not math.isfinite(price) or price <= 0):
            raise FeedError("Cannot activate unverified Dhan read-only quote")
        self.disconnect()
        self._origin, self._pairing_key = origin, pairing_key.strip()

    def activate_historical_verified(self, endpoint, pairing_key, candles):
        """Allow historical-only read access after an actual Dhan candle response.

        This is NOT a live-quote verification and must never enable orders.
        """
        import math
        origin = server_origin(endpoint)
        if (not isinstance(pairing_key, str) or not pairing_key.strip()
                or not isinstance(candles, dict)
                or candles.get("source") != "dhan"
                or candles.get("symbol") != "RELIANCE"
                or candles.get("live_orders_enabled") is not False
                or candles.get("freshness") != "historical_unverified"):
            raise FeedError("Cannot activate unverified Dhan historical feed")
        bars = candles.get("bars")
        if (not isinstance(bars, list) or not bars
                or not all(isinstance(row, list) and len(row) == 6
                           and all(isinstance(v, (int, float)) and not isinstance(v, bool)
                                   and math.isfinite(v) for v in row)
                           and row[0] > 0 and min(row[1:5]) > 0 and row[5] >= 0
                           for row in bars)
                or any(row[2] < max(row[1], row[4], row[3])
                       or row[3] > min(row[1], row[4], row[2])
                       for row in bars)
                or any(bars[i][0] >= bars[i + 1][0] for i in range(len(bars) - 1))):
            raise FeedError("Cannot activate empty or invalid Dhan candles")
        self.disconnect()
        self._origin, self._pairing_key = origin, pairing_key.strip()
        self._historical_only = True

    def quote(self, symbol):
        if symbol not in DHAN_VERIFIED_SYMBOLS:
            raise FeedError("Dhan instrument mapping not verified for " + str(symbol)[:32])
        result = self._call("/dhan/ltp", {"symbol": symbol})
        price = result.get("ltp")
        import math
        if (result.get("source") != "dhan" or result.get("symbol") != symbol
                or isinstance(price, bool) or not isinstance(price, (int, float))
                or not math.isfinite(price) or price <= 0):
            raise FeedError("Invalid Dhan quote; cannot use for signals")
        # The provider endpoint has no exchange timestamp: do not mark this live.
        return {"symbol": symbol, "price": price, "source": "Dhan",
                "quote_timestamp": None, "freshness": "unverified"}

    def cooldown_remaining(self, path):
        """Seconds left before a rate-limited read-only endpoint may be retried."""
        if path not in ("/v2/snapshot", "/dhan/ltp-batch", "/dhan/intraday"):
            return 0
        return max(0, int(max(self._cooldown_until.get(path, 0.0),
                              self._global_cooldown_until) - time.monotonic() + 0.999))

    def batch_quotes(self):
        """Read the Oracle-owned 51-equity snapshot without a new Dhan API call.

        A recently collected server snapshot is not exchange-timestamp verified.
        Fail closed on missing, overdue, partial or invalid snapshots.
        """
        import math
        result = self._call("/v2/snapshot")
        raw = result.get("quotes")
        unavailable = result.get("unavailable")
        age = result.get("age_seconds")
        if (result.get("protocol") != 2 or result.get("source") != "dhan"
                or result.get("live_orders_enabled") is not False
                or result.get("error") is not None
                or result.get("collection_status") != "recently_collected"
                or isinstance(age, bool) or not isinstance(age, (int, float))
                or not math.isfinite(age) or age < 0 or age > 120
                or not isinstance(raw, dict) or not isinstance(unavailable, list)
                or result.get("freshness") != "unverified"
                or any(not isinstance(symbol, str) or symbol not in DHAN_VERIFIED_SYMBOLS
                       or symbol == "NIFTY" for symbol in unavailable)
                or len(unavailable) != len(set(unavailable))
                or set(raw).intersection(unavailable)):
            raise FeedError("Oracle Dhan snapshot missing, stale or invalid")
        if not raw:
            raise FeedError("Oracle Dhan snapshot contains no quotes")
        # Partial quotes are usable, but must not imply complete coverage.
        # Missing symbols remain absent from returned quotes, never synthesized.
        quotes = {}
        for symbol, price in raw.items():
            if (symbol not in DHAN_VERIFIED_SYMBOLS or symbol == "NIFTY"
                    or isinstance(price, bool) or not isinstance(price, (int, float))
                    or not math.isfinite(price) or price <= 0):
                raise FeedError("Invalid Oracle Dhan snapshot quote")
            quotes[symbol] = {"symbol": symbol, "price": price, "source": "Dhan",
                              "quote_timestamp": None, "freshness": "unverified"}
        return quotes

    def intraday(self, symbol, interval, from_date, to_date):
        if symbol not in DHAN_VERIFIED_SYMBOLS or interval not in (1, 5, 15, 25, 60):
            raise FeedError("Dhan candle instrument or interval not verified")
        result = self._call("/dhan/intraday", {
            "symbol": symbol, "interval": interval,
            "from_date": str(from_date), "to_date": str(to_date)})
        if (result.get("source") != "dhan" or result.get("symbol") != symbol
                or not isinstance(result.get("bars"), list)):
            raise FeedError("Invalid Dhan candle response")
        return result
