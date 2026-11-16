"""Build exact, completed 3-minute candles from Dhan one-minute history.

Pure offline helper. No network calls, no source fallback, no exchange-live claim.
Input candles are [epoch_seconds, open, high, low, close, volume] in UTC epoch;
timestamps denote the *start* of each one-minute candle. Return only groups
containing all 3 consecutive, valid minute starts aligned to 09:15 IST.
"""
from datetime import datetime, timedelta, timezone
from math import isfinite

IST = timezone(timedelta(hours=5, minutes=30))


def completed_three_minute_bars(minute_bars, *, now_epoch):
    if not isinstance(minute_bars, (tuple, list)):
        return []
    if type(now_epoch) not in (int, float) or not isfinite(now_epoch):
        return []
    grouped = {}
    duplicate_buckets = set()
    for row in minute_bars:
        if not isinstance(row, (tuple, list)) or len(row) < 6:
            continue
        ts, op, hi, lo, cl, vol = row[:6]
        if (type(ts) not in (int, float) or not isfinite(ts)
                or int(ts) != ts or int(ts) % 60 != 0):
            continue
        vals = (op, hi, lo, cl, vol)
        if any(type(v) not in (int, float) or not isfinite(v) for v in vals):
            continue
        if min(op, hi, lo, cl) <= 0 or vol < 0 or not lo <= min(op, cl) <= max(op, cl) <= hi:
            continue
        local = datetime.fromtimestamp(ts, IST)
        if local.second != 0 or local.microsecond != 0:
            continue
        session_start = local.replace(hour=9, minute=15, second=0, microsecond=0).timestamp()
        minutes = int((ts - session_start) // 60)
        # A market session's 09:15 is the 3m anchor; do not combine
        # pre-open/out-of-session bars or cross trading dates.
        if minutes < 0 or minutes >= 375:
            continue
        bucket = int(session_start + (minutes // 3) * 180)
        if bucket + 180 > now_epoch:
            continue  # Never display the still-forming 3-minute candle.
        minute = int(ts)
        candles = grouped.setdefault(bucket, {})
        # Duplicate source minutes make ordering/volume ambiguous. Reject the
        # entire 3m group rather than silently keeping the last duplicate.
        if minute in candles:
            duplicate_buckets.add(bucket)
            continue
        candles[minute] = (float(op), float(hi), float(lo), float(cl), float(vol))
    out = []
    for start, candles in sorted(grouped.items()):
        if start in duplicate_buckets:
            continue
        required = (start, start + 60, start + 120)
        if any(t not in candles for t in required):
            continue
        a, b, c = (candles[t] for t in required)
        out.append((start, a[0], max(a[1], b[1], c[1]),
                    min(a[2], b[2], c[2]), c[3], a[4] + b[4] + c[4]))
    return out
