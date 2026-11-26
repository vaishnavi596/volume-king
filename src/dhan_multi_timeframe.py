"""Session-aligned, completed Dhan candle aggregation for 10m and 30m.

Sources: 10m from consecutive 5m, 30m from consecutive 15m.
No network or fabricated ticks, no cross-session/partial/duplicate grouping.
"""
from datetime import datetime, timedelta, timezone
from math import isfinite

IST=timezone(timedelta(hours=5,minutes=30))
PAIRS={"5m":("1m",1,5),"10m":("5m",5,2),"30m":("15m",15,2)}

def completed_derived_bars(rows, target, *, now_epoch):
    if target not in PAIRS:
        raise ValueError("Unsupported derived timeframe")
    if not isinstance(rows,(tuple,list)) or type(now_epoch) not in (int,float) or not isfinite(now_epoch):
        return []
    source,source_mins,parts=PAIRS[target]
    slot=source_mins*60
    width=slot*parts
    buckets={}
    duplicate=set()
    for row in rows:
        if not isinstance(row,(tuple,list)) or len(row)<6:
            continue
        stamp,op,hi,lo,cl,vol=row[:6]
        vals=(stamp,op,hi,lo,cl,vol)
        if any(type(v) not in (int,float) or not isfinite(v) for v in vals):
            continue
        if int(stamp)!=stamp or stamp%60!=0 or min(op,hi,lo,cl)<=0 or vol<0 or not lo<=min(op,cl)<=max(op,cl)<=hi:
            continue
        try:
            local=datetime.fromtimestamp(stamp,IST)
        except (ValueError,OverflowError,OSError):
            continue
        session=local.replace(hour=9,minute=15,second=0,microsecond=0).timestamp()
        delta=int(stamp-session)
        if delta<0 or delta>=375*60 or delta%slot!=0:
            continue
        bucket=int(session+(delta//width)*width)
        if bucket+width>min(now_epoch,session+375*60):
            continue
        members=buckets.setdefault(bucket,{})
        if stamp in members:
            duplicate.add(bucket)
        members[int(stamp)]=(float(op),float(hi),float(lo),float(cl),float(vol))
    result=[]
    for start,members in sorted(buckets.items()):
        if start in duplicate:
            continue
        indices=[start+i*slot for i in range(parts)]
        if any(k not in members for k in indices):
            continue
        values=[members[k] for k in indices]
        if not isfinite(sum(v[4] for v in values)):
            continue
        result.append((start,values[0][0],max(v[1] for v in values),
                       min(v[2] for v in values),values[-1][3],sum(v[4] for v in values)))
    return result
