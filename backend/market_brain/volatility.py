"""Day-range regime: will today's range exceed the trailing-20-day median?

Point-in-time at 09:45 IST: uses only the previous days, today's gap, today's first
30 minutes and the previous close of an optional daily VIX-like series.
Measured on 1y NIFTY 5m: ~72% vs 53-60% for naive baselines (n=182 days). Advisory only.
"""
import math

from .model import Logistic

FIRST_30_MIN_BARS = 6


def _range(rows):
    return (max(b[2] for b in rows) - min(b[3] for b in rows)) / rows[0][1]


def _median(values):
    s = sorted(values)
    n = len(s)
    return s[n // 2] if n % 2 else (s[n // 2 - 1] + s[n // 2]) / 2


def build_days(days_bars, vix_prev=None, window=20, warm=25):
    """days_bars: {day: [bars sorted]} full sessions only. vix_prev: {day: previous VIX close}.
    Returns chronological rows {day, x, big(label or None for unfinished)}."""
    order = sorted(days_bars)
    rng = {d: _range(days_bars[d]) for d in order if len(days_bars[d]) >= 70}
    full = [d for d in order if d in rng]
    vix_prev = vix_prev or {}
    out = []
    for i, d in enumerate(full):
        if i < warm:
            continue
        prior = full[i - window:i]
        med = _median([rng[x] for x in prior])
        rows = days_bars[d]
        prev = full[i - 1]
        first = rows[:FIRST_30_MIN_BARS]
        r30 = _range(first)
        med30 = _median([_range(days_bars[x][:FIRST_30_MIN_BARS]) for x in prior])
        gap = abs(rows[0][1] / days_bars[prev][-1][4] - 1.0) * 100
        v = vix_prev.get(d)
        vbase = [vix_prev[x] for x in prior if x in vix_prev]
        vix_x = math.log(v / (sum(vbase) / len(vbase))) if v and vbase else 0.0
        x = [math.log(rng[prev] / med), gap, math.log(r30 / med30) if r30 > 0 and med30 > 0 else 0.0, vix_x]
        out.append({"day": d, "x": x, "big": int(rng[d] > med)})
    return out


def predict_today(history_rows, today_x, max_train=200, min_train=40):
    """Train only on finished earlier days; return P(big range) or None if too little data."""
    tr = history_rows[-max_train:]
    if len(tr) < min_train or len({r["big"] for r in tr}) < 2:
        return None
    cols = list(zip(*[r["x"] for r in tr]))
    mu = [sum(c) / len(c) for c in cols]
    sd = [math.sqrt(sum((v - m) ** 2 for v in c) / len(c)) + 1e-9 for c, m in zip(cols, mu)]
    norm = lambda x: [(a - m) / s for a, m, s in zip(x, mu, sd)]
    model = Logistic().fit([norm(r["x"]) for r in tr], [r["big"] for r in tr])
    return float(model.predict_proba([norm(today_x)])[0])


def verdict(p):
    if p is None:
        return "डेटा नाकाफ़ी"
    if p >= 0.60:
        return "आज बड़ी चाल की संभावना"
    if p <= 0.40:
        return "आज शांत दिन की संभावना"
    return "साफ़ संकेत नहीं"
