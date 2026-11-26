"""Allow display-only use of a completed regular session's candle prefix.

This does not alter original Dhan/cache data, prove exchange provenance,
interpolate missing bars, or make any LIVE signal eligible.
"""
from datetime import datetime,timedelta,timezone
from math import isfinite
IST=timezone(timedelta(hours=5,minutes=30))

def _strip_after_close_suffix(rows, timeframe):
    """Remove a validated final after-close cash-session suffix without mutating input.

    The normalized gateway may append a post-close reference bar after 18:00.
    Such a bar must not invalidate valid completed 1m historical analysis.
    """
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
    if not ((15,30)<=(last.hour,last.minute)<(24,0)):
        return rows
    i=len(rows)
    while i and valid(rows[i-1]):
        dt=datetime.fromtimestamp(rows[i-1][0],IST)
        if dt.date()!=last.date() or not ((15,30)<=(dt.hour,dt.minute)<(24,0)):
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


def _stale(r, prev):
    """Flat bar repeating the previous bar's volume: a frozen feed, not a trade print."""
    return (r[1]==r[2]==r[3]==r[4] and r[5]>0 and r[5]==prev[5])

def drop_stale_flat_tail(rows, timeframe):
    """Cut a frozen-feed run (>=2 flat, same-volume bars) near the end of the session.

    Measured on 1y NIFTY 5m: on ~1/3 of days the last 15:15/15:20 bars are frozen and the
    final bar jumps to the close; on 26 Nov the 1m tail had 6 frozen bars. Analysing them
    gives RSI 0 / doji-dominated votes. The series is cut BEFORE the frozen run (and the
    closing print after it), so spacing stays contiguous. Never cuts below 30 bars."""
    if timeframe not in ("1m","3m","5m") or not isinstance(rows,(list,tuple)) or len(rows)<32:
        return rows
    try:
        n=len(rows)
        flags=[k>=1 and _stale(rows[k],rows[k-1]) for k in range(n)]
        end=next((k for k in range(n-1,n-4,-1) if flags[k]),None)   # run may end 0-2 bars before the last
        if end is None:
            return rows
        start=end
        while start-1>=1 and flags[start-1]:
            start-=1
        if end-start+1>=2 and start>=30:
            return list(rows[:start])
    except (TypeError,IndexError):
        return rows
    return rows

def historical_regular_session_bars(rows, timeframe):
    """After-close suffix removal, then frozen-feed tail removal (HIST analysis only)."""
    return drop_stale_flat_tail(_strip_after_close_suffix(rows,timeframe),timeframe)
