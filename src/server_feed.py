"""Owner HTTPS transport for market data and separately confirmed live orders."""
import json
import urllib.error
import urllib.parse
import urllib.request

from market_feed import AngelFeed, FeedError, SessionExpired


class LiveOperationError(FeedError):
    """Public, bounded error from the trusted owner's live-order gateway."""
    pass


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
            with urllib.request.build_opener(NoRedirect()).open(req, timeout=45) as response:
                raw = response.read(4 * 1024 * 1024 + 1)
                if len(raw) > 4 * 1024 * 1024:
                    raise FeedError("Server response too large")
                return json.loads(raw)
        except urllib.error.HTTPError as exc:
            if exc.code == 401 and path != "/v1/login":
                self.disconnect()
                raise SessionExpired("Server session expired; reconnect") from None
            if exc.code == 429:
                raise FeedError("Server busy; wait before retrying") from None
            if path.startswith("/v1/live/"):
                try:
                    detail = json.loads(exc.read(4096)).get("detail", "Live operation could not be verified")
                    if not isinstance(detail, str) or len(detail) > 400:raise ValueError()
                except Exception:
                    detail = "Live operation could not be verified; refresh broker orders before sending another order"
                raise LiveOperationError(detail) from None
            raise FeedError("Server rejected request; check server access and broker login") from None
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

    def live(self, operation, payload=None):
        if operation not in ("capabilities", "arm", "disarm", "preview", "submit", "orders", "positions", "cancel"):
            raise FeedError("Unsupported live operation")
        if not self.server or not self.connected:
            raise FeedError("Connect Angel One through your BOT KING server for live trading")
        return self._call("/v1/live/" + operation, payload or {})
