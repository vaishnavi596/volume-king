"""DhanHQ read-only adapter. Never submits trading orders or logs credentials.

This module is intentionally independent of the existing Angel One gateway.
Only use it on a trusted server with credentials supplied through a secure channel.
Market-data entitlement is checked by the provider; errors do not fall back to
fabricated quotes. A provider token's expiry cannot be extended by this client.
"""
import json
import threading
import time
import urllib.error
import urllib.request


class DhanFeedError(RuntimeError):
    pass


class DhanRateLimitError(DhanFeedError):
    """Provider throttled requests; callers must not retry immediately."""


class DhanFeed:
    _rate_lock = threading.Lock()
    _retry_after = 0.0
    RATE_LIMIT_COOLDOWN_SECONDS = 30
    ROOT = "https://api.dhan.co/v2"

    def __init__(self, client_id, access_token, opener=None):
        self.client_id = str(client_id or "").strip()
        self._token = str(access_token or "").strip()
        self._opener = opener or urllib.request.urlopen
        if not self.client_id or not self._token:
            raise DhanFeedError("Dhan credentials are not configured")

    def _post(self, endpoint, payload):
        if endpoint not in ("/marketfeed/ltp", "/charts/intraday", "/charts/historical", "/optionchain"):
            raise DhanFeedError("Unsupported read-only endpoint")
        with self._rate_lock:
            if time.monotonic() < self._retry_after:
                raise DhanRateLimitError("Dhan rate limit cooldown active")
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
                with self._rate_lock:
                    DhanFeed._retry_after = max(DhanFeed._retry_after, time.monotonic() + self.RATE_LIMIT_COOLDOWN_SECONDS)
                raise DhanRateLimitError("Dhan rate limit reached") from None
            raise DhanFeedError("Dhan market data unavailable") from None
        except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError):
            raise DhanFeedError("Dhan market data request failed") from None
        if not isinstance(result, dict):
            raise DhanFeedError("Invalid Dhan response")
        if result.get("errorCode") or result.get("errorType"):
            raise DhanFeedError("Dhan rejected market data request; check entitlement and instrument")
        return result

    def batch_ltp(self, instruments):
        """Fetch multiple instruments in one read-only request.

        Accepts an iterable of (exchange_segment, security_id) pairs.
        Callers must inspect the returned provider data for missing quotes and
        timestamps; a successful HTTP response is not proof of live pricing.
        """
        allowed = {"IDX_I", "NSE_EQ", "NSE_FNO", "BSE_EQ", "BSE_FNO", "BSE_I", "MCX_COMM"}
        if isinstance(instruments, (str, bytes, dict)):
            raise DhanFeedError("Instrument pairs required")
        payload = {}
        total = 0
        try:
            iterator = iter(instruments)
        except TypeError:
            raise DhanFeedError("Instrument pairs required") from None
        for instrument in iterator:
            if not isinstance(instrument, (tuple, list)) or len(instrument) != 2:
                raise DhanFeedError("Instrument pair required")
            segment, security_id = instrument
            if segment not in allowed:
                raise DhanFeedError("Exchange segment required")
            if isinstance(security_id, bool) or not (
                isinstance(security_id, int) or
                (isinstance(security_id, str) and security_id.isascii() and security_id.isdecimal())
            ):
                raise DhanFeedError("Valid Dhan security ID required")
            sid = int(security_id)
            if sid <= 0:
                raise DhanFeedError("Valid Dhan security ID required")
            ids = payload.setdefault(segment, [])
            if sid not in ids:
                ids.append(sid)
                total += 1
            if total > 1000:
                raise DhanFeedError("Too many instruments in one LTP request")
        if not total:
            raise DhanFeedError("At least one instrument required")
        return self._post("/marketfeed/ltp", payload)

    def ltp(self, exchange_segment, security_id):
        return self.batch_ltp([(exchange_segment, security_id)])

    def intraday(self, payload):
        if not isinstance(payload, dict) or not payload.get("securityId"):
            raise DhanFeedError("Dhan instrument mapping required")
        return self._post("/charts/intraday", payload)

    def historical(self, payload):
        if not isinstance(payload, dict) or not payload.get("securityId"):
            raise DhanFeedError("Dhan instrument mapping required")
        return self._post("/charts/historical", payload)

    def option_chain(self, underlying_segment, underlying_security_id, expiry):
        """Read-only Dhan option-chain request; no broker fallback or order routing.

        Caller must verify the underlying against the instrument master and
        validate the returned chain before computing OI, PCR or max pain.
        """
        from datetime import date
        if underlying_segment not in ("IDX_I", "NSE_EQ", "BSE_I", "BSE_EQ"):
            raise DhanFeedError("Verified underlying segment required")
        if isinstance(underlying_security_id, bool) or not (
            isinstance(underlying_security_id, int) or
            (isinstance(underlying_security_id, str) and underlying_security_id.isascii()
             and underlying_security_id.isdecimal())
        ) or int(underlying_security_id) <= 0:
            raise DhanFeedError("Verified underlying security ID required")
        try:
            expiry_date = date.fromisoformat(expiry)
        except (TypeError, ValueError):
            raise DhanFeedError("Valid ISO expiry date required") from None
        if expiry_date < date.today():
            raise DhanFeedError("Expired option chain requested")
        return self._post("/optionchain", {
            "UnderlyingScrip": int(underlying_security_id),
            "UnderlyingSeg": underlying_segment,
            "Expiry": expiry_date.isoformat(),
        })
