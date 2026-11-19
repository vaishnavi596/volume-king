"""Oracle-only bridge: reuse authenticated V1 Dhan read endpoints, never broker orders.

This component does not provision device login, start ASGI, or mark data live.
Inject the server-side pairing key at runtime, never from an Android request.
"""
from __future__ import annotations

import json
import math
import time
from threading import Lock
from urllib.error import HTTPError, URLError
from urllib.request import Request, build_opener, ProxyHandler, HTTPRedirectHandler

from .internal_dhan_read_port import DhanReadBatch, DhanReadUnavailable, DhanRateLimited, INDEXES

MAX_RESPONSE = 65536
ORIGIN = "http://127.0.0.1:8000"
PATHS = {"indices": "/dhan/index-ltp-batch", "quotes": "/dhan/selected-ltp-batch"}


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, msg, headers, url):
        return None


class OracleDhanReadTransport:
    """Strict internal-only read transport; no phone/user-controlled URL or key."""

    def __init__(self, *, pairing_key, opener=None, clock=None):
        if not isinstance(pairing_key, str) or len(pairing_key) < 32:
            raise ValueError("Privately provisioned server key required")
        self._key = pairing_key
        self._clock = clock or time.time
        self._opener = opener or build_opener(ProxyHandler({}), _NoRedirect())
        self._revision = 0
        self._revision_lock = Lock()

    def __call__(self, feed, selected):
        if feed not in PATHS or type(selected) is not tuple:
            raise DhanReadUnavailable("Unsupported feed request")
        if feed == "indices":
            if selected != INDEXES:
                raise DhanReadUnavailable("Index roster mismatch")
            body = b""
        else:
            if not 1 <= len(selected) <= 70 or len(set(selected)) != len(selected):
                raise DhanReadUnavailable("Invalid equity roster")
            if any(type(s) is not str or not s or len(s) > 32 or
                   not all(c.isupper() or c.isdigit() or c in "&_-" for c in s)
                   for s in selected):
                raise DhanReadUnavailable("Invalid equity symbols")
            body = json.dumps({"symbols": list(selected)}, separators=(",", ":")).encode()
        url = ORIGIN + PATHS[feed]
        req = Request(url, data=body, method="POST",
                      headers={"X-BotKing-Key": self._key,
                               "Content-Type": "application/json",
                               "Accept": "application/json"})
        try:
            with self._opener.open(req, timeout=15) as resp:
                if resp.status != 200 or resp.geturl() != url:
                    raise DhanReadUnavailable("Unexpected Oracle response")
                raw = resp.read(MAX_RESPONSE + 1)
                if len(raw) > MAX_RESPONSE:
                    raise DhanReadUnavailable("Oversized Oracle response")
        except HTTPError as exc:
            if exc.code == 429:
                raise DhanRateLimited("Oracle Dhan read cooldown") from None
            raise DhanReadUnavailable("Oracle Dhan read denied/unavailable") from None
        except (URLError, TimeoutError, OSError):
            raise DhanReadUnavailable("Oracle Dhan read unavailable") from None
        try:
            response = json.loads(raw)
            if not isinstance(response, dict) or response.get("source") != "dhan" or response.get("live_orders_enabled") is not False:
                raise ValueError("Untrusted Dhan response")
            quotes = response["quotes"]
            unavailable = response.get("unavailable", [])
            if not isinstance(quotes, dict) or not isinstance(unavailable, list) or unavailable or set(quotes) != set(selected):
                raise ValueError("Incomplete quote batch")
            observed_at = float(self._clock())
            if not math.isfinite(observed_at) or observed_at <= 0:
                raise ValueError("Bad observation clock")
            rows = {}
            for symbol in selected:
                value = quotes[symbol]
                price = value.get("ltp") if feed == "indices" and isinstance(value, dict) else value
                if type(price) not in (int, float) or not math.isfinite(price) or price <= 0:
                    raise ValueError("Bad quote")
                rows[symbol] = {"price": price, "observed_at": observed_at}
            with self._revision_lock:
                self._revision += 1
                revision = self._revision
            return DhanReadBatch("dhan", selected, rows, revision, observed_at)
        except (TypeError, ValueError, KeyError, OverflowError):
            raise DhanReadUnavailable("Invalid/incomplete Oracle Dhan response") from None
