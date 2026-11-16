"""Read-only request coalescing for BOT KING logical refresh lanes.

Independent, in-process scheduler primitive. Does NOT make HTTP requests.
Dhan/Oracle source-side quotas, broker credentials, user auth and expiry
remain the responsibility of the caller. Do not treat a cached result as LIVE.
"""
from concurrent.futures import Future
from copy import deepcopy
from threading import Lock
import time

VALID_LANES = frozenset(("quotes", "candles", "derivatives", "context"))


class LaneCoordinator:
    """Single-flight same-source requests, bounded recent-result reuse.

    Distinct keys in the same lane are NOT combined into an upstream Dhan
    market request. Backend provider rate limits must be enforced separately.

    The caller controls TTL and must never pass a longer TTL than data
    freshness permits. A result is cached only when fetch succeeds.
    """

    def __init__(self, *, clock=None, max_cached=128):
        if type(max_cached) is not int or not 1 <= max_cached <= 10000:
            raise ValueError("Invalid cache budget")
        self._clock = clock or time.monotonic
        self._max_cached = max_cached
        self._lock = Lock()
        self._active = {}
        self._cache = {}

    def run(self, lane, key, fetch, *, ttl_seconds=0):
        if lane not in VALID_LANES:
            raise ValueError("Unsupported refresh lane")
        if not isinstance(key, str) or not key or len(key) > 256:
            raise ValueError("Invalid source cache key")
        if not callable(fetch):
            raise TypeError("fetch must be callable")
        if type(ttl_seconds) not in (int, float) or not 0 <= ttl_seconds <= 900:
            raise ValueError("Unsafe cache TTL")
        slot = (lane, key)
        with self._lock:
            old = self._cache.get(slot)
            now = self._clock()
            if old is not None and now >= old[0] and now - old[0] < ttl_seconds:
                return deepcopy(old[1])
            flight = self._active.get(slot)
            if flight is None:
                flight = Future()
                self._active[slot] = flight
                owner = True
            else:
                owner = False
        if not owner:
            # Wait for the only same-key in-progress owner. Never refetch
            # on failure; let caller apply provider cooldown before retry.
            return deepcopy(flight.result())
        try:
            value = fetch()
            stable = deepcopy(value)
            with self._lock:
                if ttl_seconds > 0:
                    if len(self._cache) >= self._max_cached:
                        # Evict the oldest timestamp without touching active flights.
                        oldest = min(self._cache, key=lambda k: self._cache[k][0])
                        del self._cache[oldest]
                    self._cache[slot] = (self._clock(), stable)
                # Publish while lock protects cache+active state consistently.
                flight.set_result(deepcopy(stable))
                del self._active[slot]
            return deepcopy(stable)
        except BaseException as exc:
            with self._lock:
                flight.set_exception(exc)
                del self._active[slot]
            raise

    def invalidate(self, lane, key):
        if lane not in VALID_LANES or not isinstance(key, str):
            raise ValueError("Unsupported refresh source")
        with self._lock:
            self._cache.pop((lane, key), None)

    def cache_size(self):
        with self._lock:
            return len(self._cache)
