"""BOT KING read-only four-lane refresh planning constants.

These are *logical* lanes and local-view targets, not four new network
requests, not broker quotas, and not evidence of Oracle production support.
Dhan calls continue to honor adapter serialization and provider cooldown.
"""
from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True)
class DataLane:
    name: str
    consumers: tuple[str, ...]
    requested_min_seconds: int
    mode: str


LANES = (
    DataLane("quotes", ("watchlist", "indices", "dashboard", "paper-mark"), 60, "oracle-cache"),
    DataLane("candles", ("scanner", "super-five", "chart", "historical-index"), 300, "completed-bars"),
    DataLane("derivatives", ("options", "oi", "pcr", "max-pain"), 30, "selected-contract"),
    DataLane("context", ("news", "assessment", "health"), 300, "independent-ttl"),
)

# Equity quote lane is a 60s provider floor, not the 2s local UI observation.
# Faster LTP must be verified with upstream transport without polling fanout.
# A local recomputation never authorizes an additional Dhan request.
SUPER_FIVE_LOCAL_TICK_SECONDS = 2
WATCHLIST_LOCAL_TICK_SECONDS = 2
SCANNER_LOCAL_TICK_SECONDS = 2
AUTO_WINDOW_IST = ((9, 10), (15, 45))


def data_changed(previous_revision, next_revision):
    """Only a real, distinct source revision warrants a data-driven repaint."""
    return next_revision is not None and next_revision != previous_revision


def completed_bar_revision(rows):
    """Stable revision from the latest completed OHLCV bar, not a quote clock."""
    if not isinstance(rows, (tuple, list)) or not rows:
        return None
    row = rows[-1]
    if not isinstance(row, (tuple, list)) or len(row) < 6:
        return None
    if any(type(v) not in (int,float) or not isfinite(v) for v in row[:6]):
        return None
    t,o,h,l,c,v=row[:6]
    if t<=0 or min(o,h,l,c)<=0 or v<0 or h<max(o,l,c) or l>min(o,h,c):
        return None
    return tuple(row[:6])
