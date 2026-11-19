"""Single logical V2 pipeline: one secure read port, independently gated lanes.

No broker SDK or HTTP calls. A verified login gateway must authorize a device
BEFORE calling dispatch(). Market auto-refresh is IST-gated, manual refresh may
run outside hours. Unsupported features fail closed, never return fake live.
"""
from __future__ import annotations

from datetime import datetime, time
from threading import RLock
from zoneinfo import ZoneInfo

from .internal_dhan_read_port import InternalDhanReadPort, DhanReadUnavailable
from .api_contract import validate_snapshot

IST = ZoneInfo("Asia/Kolkata")
START = time(9, 10)
END = time(15, 45)
SUPPORTED = frozenset(("quotes", "indices"))
FUTURE_LANES = frozenset(("candles", "scanner", "super_five", "options", "assessment"))
CACHE_SECONDS = {"quotes": 180, "indices": 60}


class PipelineUnavailable(RuntimeError):
    pass


def market_poll_allowed(moment):
    if not isinstance(moment, datetime) or moment.tzinfo is None:
        raise ValueError("Timezone-aware datetime required")
    local = moment.astimezone(IST)
    return local.weekday() < 5 and START <= local.time().replace(tzinfo=None) <= END


class V2UnifiedReadPipeline:
    """Read-only common gateway with bounded cache shared across authorized devices."""

    def __init__(self, *, read_port, clock, monotonic):
        if not isinstance(read_port, InternalDhanReadPort):
            raise ValueError("Explicit Dhan-only read port required")
        if not callable(clock) or not callable(monotonic):
            raise ValueError("Verified clock sources required")
        self._port = read_port
        self._clock = clock
        self._mono = monotonic
        self._cache = {}
        self._lock = RLock()

    def dispatch(self, device_id, feed, *, manual=False):
        if (type(device_id) is not str or not device_id or
                type(feed) is not str or type(manual) is not bool):
            raise PipelineUnavailable("Invalid authorized request")
        if feed in FUTURE_LANES:
            raise PipelineUnavailable("Source lane not connected")
        if feed not in SUPPORTED:
            raise PipelineUnavailable("Unsupported V2 feed")
        if not manual and not market_poll_allowed(self._clock()):
            raise PipelineUnavailable("Automatic data polling outside IST market hours")
        # Do NOT trust the device identifier from HTTP; the verified session
        # layer must call this with the server-authorized device identity.
        with self._lock:
            now = self._mono()
            if type(now) not in (int, float) or not 0 <= now < float("inf"):
                raise PipelineUnavailable("Invalid cache clock")
            cached = self._cache.get(feed)
            if cached and 0 <= now - cached[0] < CACHE_SECONDS[feed]:
                return validate_snapshot(cached[1])
            try:
                snapshot = validate_snapshot(self._port(device_id, feed))
            except (DhanReadUnavailable, ValueError, TypeError):
                # Client and app retain last-good. Do not silently relabel an
                # old snapshot as newly verified or substitute a fake quote.
                raise PipelineUnavailable("Read-only Dhan lane unavailable") from None
            self._cache[feed] = (now, snapshot)
            return snapshot
