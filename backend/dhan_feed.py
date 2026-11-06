"""DhanHQ read-only adapter. Never submits trading orders or logs credentials.

This module is intentionally independent of the existing Angel One gateway.
Only use it on a trusted server with credentials supplied through a secure channel.
Market-data entitlement is checked by the provider; errors do not fall back to
fabricated quotes. A provider token's expiry cannot be extended by this client.
"""
import json
import urllib.error
import urllib.request


class DhanFeedError(RuntimeError):
    pass


class DhanFeed:
    ROOT = "https://api.dhan.co/v2"

    def __init__(self, client_id, access_token, opener=None):
        self.client_id = str(client_id or "").strip()
        self._token = str(access_token or "").strip()
        self._opener = opener or urllib.request.urlopen
        if not self.client_id or not self._token:
            raise DhanFeedError("Dhan credentials are not configured")

    def _post(self, endpoint, payload):
        if endpoint not in ("/marketfeed/ltp", "/charts/intraday", "/charts/historical"):
            raise DhanFeedError("Unsupported read-only endpoint")
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        request = urllib.request.Request(
            self.ROOT + endpoint,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "client-id": self.client_id,
                "access-token": self._token,
            },
            method="POST",
        )
        try:
            with self._opener(request, timeout=12) as response:
                raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                raise DhanFeedError("Dhan response exceeds size limit")
            result = json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code in (401, 403):
                raise DhanFeedError("Dhan token expired or data access not entitled") from None
            if exc.code == 429:
                raise DhanFeedError("Dhan rate limit reached") from None
            raise DhanFeedError("Dhan market data unavailable") from None
        except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError):
            raise DhanFeedError("Dhan market data request failed") from None
        if not isinstance(result, dict):
            raise DhanFeedError("Invalid Dhan response")
        if result.get("errorCode") or result.get("errorType"):
            raise DhanFeedError("Dhan rejected market data request; check entitlement and instrument")
        return result

    def ltp(self, exchange_segment, security_id):
        if not isinstance(exchange_segment, str) or not exchange_segment.strip():
            raise DhanFeedError("Exchange segment required")
        try:
            sid = int(security_id)
        except (ValueError, TypeError):
            raise DhanFeedError("Valid Dhan security ID required") from None
        if sid <= 0:
            raise DhanFeedError("Valid Dhan security ID required")
        return self._post("/marketfeed/ltp", {exchange_segment: [sid]})

    def intraday(self, payload):
        if not isinstance(payload, dict) or not payload.get("securityId"):
            raise DhanFeedError("Dhan instrument mapping required")
        return self._post("/charts/intraday", payload)

    def historical(self, payload):
        if not isinstance(payload, dict) or not payload.get("securityId"):
            raise DhanFeedError("Dhan instrument mapping required")
        return self._post("/charts/historical", payload)
