"""Allow display-only use of a completed regular session's candle prefix.

This does not alter original Dhan/cache data, prove exchange provenance,
interpolate missing bars, or make any LIVE signal eligible.
"""
from datetime import datetime,timedelta,timezone
from math import isfinite
IST=timezone(timedelta(hours=5,minutes=30))

def historical_regular_session_bars(rows, timeframe):
    """Remove only an unambiguous final after-close suffix (NSE/BSE cash)."""
    if timeframe not in ("1m","3m","5m") or not isinstance(rows,(list,tuple)) or len(rows)<31:
        return rows
    def valid(r):
        if not isinstance(r,(list,tuple)) or len(r)<6 or any(type(x) not in (int,float) or not isfinite(x) for x in r[:6]):
            return False
        t,o,h,l,c,v=r[:6]
        return t>0 and min(o,h,l,c)>0 and v>=0 and h>=max(o,c) and l<=min(o,c)
    if not valid(rows[-1]):
        return rows
    last=datetime.fromtimestamp(rows[-1][0],IST)
    if not ((15,30)<=(last.hour,last.minute)<(18,0)):
        return rows
    i=len(rows)
    while i and valid(rows[i-1]):
        dt=datetime.fromtimestamp(rows[i-1][0],IST)
        if dt.date()!=last.date() or not ((15,30)<=(dt.hour,dt.minute)<(18,0)):
            break
        i-=1
    if i<30 or i==len(rows) or not valid(rows[i-1]):
        return rows
    end=datetime.fromtimestamp(rows[i-1][0],IST)
    if end.date()!=last.date() or not ((9,15)<=(end.hour,end.minute)<(15,30)):
        return rows
    if rows[i][0]<=rows[i-1][0]:
        return rows
    return list(rows[:i])
