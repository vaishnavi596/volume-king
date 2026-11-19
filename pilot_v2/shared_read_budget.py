"""Single shared V2 read quota; app priorities never override provider cooldown.

A fail-closed, monotonic, worker-local gate. Only a real server deployment
with one coordinated worker/shared quota can treat this as provider budgeting.
No Dhan SDK, HTTP calls, orders, or implicit retry loops.
"""
from __future__ import annotations
from math import isfinite
from threading import RLock


class BudgetDenied(RuntimeError):
    pass


class SharedReadBudget:
    def __init__(self, *, monotonic, min_gap_seconds=1.0, cooldown_seconds=30.0):
        if (not callable(monotonic) or type(min_gap_seconds) not in (int, float)
                or not 0 < min_gap_seconds <= 60
                or type(cooldown_seconds) not in (int, float)
                or not 1 <= cooldown_seconds <= 300):
            raise ValueError("Invalid shared read budget")
        self._mono = monotonic
        self._gap = min_gap_seconds
        self._cooldown = cooldown_seconds
        self._next = 0.0
        self._cooldown_until = 0.0
        self._lock = RLock()

    def _now(self):
        value = self._mono()
        if type(value) not in (float, int) or not isfinite(value) or value < 0:
            raise BudgetDenied("Invalid rate budget clock")
        return float(value)

    def reserve(self):
        """Reserve a single provider read; NEVER wait or queue indefinitely."""
        with self._lock:
            now = self._now()
            if now < self._cooldown_until:
                raise BudgetDenied("Provider cooldown")
            if now < self._next:
                raise BudgetDenied("Shared provider spacing")
            self._next = now + self._gap

    def throttle(self):
        """Provider 429: enter shared cooldown; later priority never bypasses."""
        with self._lock:
            now = self._now()
            self._cooldown_until = max(self._cooldown_until, now + self._cooldown)

    def status(self):
        with self._lock:
            now = self._now()
            return {
                "cooldown_seconds": max(0.0, self._cooldown_until - now),
                "next_read_seconds": max(0.0, self._next - now),
            }
