"""V2 read-only Dhan collector port: server-owned, fail-closed, no HTTP or SDK.

A separately authorized server process must inject a genuine Dhan read adapter.
The request identity never contains broker credentials and does not establish
market freshness. No implicit cache fallback, fake provider, or live trading.
"""
from __future__ import annotations

from dataclasses import dataclass
import time
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


class InternalDhanReadPort:
    """Compose only a server-injected Dhan transport, never user-supplied data."""

    def __init__(self, *, transport, selected_equities, clock=None):
        if not callable(transport):
            raise ValueError("Authorized internal Dhan read transport required")
        if type(selected_equities) not in (tuple, list):
            raise ValueError("Server-owned equity roster required")
        selected = tuple(selected_equities)
        if len(selected) > 70 or len(set(selected)) != len(selected):
            raise ValueError("Invalid equity selection")
        # Validate selection before any transport call, even with empty data.
        try:
            normalize_dhan_readonly(
                feed="quotes", selected=selected, rows={},
                revision=0, observed_at=1, now=1)
        except IngressRejected as exc:
            if str(exc) != "Incomplete provider snapshot":
                raise ValueError("Invalid equity selection") from None
        self._transport = transport
        self._equities = selected
        self._clock = clock or time.time

    def __call__(self, device_id, feed):
        # This port must be used behind verified session authorization.
        if type(device_id) is not str or not device_id:
            raise DhanReadUnavailable("Verified internal device identity required")
        if type(feed) is not str or feed not in ("quotes", "indices"):
            raise DhanReadUnavailable("Unsupported feed")
        selected = INDEXES if feed == "indices" else self._equities
        try:
            batch = self._transport(feed, selected)
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
