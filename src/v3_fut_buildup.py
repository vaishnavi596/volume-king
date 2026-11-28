"""B253: index-futures build-up classification from price AND open interest (pure, read-only, never a vote by itself).

price up + OI up   -> LONG_BUILDUP     (new longs, bullish)
price down + OI up -> SHORT_BUILDUP    (new shorts, bearish)
price up + OI down -> SHORT_COVERING   (shorts leaving, weakly bullish)
price down + OI down -> LONG_UNWINDING (longs leaving, weakly bearish)
"""
import math

STATES = {"LONG_BUILDUP": (1, 1.0), "SHORT_BUILDUP": (-1, 1.0),
          "SHORT_COVERING": (1, 0.5), "LONG_UNWINDING": (-1, 0.5)}


def futures_buildup(bars, oi, n=30, min_price_frac=0.0005, min_oi_frac=0.001):
    """bars: [(t,o,h,l,c,v)...]; oi: same-length list of open interest. None unless both moved enough.

    Returns {"state","direction","weight","price_change","oi_change_pct"}.
    """
    if not isinstance(bars, (list, tuple)) or not isinstance(oi, (list, tuple)) or len(bars) != len(oi) or len(bars) <= n:
        return None
    try:
        p0, p1 = float(bars[-n - 1][4]), float(bars[-1][4])
        o0, o1 = float(oi[-n - 1]), float(oi[-1])
    except (TypeError, ValueError, IndexError):
        return None
    if not all(math.isfinite(x) for x in (p0, p1, o0, o1)) or p0 <= 0 or o0 <= 0:
        return None
    dp, do = (p1 - p0) / p0, (o1 - o0) / o0
    if abs(dp) < min_price_frac or abs(do) < min_oi_frac:
        return None
    state = ("LONG_BUILDUP" if do > 0 else "SHORT_COVERING") if dp > 0 else ("SHORT_BUILDUP" if do > 0 else "LONG_UNWINDING")
    direction, weight = STATES[state]
    return {"state": state, "direction": "BULLISH" if direction == 1 else "BEARISH", "weight": weight,
            "price_change": round(p1 - p0, 2), "oi_change_pct": round(100 * do, 2)}
