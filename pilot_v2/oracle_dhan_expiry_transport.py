"""Private, opt-in Oracle Dhan listed-expiry reader for V2 evidence.

A single operator-selected underlying per demand. Uses the existing protected
V1 read-only /dhan/option-expiries route at fixed loopback, never a device URL.
No live option-chain signals are synthesized. The operator must independently
confirm the endpoint/entitlement and mount this as evidence_transport; the
normal V2 app deliberately does not auto-install it.
"""
import json
import math
import time
from datetime import date
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, HTTPRedirectHandler, ProxyHandler

from .internal_dhan_read_port import INDEXES, DhanRateLimited, DhanReadUnavailable
from .oracle_evidence_lane import DhanEvidenceBatch

_LOOPBACK = "http://127.0.0.1:8000/dhan/option-expiries"
_MAX_RESPONSE = 8192


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, url):
        return None


class OracleDhanExpiryTransport:
    """Operator-owned one-request expiry collector, no broker SDK fallback."""

    def __init__(self, *, pairing_key, symbol, opener=None, clock=None):
        if (type(pairing_key) is not str or len(pairing_key) < 32
                or type(symbol) is not str or not 1 <= len(symbol) <= 32
                or not all(c.isupper() or c.isdigit() or c in "&_-" for c in symbol)):
            raise ValueError("Private Dhan expiry identity required")
        self._pairing_key = pairing_key
        self._symbol = symbol
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect())
        self._clock = clock or time.time
        self._revision = 0
        self._lock = Lock()

    def __call__(self):
        # Only one upstream request per reserved shared read budget token.
        request = Request(_LOOPBACK,
                          data=json.dumps({"symbol": self._symbol}).encode("ascii"),
                          method="POST",
                          headers={"X-BotKing-Key": self._pairing_key,
                                   "Accept": "application/json",
                                   "Content-Type": "application/json"})
        try:
            with self._opener.open(request, timeout=10) as response:
                if response.status != 200 or response.geturl() != _LOOPBACK:
                    raise DhanReadUnavailable("Oracle Dhan expiry route unavailable")
                raw = response.read(_MAX_RESPONSE + 1)
                if len(raw) > _MAX_RESPONSE:
                    raise DhanReadUnavailable("Oracle expiry response too large")
        except HTTPError as exc:
            if exc.code == 429:
                raise DhanRateLimited("Dhan expiry shared cooldown") from None
            raise DhanReadUnavailable("Dhan listed expiries denied/unavailable") from None
        except (URLError, TimeoutError, OSError):
            raise DhanReadUnavailable("Dhan listed expiries unavailable") from None
        try:
            parsed = json.loads(raw)
            if (type(parsed) is not dict
                    or parsed.get("source") != "dhan"
                    or parsed.get("live_orders_enabled") is not False
                    or parsed.get("symbol") != self._symbol):
                raise ValueError("Unverified Dhan expiry source")
            supplied = parsed.get("expiries")
            if (type(supplied) is not list or not 1 <= len(supplied) <= 64
                    or any(type(d) is not str or len(d) != 10
                           or date.fromisoformat(d).isoformat() != d for d in supplied)
                    or len(set(supplied)) != len(supplied)):
                raise ValueError("Invalid Dhan expiry roster")
            expiries = sorted(supplied)
            observed = self._clock()
            if type(observed) not in (int, float) or not math.isfinite(observed) or observed <= 0:
                raise ValueError("Invalid expiry response clock")
        except (ValueError, TypeError, KeyError, OverflowError):
            raise DhanReadUnavailable("Invalid/incomplete Dhan expiry response") from None
        with self._lock:
            self._revision += 1
            revision = self._revision
        return DhanEvidenceBatch("dhan", revision, observed, [{
            "kind": "expiries", "symbol": self._symbol,
            "revision": revision, "available": expiries}])
