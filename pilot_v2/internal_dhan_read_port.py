"""V2 read-only Dhan collector port: server-owned, fail-closed, no HTTP or SDK.

A separately authorized server process must inject a genuine Dhan read adapter.
The request identity never contains broker credentials and does not establish
market freshness. No implicit cache fallback, fake provider, or live trading.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
from threading import RLock
from .dhan_readonly_ingress import IngressRejected, normalize_dhan_readonly

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")


@dataclass(frozen=True)
class DhanReadBatch:
    source: str
    symbols: tuple
    rows: dict
    revision: int
    observed_at: float


class DhanReadUnavailable(RuntimeError):
    pass


class DhanRateLimited(DhanReadUnavailable):
    """Only the approved internal Dhan adapter may signal provider HTTP 429."""
    pass


class InternalDhanReadPort:
    """Compose only a server-injected Dhan transport, never user-supplied data."""

    def __init__(self, *, transport, selected_equities, clock=None):
        if not callable(transport):
            raise ValueError("Authorized internal Dhan read transport required")
        if type(selected_equities) not in (tuple, list):
            raise ValueError("Server-owned equity roster required")
        self._transport = transport
        self._equities = self._validated_equities(selected_equities)
        self._clock = clock or time.time
        self._lock = RLock()

    @staticmethod
    def _validated_equities(symbols):
        if type(symbols) not in (tuple, list):
            raise ValueError("Server-owned equity roster required")
        selected = tuple(symbols)
        # Reject unhashable/malformed inputs before duplicate hashing.
        if (len(selected) > 70 or any(type(s) is not str for s in selected)
                or len(set(selected)) != len(selected)):
            raise ValueError("Invalid equity selection")
        try:
            normalize_dhan_readonly(
                feed="quotes", selected=selected, rows={},
                revision=0, observed_at=1, now=1)
        except IngressRejected as exc:
            if str(exc) != "Incomplete provider snapshot":
                raise ValueError("Invalid equity selection") from None
        return selected

    def has_selected_equities(self):
        with self._lock:
            return bool(self._equities)

    def replace_selected_equities(self, symbols):
        """Server-controlled roster change, never a direct device HTTP action."""
        validated = self._validated_equities(symbols)
        with self._lock:
            changed = validated != self._equities
            self._equities = validated
            return changed

    def __call__(self, device_id, feed):
        # This port must be used behind verified session authorization.
        if type(device_id) is not str or not device_id:
            raise DhanReadUnavailable("Verified internal device identity required")
        if type(feed) is not str or feed not in ("quotes", "indices"):
            raise DhanReadUnavailable("Unsupported feed")
        with self._lock:
            selected = INDEXES if feed == "indices" else self._equities
            try:
                batch = self._transport(feed, selected)
            except DhanRateLimited:
                raise
            except Exception:
                raise DhanReadUnavailable("Authorized Dhan transport unavailable") from None
            if not isinstance(batch, DhanReadBatch) or batch.source != "dhan":
                raise DhanReadUnavailable("Trusted Dhan transport evidence missing")
            if batch.symbols != selected:
                raise DhanReadUnavailable("Dhan response does not match requested roster")
            try:
                return normalize_dhan_readonly(
                    feed=feed, selected=selected, rows=batch.rows,
                    revision=batch.revision, observed_at=batch.observed_at,
                    now=self._clock())
            except (IngressRejected, TypeError, ValueError):
                raise DhanReadUnavailable("Invalid Dhan read-only response") from None
