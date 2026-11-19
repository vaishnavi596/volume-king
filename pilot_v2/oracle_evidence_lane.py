"""Opt-in, server-only Dhan evidence read lane sharing the quote rate budget.

A separately reviewed *private* Oracle collector is required. This adapter
does not infer Dhan identity from arbitrary client JSON, connect to an
unreviewed URL, invent price bars/option factors, or verify LIVE freshness.
Default production factory injects no collector: /v2-pilot/evidence -> 503.
"""
from copy import deepcopy
from dataclasses import dataclass
from math import isfinite
from threading import RLock

from .evidence_contract import validate_evidence_envelope
from .internal_dhan_read_port import DhanRateLimited, DhanReadUnavailable
from .shared_read_budget import SharedReadBudget, BudgetDenied
from .unified_data_pipeline import PipelineUnavailable


@dataclass(frozen=True)
class DhanEvidenceBatch:
    """Private collector result, NOT a device-controlled HTTP schema."""
    source: str
    revision: int
    observed_at: float
    events: list


class OracleDhanEvidenceLane:
    """One read-only Dhan evidence demand lane across signed devices.

    The trusted transport must return a DhanEvidenceBatch from an audited,
    operator-owned Dhan-only collector. Its provenance is independently an
    operational acceptance gate. A mere source='dhan' label cannot prove it.
    """

    def __init__(self, *, transport, read_budget, monotonic, clock,
                 cache_seconds=30):
        if (not callable(transport) or not isinstance(read_budget, SharedReadBudget)
                or not callable(monotonic) or not callable(clock)
                or type(cache_seconds) not in (int, float)
                or not 1 <= cache_seconds <= 300):
            raise ValueError("Approved private Dhan evidence transport required")
        self._transport = transport
        self._budget = read_budget
        self._mono = monotonic
        self._clock = clock
        self._ttl = cache_seconds
        self._lock = RLock()
        self._cached = None
        self._revision = -1

    def __call__(self, device_id):
        # The HTTP gateway has already checked the signed session and will
        # enforce per-event index/equity permission before sending anything.
        if type(device_id) is not str or not device_id:
            raise PipelineUnavailable("Verified reader identity required")
        with self._lock:
            now = self._mono()
            if type(now) not in (int, float) or not isfinite(now) or now < 0:
                raise PipelineUnavailable("Invalid evidence cache clock")
            if self._cached is not None and 0 <= now - self._cached[0] < self._ttl:
                return deepcopy(self._cached[1])
            try:
                self._budget.reserve()
                batch = self._transport()
                source_time = self._clock()
                if (type(batch) is not DhanEvidenceBatch
                        or batch.source != "dhan"
                        or type(batch.revision) is not int
                        or batch.revision <= self._revision
                        or type(batch.observed_at) not in (int, float)
                        or not isfinite(batch.observed_at)
                        or type(source_time) not in (int, float)
                        or not isfinite(source_time)
                        or not 0 < batch.observed_at <= source_time + 5
                        or batch.observed_at < source_time - 86400):
                    raise ValueError("Unverified Dhan evidence revision or observation")
                value = validate_evidence_envelope({"events": batch.events})
            except DhanRateLimited:
                self._budget.throttle()
                raise PipelineUnavailable("Dhan evidence provider cooldown") from None
            except (BudgetDenied, DhanReadUnavailable, ValueError, TypeError, OSError,
                    TimeoutError, LookupError):
                # Do not overwrite last-good cache, fabricate events or retry
                # on a missing/unverified source.
                raise PipelineUnavailable("Dhan evidence not verified") from None
            self._revision = batch.revision
            self._cached = (now, deepcopy(value))
            return deepcopy(value)


class RoundRobinDhanEvidenceTransport:
    """One protected Oracle read per demand, never simultaneous Dhan fanout.

    Batches from different source lanes receive one aggregate revision while
    their individual per-event revisions remain source-local and monotonic.
    Failures rotate to the next source, preserving last-good app histories.
    """

    def __init__(self, transports):
        if (type(transports) not in (list, tuple) or not transports
                or len(transports) > 8 or any(not callable(t) for t in transports)):
            raise ValueError("Approved bounded Dhan evidence transports required")
        self._transports = tuple(transports)
        self._next = 0
        self._revision = 0
        self._lock = RLock()

    def __call__(self):
        with self._lock:
            transport = self._transports[self._next]
            self._next = (self._next + 1) % len(self._transports)
            batch = transport()
            if type(batch) is not DhanEvidenceBatch or batch.source != "dhan":
                raise PipelineUnavailable("Unverified source collection")
            self._revision += 1
            return DhanEvidenceBatch("dhan", self._revision,
                                     batch.observed_at, batch.events)
