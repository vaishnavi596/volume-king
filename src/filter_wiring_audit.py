"""Read-only per-filter capability trace; never creates a trading vote.

The candle engine handles all listed technical filters. Option-chain context,
news headlines and futures contracts are distinct evidence sources, and none
is automatically a directional vote merely because the market is open.
"""
from scanner_engine import ALL_FILTERS, OPTION_FILTERS

CANDLE_FILTERS=frozenset(ALL_FILTERS)-frozenset(OPTION_FILTERS)-{"News Headlines"}


def filter_wiring_matrix(selected, rows, *, source="Dhan", timeframe="1m",
                         candle_ready=False, options_context=False,
                         news_context=False, modes=None):
    """Explain what actually ran for a symbol with no network/side effects."""
    modes=modes or {}
    if not isinstance(selected,(list,tuple)):
        return []
    by_name={row.get("name"):row for row in rows
             if isinstance(row,dict) and row.get("name") in ALL_FILTERS}
    result=[]
    for name in dict.fromkeys(selected):
        if name not in ALL_FILTERS:
            result.append({"name":str(name),"state":"UNKNOWN_FILTER","vote":None})
            continue
        row=by_name.get(name,{})
        vote=row.get("vote")
        if modes.get(name)=="Chart":
            state="CHART_ONLY"
        elif source!="Dhan":
            state="SOURCE_MISMATCH"
        elif name in OPTION_FILTERS:
            state="ADAPTER_NOT_DIRECTIONAL" if options_context else "OPTION_DATA_MISSING"
        elif name=="News Headlines":
            state="ADAPTER_NOT_DIRECTIONAL" if news_context else "NEWS_DATA_MISSING"
        elif not candle_ready:
            state="CANDLE_DATA_MISSING_OR_INVALID"
        elif type(vote) is int and vote in (-1,0,1):
            state="CALCULATED"
        else:
            state="CANDLE_INPUT_UNAVAILABLE"
        result.append({"name":name,"state":state,
                       "vote":vote if state=="CALCULATED" else None,
                       "timeframe":timeframe,
                       "role":"technical" if name in CANDLE_FILTERS else
                              "options" if name in OPTION_FILTERS else "news"})
    return result


def diagnostic_candle_readiness(history, timeframe, *, now):
    """Read-only source/timeframe/closed-bar proof for the 18-filter Doctor.

    This is only an eligibility preflight. The scanner engine separately
    validates OHLCV ordering, spacing and the 30-bar technical calculation.
    The phone's receipt time never proves a Dhan exchange-live candle.
    """
    from math import isfinite
    if not isinstance(history,dict) or history.get("source")!="Dhan":
        return "SOURCE_MISSING_OR_MISMATCH"
    seconds={"1m":60,"2m":120,"3m":180,"5m":300,"10m":600,
             "15m":900,"30m":1800,"1h":3600}.get(timeframe)
    if seconds is None or history.get("_scanner_timeframe","5m")!=timeframe:
        return "TIMEFRAME_MISMATCH"
    bars=history.get("bars")
    if not isinstance(bars,(list,tuple)) or len(bars)<30:
        return "CANDLE_DATA_MISSING_OR_INSUFFICIENT"
    if type(now) not in (int,float) or not isfinite(now) or now<=0:
        return "INVALID_OBSERVATION_TIME"
    last=bars[-1]
    if not isinstance(last,(list,tuple)) or len(last)<6 or type(last[0]) not in (int,float) or not isfinite(last[0]):
        return "CANDLE_INVALID_TIMESTAMP"
    if last[0]+seconds>now:
        return "LATEST_CANDLE_NOT_COMPLETED"
    return "READY_FOR_QUALITY_AND_CALCULATION"
