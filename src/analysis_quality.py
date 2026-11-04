"""Deterministic input validation; never a probability or trained AI model."""
import math
from datetime import datetime,timezone

def quality_check(bars,seconds,now=None):
    now=datetime.now(timezone.utc).timestamp() if now is None else now
    clean=[];reasons=[];previous=None
    for row in bars:
        try:
            if len(row)<6:raise ValueError()
            ts,o,h,l,c=map(float,row[:5])
            volume=0.0 if row[5] is None else float(row[5])
            if not all(math.isfinite(v) for v in (ts,o,h,l,c,volume)):raise ValueError()
            if min(ts,o,h,l,c)<=0 or volume<0 or l>min(o,c) or h<max(o,c) or l>h:raise ValueError()
            if previous is not None and ts<=previous:
                reasons.append("Duplicate or unordered candle timestamps")
            previous=ts
            if ts>now:reasons.append("Future candle timestamp")
            # Intraday candle timestamps denote the start of the bar.
            if seconds<86400 and ts+seconds>now:continue
            if seconds>=86400:
                # A daily bar dated today may still be forming; keep historical days only.
                from datetime import timedelta
                ist=timezone(timedelta(hours=5,minutes=30))
                if datetime.fromtimestamp(ts,ist).date()>=datetime.fromtimestamp(now,ist).date():continue
            clean.append([ts,o,h,l,c,volume])
        except (ValueError,TypeError,OverflowError):
            reasons.append("Invalid OHLC or volume values")
    if len(clean)<30:reasons.append("Need 30 completed valid candles")
    if clean and now-clean[-1][0]>max(1800,seconds*2):reasons.append("Completed candles are stale")
    return {"usable":not reasons,"bars":clean,"reasons":list(dict.fromkeys(reasons)),
            "completed_count":len(clean),"excluded_count":len(bars)-len(clean),
            "method":"Input quality checks, not AI accuracy or success probability"}

def agreement_detail(result):
    votes=result.get("votes",[])
    available=[v for v in votes if v.get("vote") is not None]
    directional=[v for v in available if v.get("vote") in (-1,1)]
    # Multiple indicators share price inputs; their agreement is not independent evidence.
    return {"available_filters":len(available),"unavailable_filters":max(len(votes),result.get("requested_filters",len(votes)))-len(available),
            "directional_filters":len(directional),
            "bullish_filters":sum(v.get("vote")==1 for v in votes),
            "bearish_filters":sum(v.get("vote")==-1 for v in votes),
            "neutral_filters":sum(v.get("vote")==0 for v in available),
            "requested_filters":result.get("requested_filters",len(votes)),
            "coverage_ok":result.get("coverage_ok",False),
            "directional_agreement":round(100*max(sum(v.get("vote")==1 for v in votes),sum(v.get("vote")==-1 for v in votes))/len(directional),1) if directional else 0,
            "limitation":"Indicators share price inputs; agreement is not a win probability."}
