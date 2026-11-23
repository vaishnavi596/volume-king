"""Read-only evidence-quality review for suspicious repeated cached candles.

A review finding is not proof the broker returned bad OHLCV. Do not promote
the cache to LIVE or synthesize candles. The original bars remain untouched.
"""
from datetime import datetime, timedelta, timezone
from hashlib import sha256
import json
from math import isfinite

IST=timezone(timedelta(hours=5,minutes=30))

def inspect_candle_tail(raw_bars, *, timeframe="1m"):
    if timeframe not in ("1m","3m","5m"):
        raise ValueError("Unsupported candle timeframe")
    if not isinstance(raw_bars,(list,tuple)):
        return {"status":"NO_HISTORY","review":[],"source_error_confirmed":False,
                "provider_requests":0,"orders_sent":0}
    tail=raw_bars[-8:]
    valid=[r for r in tail if isinstance(r,(list,tuple)) and len(r)>=6
           and all(type(v) in (int,float) and isfinite(v) for v in r[:6])]
    review=[]
    # Exact repeated OHLCV across distinct consecutive timestamps suggests a
    # transport/source aggregation pattern needing comparison, not a direction.
    run=1
    best=1
    best_start=0
    best_end=0
    for pos,(prev,now) in enumerate(zip(valid,valid[1:]),start=1):
        if (now[0]>prev[0] and now[0]-prev[0]==int(timeframe[:-1])*60
                and tuple(now[1:6])==tuple(prev[1:6])):
            run+=1
        else:
            run=1
        if run>best:
            best=run
            best_end=pos
            best_start=pos-run+1
    if best>=5:
        review.append({"code":"REPEATED_IDENTICAL_OHLCV_REVIEW",
                       "consecutive_candles":best,
                       "first_ist":datetime.fromtimestamp(valid[best_start][0],IST).strftime("%Y-%m-%d %H:%M IST"),
                       "last_ist":datetime.fromtimestamp(valid[best_end][0],IST).strftime("%Y-%m-%d %H:%M IST"),
                       "cached_ohlcv_sample_sha256":sha256(json.dumps(
                           [list(c[:6]) for c in valid[best_start:best_end+1]],
                           separators=(",",":"),allow_nan=False).encode("utf-8")).hexdigest(),
                       "digest_scope":"PHONE_CACHED_NORMALIZED_ROWS_NOT_RAW_DHAN",
                       "stage":"RAW_DHAN_TO_NORMALIZED_GATEWAY_TO_PHONE_CACHE",
                       "next_action":"COMPARE_RAW_DHAN_WITH_NORMALIZED_GATEWAY_AND_PHONE_VALUES"})
    after=[]
    for candle in valid:
        try:
            at=datetime.fromtimestamp(candle[0],IST)
        except (ValueError,OverflowError,OSError):
            continue
        minute=at.hour*60+at.minute
        if at.weekday()>=5 or not 9*60+15<=minute<15*60+30:
            after.append(at.strftime("%Y-%m-%d %H:%M IST"))
    if after:
        review.append({"code":"OUTSIDE_REGULAR_SESSION_CANDLE_PRESENT",
                       "count":len(after),"last_observed":after[-1],
                       "stage":"CACHED_OHLCV_SESSION_BOUNDARY",
                       "next_action":"EXCLUDE_OUTSIDE_SESSION_FROM_HIST_VOTES;_VERIFY_SOURCE"})
    return {"status":"REVIEW" if review else "NO_REVIEW_FLAGS",
            "review":review,"source_error_confirmed":False,
            "quality_gate":"NEVER_PROMOTE_REVIEW_FLAGS_TO_LIVE_VOTES",
            "provider_requests":0,"orders_sent":0}
