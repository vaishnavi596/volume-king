"""Read-only historical close label. Never promotes OHLC into Dhan LTP."""
from datetime import datetime, timezone, timedelta
from math import isfinite

IST=timezone(timedelta(hours=5,minutes=30))

def historical_close_display(history, *, now, frame="3m"):
    """Return (price label, status) for a completed exact-frame (1m/3m/5m) Dhan candle, else None."""
    if not isinstance(history,dict) or history.get("source")!="Dhan" or history.get("_scanner_timeframe")!=frame or frame not in ("1m","3m","5m"):
        return None
    bars=history.get("bars")
    if not isinstance(bars,(tuple,list)) or not bars or type(now) not in (int,float) or not isfinite(now):
        return None
    latest=None
    for bar in bars:
        if not isinstance(bar,(tuple,list)) or len(bar)<6:
            continue
        stamp,opening,high,low,closing,volume=bar[:6]
        values=(stamp,opening,high,low,closing,volume)
        if any(type(v) not in (int,float) or not isfinite(v) for v in values):
            continue
        if stamp<=0 or stamp+{"1m":60,"3m":180,"5m":300}[frame]>now or min(opening,high,low,closing)<=0 or volume<0:
            continue
        if high<max(opening,closing,low) or low>min(opening,closing,high):
            continue
        if latest is None or stamp>latest[0]:
            latest=(stamp,closing)
    if latest is None:
        return None
    stamp,closing=latest
    try:
        clock=datetime.fromtimestamp(stamp,IST).strftime("%d %b %H:%M IST")
    except (ValueError,OverflowError,OSError):
        return None
    return (f"HIST {closing:,.2f}",f"HIST CLOSE • {clock} • NOT LIVE • source unverified")
