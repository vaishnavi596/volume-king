"""Read-only BOT KING 226 Oracle cache transport.

Transitional transport: the legacy pairing header is supported only until
device enrollment and Keystore-backed sessions replace it. Never log secrets.
"""
import json
import math
import re
import urllib.error
import urllib.parse
import urllib.request

from server_feed import NoRedirect, server_origin


class OracleCacheError(RuntimeError):
    pass


class Oracle226Client:
    def __init__(self, origin, access_key, *, auth_mode="legacy_pairing"):
        self.origin = server_origin(origin)
        if not isinstance(access_key, str) or not access_key:
            raise OracleCacheError("Oracle device session is not configured")
        if auth_mode not in ("legacy_pairing", "device_session"):
            raise OracleCacheError("Unsupported Oracle authentication mode")
        if auth_mode == "device_session" and re.fullmatch(r"[A-Za-z0-9_-]{32,256}", access_key) is None:
            raise OracleCacheError("Invalid Oracle device session token")
        self._access_key = access_key
        self._auth_mode = auth_mode
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )

    def _read(self, path):
        req = urllib.request.Request(
            self.origin + path,
            headers={"Accept": "application/json", **(
                {"Authorization": "Bearer " + self._access_key}
                if self._auth_mode == "device_session"
                else {"X-BotKing-Key": self._access_key})},
            method="GET",
        )
        try:
            with self._opener.open(req, timeout=15) as response:
                if response.status != 200:
                    raise OracleCacheError("Oracle cache unavailable")
                payload = response.read(2_000_001)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise OracleCacheError("Oracle cache request failed") from exc
        if len(payload) > 2_000_000:
            raise OracleCacheError("Oracle cache response too large")
        try:
            data = json.loads(payload)
        except (ValueError, UnicodeDecodeError) as exc:
            raise OracleCacheError("Invalid Oracle cache response") from exc
        if not isinstance(data, dict) or data.get("live_orders_enabled") is not False:
            raise OracleCacheError("Unexpected Oracle cache protocol")
        return data

    def snapshot(self):
        data = self._read("/v2/snapshot")
        if data.get("protocol") != 2 or not isinstance(data.get("quotes"), dict):
            raise OracleCacheError("Unexpected snapshot schema")
        # Collection recency does not prove exchange timestamp freshness.
        if data.get("freshness") not in ("unverified", "stale_or_missing"):
            raise OracleCacheError("Unknown snapshot freshness")
        return data

    def candles(self, symbol, interval=5):
        if not isinstance(symbol, str) or not symbol or not all(
            ch.isascii() and (ch.isupper() or ch.isdigit() or ch in "&_-")
            for ch in symbol
        ):
            raise OracleCacheError("Invalid symbol")
        if type(interval) is not int or interval not in (1, 5, 15, 25, 60):
            raise OracleCacheError("Unsupported candle interval")
        data = self._read(
            "/v2/candles/" + urllib.parse.quote(symbol, safe="") + "/" + str(interval)
        )
        if data.get("symbol") != symbol or not isinstance(data.get("bars"), list):
            raise OracleCacheError("Unexpected candle schema")
        if data.get("freshness") not in ("historical_unverified", "stale_or_missing"):
            raise OracleCacheError("Unknown candle freshness")
        for bar in data["bars"]:
            if not isinstance(bar, list) or len(bar) < 6 or any(
                type(value) not in (int, float) or not math.isfinite(value)
                for value in bar[:6]
            ):
                raise OracleCacheError("Invalid cached candle")
        return data
