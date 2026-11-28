"""B248 box M: short-horizon forward lean (display + ledger only, never a vote).

Pure and offline. Input: completed 1m bars [(t,o,h,l,c,v),...]. Output a lean
(bullish/bearish %) for the next ~20 minutes from price slope vs recent range.
It is an expectation to be MEASURED by a ledger; until a measured hit-rate
exists it must not be counted in the live vote.
"""
import math

HORIZON_MINUTES = 20
MIN_BARS = 30


HORIZONS = (20, 30, 60)
_WINDOW = {20: 60, 30: 60, 60: 90}
_MIN = {20: 30, 30: 30, 60: 45}


def m_lean(bars, horizon=HORIZON_MINUTES):
    """Return {"bullish","bearish","lean","strength"} or None when evidence is thin.

    horizon: 20, 30 or 60 minutes (B249). 60 needs more bars (45+) so it appears later in the session."""
    if horizon not in _WINDOW:
        return None
    clean = []
    for b in bars or ():
        try:
            c = float(b[4]); h = float(b[2]); l = float(b[3])
        except (TypeError, ValueError, IndexError):
            continue
        if all(math.isfinite(x) and x > 0 for x in (c, h, l)) and h >= l:
            clean.append((h, l, c))
    clean = clean[-_WINDOW[horizon]:]
    if len(clean) < _MIN[horizon]:
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
    score = max(-1.0, min(1.0, slope * math.sqrt(horizon * HORIZON_MINUTES) / (rng * 4)))  # sqrt: longer horizons do not saturate
    # Reversal damper: last 5 bars against the slope reduce confidence.
    recent = closes[-1] - closes[-6]
    if score * recent < 0:
        score *= 0.5
    bull = round(50 + 50 * score)
    bear = 100 - bull
    return {"bullish": bull, "bearish": bear,
            "lean": "BULLISH" if bull > 55 else "BEARISH" if bull < 45 else "NEUTRAL",
            "strength": round(abs(score), 3), "horizon_minutes": horizon,
            "vote_eligible": False}


def resolve_prediction(entry_price, lean, price_after):
    """Ledger rule: NEUTRAL is not scored; otherwise hit when price moved in the lean's direction."""
    if lean == "NEUTRAL" or not all(type(x) in (int, float) and math.isfinite(x) for x in (entry_price, price_after)):
        return None
    if price_after == entry_price:
        return None
    return (price_after > entry_price) == (lean == "BULLISH")


def m_leans(bars):
    """All horizons at once: {"20":lean|None,"30":...,"60":...}."""
    return {str(h): m_lean(bars, h) for h in HORIZONS}


def confidence_label(strength):
    """Plain-language confidence from lean strength (NOT a measured probability)."""
    try:
        v = float(strength)
    except (TypeError, ValueError):
        return "—"
    return "मज़बूत" if v >= 0.6 else "मध्यम" if v >= 0.3 else "हल्का"


WINDOWS = (("OPEN_VOLATILE", 555, 585), ("SETTLING", 585, 600), ("BEST_TREND", 600, 690),
           ("MIDDAY_QUIET", 690, 810), ("AFTERNOON", 810, 900), ("LATE_RISKY", 900, 931))
_WINDOW_FACTOR = {"OPEN_VOLATILE": 0.6, "SETTLING": 0.8, "BEST_TREND": 1.0, "MIDDAY_QUIET": 0.7,
                  "AFTERNOON": 0.9, "LATE_RISKY": 0.7, "OTHER": 0.7}


def window_of(ts):
    """IST time-window label for an epoch timestamp (general table; the ledger measures it)."""
    from datetime import datetime, timezone, timedelta
    t = datetime.fromtimestamp(ts, timezone(timedelta(hours=5, minutes=30)))
    m = t.hour * 60 + t.minute
    for name, a, b in WINDOWS:
        if a <= m < b:
            return name
    return "OTHER"


def _vwap_and_volume(bars):
    pv = vv = 0.0
    vols = []
    last = None
    for b in bars or ():
        try:
            h, l, c, v = float(b[2]), float(b[3]), float(b[4]), float(b[5])
        except (TypeError, ValueError, IndexError):
            continue
        if not all(math.isfinite(x) for x in (h, l, c, v)) or v < 0 or c <= 0:
            continue
        pv += (h + l + c) / 3 * v; vv += v; vols.append(v); last = c
    if vv <= 0 or last is None or len(vols) < 20:
        return None, None
    recent = sum(vols[-10:]) / 10
    before = sum(vols[:-10]) / max(1, len(vols) - 10)
    return (1 if last > pv / vv else -1 if last < pv / vv else 0), (recent / before if before > 0 else None)


def m_context(lean, bars, engine_biases=None, now=None):
    """Confluence around one lean. Returns {"checks":[...], "agree","total","window","adj_strength","confidence"}.

    engine_biases: iterable of "BULLISH"/"BEARISH"/other from the other engine rows (any timeframe).
    Pure; never a vote. Adjusted strength = lean strength x window factor x confluence factor.
    """
    if not isinstance(lean, dict) or lean.get("lean") not in ("BULLISH", "BEARISH"):
        return None
    sign = 1 if lean["lean"] == "BULLISH" else -1
    checks = []
    side, vol_ratio = _vwap_and_volume(bars)
    if side is not None:
        checks.append(("VWAP", side == sign))
    if vol_ratio is not None:
        checks.append(("VOLUME", vol_ratio >= 1.0))
    bi = [b for b in (engine_biases or ()) if b in ("BULLISH", "BEARISH")]
    if len(bi) >= 3:
        aligned = sum((b == "BULLISH") == (sign == 1) for b in bi)
        checks.append(("ENGINES", aligned * 2 > len(bi)))
    agree = sum(1 for _, ok in checks if ok)
    total = len(checks)
    window = window_of(now) if now is not None else "OTHER"
    conf = (0.5 + 0.5 * agree / total) if total else 0.7
    adj = round(float(lean.get("strength", 0)) * _WINDOW_FACTOR.get(window, 0.7) * conf, 3)
    return {"checks": [{"name": n, "agrees": bool(ok)} for n, ok in checks], "agree": agree, "total": total,
            "window": window, "adj_strength": adj, "confidence": confidence_label(adj)}
