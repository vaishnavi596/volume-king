"""Oracle-side shared read-only quote requests across multiple BOT KING devices.

One process-wide lane, short-lived valid-response cache, and shared 429 cooldown.
No broker tokens are retained in cache keys: callers supply an opaque token
fingerprint. Never caches failures or marks results live.
"""
import math
import threading
import time
from collections import OrderedDict


class SharedQuoteLane:
    def __init__(self, *, ttl_seconds=60, cooldown_seconds=30,
                 max_entries=24, clock=time.monotonic):
        self._ttl = ttl_seconds
        self._cooldown_seconds = cooldown_seconds
        self._max_entries = max_entries
        self._clock = clock
        self._lock = threading.RLock()
        self._entries = OrderedDict()
        self._cooldown_until = 0.0

    def run(self, key, fetch, validate, *, rate_limit_error):
        """Coalesce equal requests and serialize other upstream market calls.

        A second caller rechecks the cache *inside* the lock after the first
        completes. A 429 never makes a second Dhan call during cooldown.
        """
        with self._lock:
            now = self._clock()
            entry = self._entries.get(key)
            if entry is not None:
                when, value = entry
                if (type(when) in (int, float) and math.isfinite(when)
                        and 0 <= now - when < self._ttl):
                    self._entries.move_to_end(key)
                    return value
                self._entries.pop(key, None)
            if now < self._cooldown_until:
                raise rate_limit_error("Shared Dhan quote cooldown active")
            try:
                value = fetch()
            except rate_limit_error:
                self._cooldown_until = max(self._cooldown_until,
                                           self._clock() + self._cooldown_seconds)
                raise
            if not validate(value):
                # Fail closed: never share an invalid/provider-error payload.
                return value
            self._entries[key] = (self._clock(), value)
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)
            return value
