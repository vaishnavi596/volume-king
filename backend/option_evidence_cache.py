"""Bounded, in-process, read-only handoff of validated option metrics.

The handoff never fetches market data and never upgrades evidence to live votes.
"""
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from threading import RLock
from time import monotonic


class OptionEvidenceCache:
    def __init__(self, ttl_seconds=120, max_entries=128, clock=monotonic, today=None):
        if not (0 < ttl_seconds <= 600 and 0 < max_entries <= 1024):
            raise ValueError("Invalid bounded evidence cache settings")
        self._ttl = ttl_seconds
        self._limit = max_entries
        self._clock = clock
        self._today = today or (lambda: datetime.now(timezone(timedelta(hours=5, minutes=30))).date())
        self._lock = RLock()
        self._items = {}

    def put(self, symbol, expiry, metrics):
        if not isinstance(symbol, str) or not symbol or not isinstance(expiry, str):
            return False
        try:
            if date.fromisoformat(expiry).isoformat() != expiry or date.fromisoformat(expiry) < self._today():
                return False
        except ValueError:
            return False
        if not isinstance(metrics, dict) or metrics.get("signal_eligible") is not False:
            return False
        if metrics.get("freshness") != "unverified":
            return False
        # Legacy internal Dhan metrics may omit source; explicit foreign or
        # spoofed providers must never enter the Dhan-only assessment cache.
        if metrics.get("source", "dhan") != "dhan":
            return False
        now = self._clock()
        with self._lock:
            self._prune(now)
            key = (symbol, expiry)
            if len(self._items) >= self._limit and key not in self._items:
                oldest = min(self._items, key=lambda k: self._items[k][0])
                del self._items[oldest]
            payload = deepcopy(metrics)
            payload["expiry"] = expiry
            self._items[key] = (now, payload)
        return True

    def latest(self, symbol, selected_expiry=None):
        """Return exact requested expiry when provided; legacy latest otherwise."""
        if selected_expiry is not None:
            if not isinstance(selected_expiry, str):
                return None
            try:
                if date.fromisoformat(selected_expiry).isoformat() != selected_expiry:
                    return None
            except ValueError:
                return None
        now = self._clock()
        with self._lock:
            self._prune(now)
            candidates = [(ts, expiry, data) for (sym, expiry), (ts, data)
                          in self._items.items() if sym == symbol and
                          date.fromisoformat(expiry) >= self._today()
                          and (selected_expiry is None or expiry == selected_expiry)]
            if not candidates:
                return None
            _, _, data = max(candidates, key=lambda item: (item[0], item[1]))
            return deepcopy(data)

    def _prune(self, now):
        for key, (created, _) in list(self._items.items()):
            if now - created >= self._ttl or now < created or date.fromisoformat(key[1]) < self._today():
                del self._items[key]
