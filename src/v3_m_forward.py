"""B248 box M: short-horizon forward lean (display + ledger only, never a vote).

Pure and offline. Input: completed 1m bars [(t,o,h,l,c,v),...]. Output a lean
(bullish/bearish %) for the next ~20 minutes from price slope vs recent range.
It is an expectation to be MEASURED by a ledger; until a measured hit-rate
exists it must not be counted in the live vote.
"""
import math

HORIZON_MINUTES = 20
MIN_BARS = 30


def m_lean(bars):
    """Return {"bullish","bearish","lean","strength"} or None when evidence is thin."""
    clean = []
    for b in bars or ():
        try:
            c = float(b[4]); h = float(b[2]); l = float(b[3])
        except (TypeError, ValueError, IndexError):
            continue
        if all(math.isfinite(x) and x > 0 for x in (c, h, l)) and h >= l:
            clean.append((h, l, c))
    clean = clean[-60:]
    if len(clean) < MIN_BARS:
        return None
    closes = [c for _, _, c in clean]
    n = len(closes)
    xs = list(range(n))
    mx = sum(xs) / n
    my = sum(closes) / n
    var = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, closes)) / var   # price per bar
    rng = sum(h - l for h, l, _ in clean) / n or 1e-9                    # mean bar range
    # Projected move over the horizon relative to typical bar range, clipped.
    score = max(-1.0, min(1.0, slope * HORIZON_MINUTES / (rng * 4)))
    # Reversal damper: last 5 bars against the slope reduce confidence.
    recent = closes[-1] - closes[-6]
    if score * recent < 0:
        score *= 0.5
    bull = round(50 + 50 * score)
    bear = 100 - bull
    return {"bullish": bull, "bearish": bear,
            "lean": "BULLISH" if bull > 55 else "BEARISH" if bull < 45 else "NEUTRAL",
            "strength": round(abs(score), 3), "horizon_minutes": HORIZON_MINUTES,
            "vote_eligible": False}


def resolve_prediction(entry_price, lean, price_after):
    """Ledger rule: NEUTRAL is not scored; otherwise hit when price moved in the lean's direction."""
    if lean == "NEUTRAL" or not all(type(x) in (int, float) and math.isfinite(x) for x in (entry_price, price_after)):
        return None
    if price_after == entry_price:
        return None
    return (price_after > entry_price) == (lean == "BULLISH")
