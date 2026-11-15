"""Presentation and coverage accounting; never creates a directional vote."""
from copy import deepcopy
from time import time


def complete_filter_rows(result, selected, modes=None):
    """Every selected rule remains visible when data cannot be analyzed."""
    modes = modes or {}
    votes = {v.get("name"): v for v in result.get("votes", [])
             if isinstance(v, dict) and isinstance(v.get("name"), str)}
    rows = []
    for name in dict.fromkeys(selected):
        if modes.get(name) == "Chart":
            row = {"name": name, "vote": None, "detail": "Chart only; excluded from analysis"}
        elif name in votes:
            row = deepcopy(votes[name])
        else:
            row = {"name": name, "vote": None,
                   "detail": result.get("reason") or "Analysis unavailable"}
        rows.append(row)
    return rows


class AnalysisAudit:
    """Current-provider, current-settings technical audit, not Five Engine proof."""
    def __init__(self):
        self.context = None
        self.rows = {}

    def reset(self, context):
        if context != self.context:
            self.context = context
            self.rows.clear()

    def record(self, symbol, timeframe, *, result=None, stage="analysis",
               error=None, elapsed=None, candle_count=0):
        result = result or {}
        votes = result.get("votes") or []
        self.rows[(symbol, timeframe)] = {
            "symbol": symbol, "timeframe": timeframe, "stage": stage,
            "status": "ERROR" if error else "ANALYZED" if result.get("timestamp") else "INSUFFICIENT",
            "reason": error or result.get("reason", "No completed candle analysis"),
            "candle_time": result.get("timestamp"), "received_at": time(),
            "candle_count": candle_count, "elapsed": elapsed,
            "available_filters": sum(v.get("vote") is not None for v in votes if isinstance(v, dict)),
            "unavailable_filters": sum(v.get("vote") is None for v in votes if isinstance(v, dict)),
        }

    def coverage(self, symbols, timeframe="5m"):
        rows = [deepcopy(self.rows.get((sym, timeframe), {
            "symbol": sym, "timeframe": timeframe, "status": "PENDING",
            "stage": "not attempted", "reason": "Waiting for current data/settings",
        })) for sym in dict.fromkeys(symbols)]
        counts = {state: sum(r["status"] == state for r in rows)
                  for state in ("ANALYZED", "INSUFFICIENT", "ERROR", "PENDING")}
        return rows, counts
