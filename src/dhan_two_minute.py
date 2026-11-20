"""Derive verified completed 2m candles from consecutive Dhan 1m candles.

Anchor each group to the regular 09:15 IST session; no cross-session groups,
partial candle, duplicate minute, invalid OHLCV, or fabricated source ticks.
"""
from datetime import datetime, timedelta, timezone
from math import isfinite

IST = timezone(timedelta(hours=5, minutes=30))


def completed_two_minute_bars(minute_bars, *, now_epoch):
    if not isinstance(minute_bars, (list, tuple)):
        return []
    if type(now_epoch) not in (int, float) or not isfinite(now_epoch):
        return []
    groups = {}
    duplicates = set()
    for row in minute_bars:
        if not isinstance(row, (tuple, list)) or len(row) < 6:
            continue
        ts, op, hi, lo, cl, vol = row[:6]
        if (type(ts) not in (int, float) or not isfinite(ts)
                or int(ts) != ts or int(ts) % 60):
            continue
        vals = (op, hi, lo, cl, vol)
        if any(type(v) not in (int, float) or not isfinite(v) for v in vals):
            continue
        if min(op, hi, lo, cl) <= 0 or vol < 0 or not lo <= min(op, cl) <= max(op, cl) <= hi:
            continue
        local = datetime.fromtimestamp(ts, IST)
        session_start = local.replace(hour=9, minute=15, second=0, microsecond=0).timestamp()
        minutes = int((ts - session_start) // 60)
        if not 0 <= minutes < 375:
            continue
        bucket = int(session_start + (minutes // 2) * 120)
        if bucket + 120 > now_epoch or bucket + 120 > session_start + 375 * 60:
            continue
        candles = groups.setdefault(bucket, {})
        minute = int(ts)
        if minute in candles:
            duplicates.add(bucket)
            continue
        candles[minute] = tuple(float(x) for x in vals)
    result = []
    for start, candles in sorted(groups.items()):
        if start in duplicates or start not in candles or start + 60 not in candles:
            continue
        a, b = candles[start], candles[start + 60]
        result.append((start, a[0], max(a[1], b[1]), min(a[2], b[2]),
                       b[3], a[4] + b[4]))
    return result
