"""Point-in-time feature builder: every feature at decision time T uses only data
completed at or before T (no lookahead). Times are epoch seconds (UTC); sessions are IST."""
import math
from collections import defaultdict

IST = 19800
SESSION_OPEN = 9 * 60 + 15
FIRST_DECISION = 9 * 60 + 45
LAST_DECISION = 14 * 60 + 45
BASE_FEATURES = ("ret_past30", "ret_day", "gap", "z_dev", "range_pos", "vol_ratio", "tod_prior")


def day_key(ts):
    return int((ts + IST) // 86400)


def minute_of_day(ts):
    return int(((ts + IST) % 86400) // 60)


def group_days(bars):
    """bars: list of (ts, o, h, l, c, v) -> {day: [bars sorted]} with sane OHLC only."""
    days = defaultdict(list)
    for b in bars:
        ts, o, h, l, c, v = b
        if not all(isinstance(x, (int, float)) and math.isfinite(x) for x in (ts, o, h, l, c)):
            continue
        if c <= 0 or h < l or not (l <= c <= h):
            continue
        days[day_key(ts)].append(tuple(b))
    return {d: sorted(rows) for d, rows in days.items()}


def _price_at(rows, bar_seconds, cutoff_ts):
    """Close of the last bar completed at or before cutoff_ts, else None."""
    price = None
    for ts, o, h, l, c, v in rows:
        if ts + bar_seconds <= cutoff_ts:
            price = c
        else:
            break
    return price


def _std(values):
    n = len(values)
    if n < 2:
        return 0.0
    m = sum(values) / n
    return math.sqrt(sum((x - m) ** 2 for x in values) / (n - 1))


def _ext_change(series, day):
    """Previous completed day's % change of an external daily series: values for
    days strictly before `day`. series: {day: close}."""
    prior = sorted(d for d in series if d < day)
    if len(prior) < 2:
        return 0.0
    a, b = series[prior[-2]], series[prior[-1]]
    return (b / a - 1.0) if a and a > 0 and b and b > 0 else 0.0


def build_samples(bars, ext=None, bar_minutes=5, step_minutes=30, horizon_minutes=30,
                  dead_zone=0.0003, warm_days=20):
    """Return samples [{day, minute, ts, x, names, ret, persist}] for one instrument."""
    ext = ext or {}
    bar_s = bar_minutes * 60
    days = group_days(bars)
    order = sorted(days)
    closes = {}      # day -> last close
    opens = {}
    dvol = {}        # day -> std of 5m returns
    for d in order:
        rows = days[d]
        closes[d] = rows[-1][4]
        opens[d] = rows[0][1]
        rets = [rows[i][4] / rows[i - 1][4] - 1 for i in range(1, len(rows))]
        dvol[d] = _std(rets)
    tod_hist = defaultdict(list)   # minute -> [(day, ret)] chronological
    names = BASE_FEATURES + tuple("ext_" + k for k in sorted(ext))
    samples = []
    for idx, d in enumerate(order):
        rows = days[d]
        day_midnight_utc = d * 86400 - IST
        todays = []
        for m in range(FIRST_DECISION, LAST_DECISION + 1, step_minutes):
            T = day_midnight_utc + m * 60
            p_t = _price_at(rows, bar_s, T)
            p_f = _price_at(rows, bar_s, T + horizon_minutes * 60)
            p_past = _price_at(rows, bar_s, T - step_minutes * 60)
            if p_past is None:
                p_past = opens[d]
            if p_t is None or p_f is None or rows[-1][0] + bar_s < T + horizon_minutes * 60:
                continue   # future price must exist inside the same session
            fut = p_f / p_t - 1.0
            if idx >= warm_days:
                prev = order[max(0, idx - 250):idx]
                prev_close = [closes[x] for x in prev]
                last20 = prev_close[-20:]
                sd = _std(last20)
                mean20 = sum(last20) / len(last20)
                lo, hi = min(prev_close), max(prev_close)
                vols = [dvol[x] for x in prev[-20:] if dvol[x] > 0]
                day_rets = [rows[i][4] / rows[i - 1][4] - 1 for i in range(1, len(rows))
                            if rows[i][0] + bar_s <= T]
                cur_vol = _std(day_rets)
                vol_ratio = math.log(cur_vol / (sum(vols) / len(vols))) if (cur_vol > 0 and vols) else 0.0
                vol_ratio = max(-2.0, min(2.0, vol_ratio))
                past_tod = [r for (dd, r) in tod_hist[m] if dd < d][-60:]
                x = [p_t / p_past - 1.0,
                     p_t / opens[d] - 1.0,
                     opens[d] / closes[prev[-1]] - 1.0,
                     (p_t - mean20) / (sd + 1e-9) if sd > 0 else 0.0,
                     ((p_t - lo) / (hi - lo) - 0.5) if hi > lo else 0.0,
                     vol_ratio,
                     sum(past_tod) / len(past_tod) if past_tod else 0.0]
                x += [_ext_change(ext[k], d) for k in sorted(ext)]
                samples.append({"day": d, "minute": m, "ts": T, "x": x, "names": names,
                                "ret": fut, "persist": p_t / p_past - 1.0})
            todays.append((m, fut))
        for m, fut in todays:       # only AFTER the day is processed: tod prior uses earlier days
            tod_hist[m].append((d, fut))
    return samples
