"""Conservative current-session Dhan candle qualification; no extra requests."""
from datetime import datetime, timezone
from math import isfinite
from v3_equity_session_calendar import IST, regular_equity_hours

def completed_live_history(response, bars, quote, *, symbol, timeframe, now):
    if timeframe not in ("1m","3m","5m") or not isinstance(response,dict) or not isinstance(quote,dict):
        return None
    if type(now) not in (int,float) or not isfinite(now):
        return None
    try:
        clock=datetime.fromtimestamp(now,timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    if not regular_equity_hours(clock):
        return None
    width={"1m":60,"3m":180,"5m":300}[timeframe]
    if (response.get("source")!="dhan" or response.get("symbol")!=symbol
            or response.get("interval")!=("1m" if timeframe=="3m" else timeframe)
            or response.get("normalized_transport_integrity")!="SHA256_MATCH"
            or response.get("candle_origin")!="DHAN_INTRADAY_TIMESTAMP"
            or quote.get("source")!="Dhan" or quote.get("cached")
            or quote.get("symbol") not in (None,symbol)
            or quote.get("timestamp_origin")!="DHAN_QUOTE_LAST_TRADE_TIME"):
        return None
    stamp=quote.get("quote_timestamp")
    if type(stamp) not in (int,float) or not isfinite(stamp) or not 0<=now-stamp<=90:
        return None
    local=clock.astimezone(IST)
    opening=local.replace(hour=9,minute=15,second=0,microsecond=0).timestamp()
    if not isinstance(bars,(tuple,list)):
        return None
    completed=[]
    previous=None
    for row in bars:
        if not isinstance(row,(tuple,list)) or len(row)<6:
            return None
        t=row[0]
        if type(t) not in (int,float) or not isfinite(t) or (previous is not None and t<=previous):
            return None
        o,h,l,c,v=row[1:6]
        if (any(type(x) not in (int,float) or not isfinite(x) for x in (o,h,l,c,v))
                or min(o,h,l,c)<=0 or v<0 or h<max(o,l,c) or l>min(o,h,c)):
            return None
        previous=t
        if t+width<=now:
            completed.append(row)
    if len(completed)<3:
        return None
    latest=completed[-1][0]
    if (completed[-3][0]<opening or (latest-opening)%width!=0
            or not 0<=now-latest-width<=width+30
            or stamp<latest+width
            or any(completed[-i][0]-completed[-i-1][0]!=width for i in (1,2))):
        return None
    return completed
