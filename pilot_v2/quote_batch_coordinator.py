"""One-process V2 read-only provider batch work planner, with no HTTP calls.

IMPORTANT: this is a synthetic scheduling contract. Production requires an
atomic *shared* coordinator and durable lease/cooldown across server workers.
All queued/provider calls must be executed by a separately approved collector.
"""
from dataclasses import dataclass
from math import isfinite
from threading import RLock

from .gateway_contract import Demand, ContractError

@dataclass(frozen=True)
class QuoteLease:
    lease_id: int
    symbols: tuple
    started_at: float

class QuoteBatchCoordinator:
    """Serialized, global-budget limited (quotes+indices) request plans.

    Planning one request is NOT making a broker request. The caller must call
    finish() even if its request failed. 429 must call cooldown_429().
    """

    def __init__(self, *, clock, minimum_spacing=1.0, per_symbol_interval=60.0,
                 max_symbols=73):
        if not callable(clock):
            raise ValueError("Clock must be provided")
        for v in (minimum_spacing, per_symbol_interval):
            if type(v) not in (int, float) or not isfinite(v):
                raise ValueError("Invalid spacing")
        if (minimum_spacing < 1 or per_symbol_interval < 30
                or type(max_symbols) is not int or not 1 <= max_symbols <= 73):
            raise ValueError("Unsafe quote batch configuration")
        self._clock = clock
        self._gap = minimum_spacing
        self._interval = per_symbol_interval
        self._max = max_symbols
        self._lock = RLock()
        self._next_id = 0
        self._pending = None
        self._cooldown_until = 0.0
        self._last_global = None
        self._last_attempts = {}

    def _now(self):
        now = self._clock()
        if type(now) not in (int, float) or not isfinite(now) or now < 0:
            raise ContractError("Invalid monotonic clock")
        return float(now)

    def next_batch(self, demand):
        """Return one lease or None; never fan out once per mobile."""
        if not isinstance(demand, Demand):
            raise ContractError("Invalid active symbol demand")
        if (len(demand.equities) > 70 or len(set(demand.equities)) != len(demand.equities)
                or len(set(demand.indices)) != len(demand.indices)):
            raise ContractError("Invalid unique symbol demand")
        active = tuple(sorted(set(demand.indices + demand.equities)))
        if len(active) > self._max:
            raise ContractError("Active market data request exceeds budget")
        with self._lock:
            now = self._now()
            if (self._pending is not None or now < self._cooldown_until
                    or (self._last_global is not None
                        and now - self._last_global < self._gap)):
                return None
            due = tuple(s for s in active if s not in self._last_attempts
                        or now - self._last_attempts[s] >= self._interval)
            if not due:
                return None
            self._next_id += 1
            lease = QuoteLease(self._next_id, due, now)
            self._pending = lease
            self._last_global = now
            # Attempt accounting happens before an external call; network
            # failure must not cause rapid retry/fanout across 3 phones.
            self._last_attempts.update({s: now for s in due})
            return lease

    def finish(self, lease):
        """Close only the matching lease, including on non-429 failure."""
        with self._lock:
            if not isinstance(lease, QuoteLease) or lease != self._pending:
                raise ContractError("Invalid or stale quote lease")
            self._pending = None

    def cooldown_429(self, lease, *, retry_after_seconds=30):
        if (type(retry_after_seconds) not in (int, float)
                or not isfinite(retry_after_seconds)
                or not 1 <= retry_after_seconds <= 3600):
            raise ContractError("Invalid provider retry-after")
        with self._lock:
            if not isinstance(lease, QuoteLease) or lease != self._pending:
                raise ContractError("Invalid or stale quote lease")
            now = self._now()
            self._cooldown_until = max(self._cooldown_until,
                                       now + retry_after_seconds)
            self._pending = None

    def state(self):
        with self._lock:
            now = self._now()
            return {"pending": self._pending is not None,
                    "cooldown_seconds": max(0.0, self._cooldown_until - now),
                    "last_global_attempt": self._last_global,
                    "attempted_symbol_count": len(self._last_attempts)}
