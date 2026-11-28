"""B253: heavy-weight constituents lean for an index (pure, read-only, never a vote until the gate passes).

Index moves are driven by a handful of large stocks. For each constituent the last-30-minute change is compared
with its own typical 1m range; the weighted share of constituents that moved decisively gives the lean.
WEIGHTS are APPROXIMATE index weights (rounded, not exchange-published numbers) and only rank importance.
"""
import math

WEIGHTS = {
    "NIFTY": {"HDFCBANK": 13.0, "RELIANCE": 9.0, "ICICIBANK": 8.0, "INFY": 5.0, "TCS": 4.0},
    "BANKNIFTY": {"HDFCBANK": 28.0, "ICICIBANK": 24.0},
    "SENSEX": {"HDFCBANK": 14.0, "RELIANCE": 11.0, "ICICIBANK": 9.0, "INFY": 6.0, "TCS": 5.0},
}
LOOKBACK = 30
MIN_COVERAGE = 0.6   # share of the listed weight that must have usable data


def constituents(index):
    return tuple(WEIGHTS.get(index, {}))


def _move(bars):
    """(change, decisive) for one constituent over the last LOOKBACK bars; decisive = move beats half the typical 30-bar range."""
    if not isinstance(bars, (list, tuple)) or len(bars) <= LOOKBACK:
        return None
    try:
        c0, c1 = float(bars[-LOOKBACK - 1][4]), float(bars[-1][4])
        rng = sum(float(b[2]) - float(b[3]) for b in bars[-LOOKBACK:]) / LOOKBACK
    except (TypeError, ValueError, IndexError):
        return None
    if not all(math.isfinite(x) for x in (c0, c1, rng)) or c0 <= 0:
        return None
    change = c1 - c0
    return change, abs(change) >= 0.5 * rng * math.sqrt(LOOKBACK)


def heavy_lean(index, bars_by_symbol):
    """{"bullish","bearish","lean","coverage","decisive"} or None when coverage is thin."""
    w = WEIGHTS.get(index)
    if not w:
        return None
    total = sum(w.values())
    used = up = down = 0.0
    decisive = 0
    for sym, weight in w.items():
        m = _move((bars_by_symbol or {}).get(sym))
        if m is None:
            continue
        used += weight
        change, dec = m
        if dec and change > 0:
            up += weight; decisive += 1
        elif dec and change < 0:
            down += weight; decisive += 1
    if used / total < MIN_COVERAGE or decisive == 0:
        return None
    bull = round(50 + 50 * (up - down) / used)
    return {"bullish": bull, "bearish": 100 - bull,
            "lean": "BULLISH" if bull > 55 else "BEARISH" if bull < 45 else "NEUTRAL",
            "coverage": round(used / total, 2), "decisive": decisive, "vote_eligible": False}
