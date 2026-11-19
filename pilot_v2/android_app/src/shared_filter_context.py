"""Shared read-only five-filter view across V2 app screens.

Values are sourced exclusively from the existing evidence inbox.
Never infer trading directions, percentages, live status or a sixth vote.
"""
from app_state import INDEXES, MAX_EQUITIES
from filter_evidence import FILTER_LABELS


def shared_filter_context(filters, symbol, timeframe, *, selected_equities=()):
    selected = tuple(selected_equities)
    if (type(symbol) is not str or type(timeframe) is not str
            or timeframe not in ("1m", "3m", "5m", "15m", "30m")
            or len(selected) > MAX_EQUITIES
            or any(type(s) is not str or not s or s in INDEXES for s in selected)
            or len(selected) != len(set(selected))
            or symbol not in INDEXES + selected):
        raise ValueError("Invalid symbol, selected roster or timeframe")
    six = tuple(filters.rows(symbol, timeframe, selected_equities=selected))
    if (len(six) != 6 or six[5] != ("", "")
            or tuple(name for name, _ in six[:5]) != FILTER_LABELS):
        raise ValueError("Invalid five-filter evidence layout")
    values = six[:5]
    if any(value not in ("WAIT", "BULLISH HIST", "BEARISH HIST", "NEUTRAL HIST")
           for _, value in values):
        raise ValueError("Unverified filter presentation")
    covered = sum(value != "WAIT" for _, value in values)
    compact = ("5 filters WAIT · no verified evidence" if not covered else
               " · ".join(f"{name} {value}" for name, value in values
                          if value != "WAIT"))
    return {
        "symbol": symbol, "timeframe": timeframe,
        "rows": values, "sixth": ("", ""), "coverage": covered,
        "coverage_label": f"{covered}/5 historical factors · " +
                          ("WAIT" if not covered else "HIST (not LIVE)"),
        "compact": compact, "live_verified": False,
    }
