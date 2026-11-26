"""Candidate directional filters, pure functions of COMPLETED bars (no lookahead).
Each returns +1 / -1 / 0. bars: [(ts,o,h,l,c,v)] chronological, may span days (IST sessions).
Used only for measurement until a filter passes the 52% bar and is wired into the app."""
IST = 19800


def _day(ts):
    return int((ts + IST) // 86400)


def _minute(ts):
    return int(((ts + IST) % 86400) // 60)


def _split(bars):
    today = [b for b in bars if _day(b[0]) == _day(bars[-1][0])]
    prior = [b for b in bars if _day(b[0]) < _day(bars[-1][0])]
    prev = [b for b in prior if _day(b[0]) == _day(prior[-1][0])] if prior else []
    return today, prev


def orb(bars, bar_minutes=5, or_minutes=30):
    """Opening-range breakout: close beyond the first-30-min high/low, only after it completed."""
    today, _ = _split(bars)
    n = or_minutes // bar_minutes
    if len(today) <= n:
        return 0
    rng = today[:n]
    hi, lo = max(b[2] for b in rng), min(b[3] for b in rng)
    p = today[-1][4]
    return 1 if p > hi else -1 if p < lo else 0


def prev_day_levels(bars):
    """Close above previous-day high = +1, below previous-day low = -1, else 0."""
    today, prev = _split(bars)
    if not prev or not today:
        return 0
    p = today[-1][4]
    return 1 if p > max(b[2] for b in prev) else -1 if p < min(b[3] for b in prev) else 0


def prev_day_close_bias(bars):
    """Above/below the previous day's close (gap-and-hold bias)."""
    today, prev = _split(bars)
    if not prev or not today:
        return 0
    pc = prev[-1][4]
    return 1 if today[-1][4] > pc else -1 if today[-1][4] < pc else 0


def adx_trend(bars, period=14, threshold=20.0):
    """Wilder ADX: trend must exist (ADX>=threshold); direction from +DI vs -DI."""
    if len(bars) < period * 3:
        return 0
    h = [b[2] for b in bars]; l = [b[3] for b in bars]; c = [b[4] for b in bars]
    tr, pdm, mdm = [], [], []
    for i in range(1, len(bars)):
        up, dn = h[i] - h[i - 1], l[i - 1] - l[i]
        pdm.append(up if up > dn and up > 0 else 0.0)
        mdm.append(dn if dn > up and dn > 0 else 0.0)
        tr.append(max(h[i] - l[i], abs(h[i] - c[i - 1]), abs(l[i] - c[i - 1])))
    atr, p_s, m_s = sum(tr[:period]), sum(pdm[:period]), sum(mdm[:period])
    dx = []
    for i in range(period, len(tr) + 1):
        if i > period:
            atr = atr - atr / period + tr[i - 1]
            p_s = p_s - p_s / period + pdm[i - 1]
            m_s = m_s - m_s / period + mdm[i - 1]
        if atr <= 0:
            return 0
        pdi, mdi = 100 * p_s / atr, 100 * m_s / atr
        dx.append((100 * abs(pdi - mdi) / (pdi + mdi) if pdi + mdi else 0.0, pdi, mdi))
    if len(dx) < period:
        return 0
    adx = sum(d[0] for d in dx[:period]) / period
    for d in dx[period:]:
        adx = (adx * (period - 1) + d[0]) / period
    _, pdi, mdi = dx[-1]
    if adx < threshold or pdi == mdi:
        return 0
    return 1 if pdi > mdi else -1


CANDIDATES = {"ORB": orb, "PrevDay High/Low": prev_day_levels,
              "PrevDay Close": prev_day_close_bias, "ADX 14": adx_trend}
