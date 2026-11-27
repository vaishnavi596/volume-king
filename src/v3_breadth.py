"""B248 Breadth: share of the watchlist moving up vs down (display only, never a vote)."""
import math


def breadth(changes):
    """changes: iterable of day-change % (None/invalid ignored). Returns dict or None."""
    up = down = flat = 0
    for v in changes:
        if type(v) not in (int, float) or not math.isfinite(v):
            continue
        if v > 0.05:
            up += 1
        elif v < -0.05:
            down += 1
        else:
            flat += 1
    total = up + down + flat
    if total < 10:
        return None
    return {"up": up, "down": down, "flat": flat, "total": total,
            "up_pct": round(100 * up / total)}


def breadth_text(b):
    if not b:
        return "Breadth: n/a"
    lean = "bullish" if b["up_pct"] >= 60 else "bearish" if b["up_pct"] <= 40 else "mixed"
    return "Breadth %d↑ %d↓ %d= of %d • %s • not voted" % (b["up"], b["down"], b["flat"], b["total"], lean)
