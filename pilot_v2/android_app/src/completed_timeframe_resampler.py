"""Read-only 5m/15m/30m resampling of already validated completed NSE 1m bars.

Require every minute in a session-aligned completed bucket. Never fills gaps,
fetches data, mutates the original cache or labels the result LIVE.
"""
from datetime import datetime, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30))
WIDTHS = {"5m": 5, "15m": 15, "30m": 30}


def complete_session_bars(minute_bars, timeframe, *, now_epoch):
    if timeframe not in WIDTHS or type(now_epoch) not in (int, float):
        return ()
    width = WIDTHS[timeframe]
    buckets = {}
    for bar in minute_bars:
        if type(bar) is not dict or bar.get("completed") is not True:
            continue
        stamp = bar.get("timestamp")
        if type(stamp) is not int or stamp % 60:
            continue
        dt = datetime.fromtimestamp(stamp, IST)
        anchor = dt.replace(hour=9, minute=15, second=0, microsecond=0)
        elapsed = int((dt - anchor).total_seconds() // 60)
        if not 0 <= elapsed < 375:
            continue
        start = int(anchor.timestamp()) + (elapsed // width) * width * 60
        if start + width * 60 > min(now_epoch, anchor.timestamp() + 375 * 60):
            continue
        bucket = buckets.setdefault(start, {})
        bucket[stamp] = None if stamp in bucket else bar
    results = []
    for start, bucket in sorted(buckets.items()):
        required = [start + i * 60 for i in range(width)]
        if any(stamp not in bucket or bucket[stamp] is None for stamp in required):
            continue
        rows = [bucket[t] for t in required]
        results.append({"timestamp": start, "open": rows[0]["open"],
                        "high": max(b["high"] for b in rows),
                        "low": min(b["low"] for b in rows),
                        "close": rows[-1]["close"],
                        "volume": sum(b["volume"] for b in rows),
                        "completed": True})
    return tuple(results)
