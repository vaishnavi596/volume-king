"""Bounded, in-process, read-only handoff of validated option metrics.

The handoff never fetches market data and never upgrades evidence to live votes.
"""
from copy import deepcopy
from threading import RLock
from time import monotonic


class OptionEvidenceCache:
    def __init__(self, ttl_seconds=120, max_entries=128, clock=monotonic):
        if not (0 < ttl_seconds <= 600 and 0 < max_entries <= 1024):
            raise ValueError("Invalid bounded evidence cache settings")
        self._ttl = ttl_seconds
        self._limit = max_entries
        self._clock = clock
        self._lock = RLock()
        self._items = {}

    def put(self, symbol, expiry, metrics):
        if not isinstance(symbol, str) or not symbol or not isinstance(expiry, str):
            return False
        if not isinstance(metrics, dict) or metrics.get("signal_eligible") is not False:
            return False
        if metrics.get("freshness") != "unverified":
            return False
        now = self._clock()
        with self._lock:
            self._prune(now)
            key = (symbol, expiry)
            if len(self._items) >= self._limit and key not in self._items:
                oldest = min(self._items, key=lambda k: self._items[k][0])
                del self._items[oldest]
            self._items[key] = (now, deepcopy(metrics))
        return True

    def latest(self, symbol):
        now = self._clock()
        with self._lock:
            self._prune(now)
            candidates = [(ts, expiry, data) for (sym, expiry), (ts, data)
                          in self._items.items() if sym == symbol]
            if not candidates:
                return None
            _, _, data = max(candidates, key=lambda item: (item[0], item[1]))
            return deepcopy(data)

    def _prune(self, now):
        for key, (created, _) in list(self._items.items()):
            if now - created >= self._ttl or now < created:
                del self._items[key]
