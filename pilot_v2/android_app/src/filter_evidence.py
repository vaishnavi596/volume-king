"""V2 app-owned evidence-gated five-filter display, no synthetic signals."""
from math import isfinite

FILTER_KEYS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")
FILTER_LABELS = ("OI Support", "OI Resistance", "Max Pain", "PCR", "Candle Trend")
SIXTH_SLOT = ""  # Owner-reserved slot is never scored.
DIRECTIONS = ("bullish", "bearish", "neutral")

class FilterEvidenceError(ValueError):
    pass

def _validated_row(row):
    if (type(row) is not dict
            or set(row) != {"direction", "source", "observed_at", "eligible"}
            or row["direction"] not in DIRECTIONS
            or row["source"] != "dhan"
            or type(row["observed_at"]) is not int or row["observed_at"] <= 0
            or row["eligible"] is not True):
        raise FilterEvidenceError("Filter lacks trusted eligible source evidence")
    return {"direction": row["direction"], "source": "dhan",
            "observed_at": row["observed_at"], "eligible": True}

class LocalFilterEvidence:
    """Only accepts a complete, source-stamped, versioned trusted app input.

    Integration caller must independently authenticate Oracle and establish
    observation freshness. This module cannot prove Dhan provenance on its own.
    """
    def __init__(self):
        self._values = {}

    def accept(self, symbol, timeframe, revision, evidence, *,
               allowed_symbols, trusted_transport=False):
        if (trusted_transport is not True
                or type(symbol) is not str or symbol not in tuple(allowed_symbols)
                or timeframe not in ("1m", "3m", "5m")
                or type(revision) is not int or revision < 0
                or type(evidence) is not dict or set(evidence) != set(FILTER_KEYS)):
            raise FilterEvidenceError("Incomplete or untrusted five-filter snapshot")
        rows = {key: _validated_row(evidence[key]) for key in FILTER_KEYS}
        slot = (symbol, timeframe)
        previous = self._values.get(slot)
        if previous and revision <= previous["revision"]:
            return False
        self._values[slot] = {"revision": revision, "rows": rows}
        return True

    def rows(self, symbol, timeframe, *, selected_equities=()):
        if symbol not in ("NIFTY", "BANKNIFTY", "SENSEX") and symbol not in selected_equities:
            return tuple((label, "WAIT") for label in FILTER_LABELS) + (("", ""),)
        entry = self._values.get((symbol, timeframe))
        if not entry:
            return tuple((label, "WAIT") for label in FILTER_LABELS) + (("", ""),)
        return tuple((label, entry["rows"][key]["direction"].upper() + " HIST")
                     for key, label in zip(FILTER_KEYS, FILTER_LABELS)) + (("", ""),)

    def forget_removed(self, selected_equities):
        allowed = set(("NIFTY", "BANKNIFTY", "SENSEX")).union(selected_equities)
        self._values = {k: v for k, v in self._values.items() if k[0] in allowed}

    def compact(self, symbol, timeframe, *, selected_equities=()):
        """One shared filter presentation for the Watchlist; no sixth score."""
        five = self.rows(symbol, timeframe, selected_equities=selected_equities)[:5]
        if all(value == "WAIT" for _, value in five):
            return f"{symbol} {timeframe} filters: WAIT (5/5 no eligible evidence)"
        return f"{symbol} {timeframe} filters: " + " · ".join(
            f"{label} {value}" for label, value in five)
