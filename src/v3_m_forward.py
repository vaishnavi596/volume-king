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


def m_lean(bars, horizon=HORIZON_MINUTES, now=None):
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
    if _past_close(bars, horizon, now):
        return None   # B252: a LIVE forecast that runs past the 15:30 close has no meaning
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
    # B252 regime: efficiency ratio (straight move / total wiggle). Sideways markets damp the lean.
    path = sum(abs(closes[i] - closes[i - 1]) for i in range(1, n))
    er = abs(closes[-1] - closes[0]) / path if path > 0 else 0.0
    regime = "TREND" if er >= 0.3 else "SIDEWAYS" if er < 0.15 else "MIXED"
    score *= {"TREND": 1.0, "MIXED": 0.8, "SIDEWAYS": 0.5}[regime]
    bull = round(50 + 50 * score)
    bear = 100 - bull
    return {"bullish": bull, "bearish": bear,
            "lean": "BULLISH" if bull > 55 else "BEARISH" if bull < 45 else "NEUTRAL",
            "strength": round(abs(score), 3), "horizon_minutes": horizon,
            "regime": regime, "efficiency": round(er, 3), "vote_eligible": False}


def _last_epoch(bars):
    for b in reversed(list(bars or ())):
        try:
            t = float(b[0])
        except (TypeError, ValueError, IndexError):
            continue
        return t if t > 1e9 else None
    return None


def _past_close(bars, horizon, now=None):
    """True when last bar time + horizon is beyond the 15:30 IST close.

    Only for a LIVE lean (last bar within 10 minutes of `now`): after the close the HIST lean of the finished
    session stays available as context (B254 fix: B252 wrongly blanked box M all evening)."""
    t = _last_epoch(bars)
    if t is None:
        return False
    import time as _time
    if abs((now if now is not None else _time.time()) - t) > 600:
        return False
    from datetime import datetime, timezone, timedelta
    d = datetime.fromtimestamp(t, timezone(timedelta(hours=5, minutes=30)))
    return d.hour * 60 + d.minute + horizon > 930


def min_move(bars, price, horizon):
    """Smallest price move (points) that counts as a real move at this horizon; smaller moves are noise."""
    rngs = []
    for b in list(bars or ())[-60:]:
        try:
            h, l = float(b[2]), float(b[3])
        except (TypeError, ValueError, IndexError):
            continue
        if math.isfinite(h) and math.isfinite(l) and h >= l:
            rngs.append(h - l)
    mean_rng = sum(rngs) / len(rngs) if rngs else 0.0
    try:
        p = float(price)
    except (TypeError, ValueError):
        p = 0.0
    return round(max(0.0008 * p * math.sqrt(horizon / 30.0), 0.5 * mean_rng * math.sqrt(horizon)), 4)


def resolve_prediction(entry_price, lean, price_after, min_move=0.0):
    """Ledger rule: NEUTRAL is not scored; a move smaller than min_move is noise (not scored);
    otherwise hit when price moved in the lean's direction."""
    if lean == "NEUTRAL" or not all(type(x) in (int, float) and math.isfinite(x) for x in (entry_price, price_after)):
        return None
    if price_after == entry_price or abs(price_after - entry_price) < (min_move or 0.0):
        return None
    return (price_after > entry_price) == (lean == "BULLISH")


def wilson_low(hits, n, z=1.28):
    """Lower confidence bound (%) of a hit-rate; z=1.28 is ~90% one-sided. None when n is 0."""
    if not n:
        return None
    p = hits / n
    d = 1 + z * z / n
    centre = p + z * z / (2 * n)
    spread = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round(100 * (centre - spread) / d, 1)


def strength_band(strength):
    try:
        v = float(strength)
    except (TypeError, ValueError):
        return "LOW"
    return "HIGH" if v >= 0.6 else "MID" if v >= 0.3 else "LOW"


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


def orb_levels(bars, minutes=15):
    """Opening-range high/low (first `minutes` after 9:15 IST) of the bars' own day, and the last close."""
    from datetime import datetime, timezone, timedelta
    ist = timezone(timedelta(hours=5, minutes=30))
    hi = lo = last = None
    day = None
    for b in bars or ():
        try:
            t = float(b[0]); h = float(b[2]); l = float(b[3]); c = float(b[4])
        except (TypeError, ValueError, IndexError):
            continue
        if t < 1e9 or not all(math.isfinite(x) for x in (h, l, c)):
            continue
        d = datetime.fromtimestamp(t, ist)
        if day is None:
            day = d.date()
        if d.date() != day:
            continue
        m = d.hour * 60 + d.minute
        last = (m, c)
        if 555 <= m < 555 + minutes:
            hi = h if hi is None else max(hi, h)
            lo = l if lo is None else min(lo, l)
    if hi is None or last is None or last[0] < 555 + minutes:
        return None
    return {"high": hi, "low": lo, "close": last[1]}


def m_context(lean, bars, engine_biases=None, now=None, oi_lean=None, prev_close=None):
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
    if len(bi) >= 2:   # B252: callers pass INDEPENDENT sources only (candle frames collapsed to one)
        aligned = sum((b == "BULLISH") == (sign == 1) for b in bi)
        checks.append(("ENGINES", aligned * 2 > len(bi)))
    orb = orb_levels(bars)
    if orb and (orb["close"] > orb["high"] or orb["close"] < orb["low"]):
        checks.append(("ORB", (orb["close"] > orb["high"]) == (sign == 1)))
    if type(prev_close) in (int, float) and prev_close > 0 and orb:
        if orb["close"] != prev_close:
            checks.append(("PDC", (orb["close"] > prev_close) == (sign == 1)))
    if isinstance(oi_lean, dict) and type(oi_lean.get("bullish")) in (int, float):
        tilt = oi_lean["bullish"] - 50
        if abs(tilt) >= 5:
            checks.append(("OI", (tilt > 0) == (sign == 1)))
    agree = sum(1 for _, ok in checks if ok)
    total = len(checks)
    window = window_of(now) if now is not None else "OTHER"
    conf = (0.5 + 0.5 * agree / total) if total else 0.7
    adj = round(float(lean.get("strength", 0)) * _WINDOW_FACTOR.get(window, 0.7) * conf, 3)
    return {"checks": [{"name": n, "agrees": bool(ok)} for n, ok in checks], "agree": agree, "total": total,
            "window": window, "adj_strength": adj, "confidence": confidence_label(adj),
            "regime": lean.get("regime")}
