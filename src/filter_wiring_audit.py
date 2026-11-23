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
        elif name in OPTION_FILTERS:
            # OI has its own selected-symbol/expiry Dhan chain. Missing
            # OHLCV candles must not be mislabeled as an option source fault.
            ready=(options_context.get(name,False) if isinstance(options_context,dict)
                   else bool(options_context))
            state="ADAPTER_NOT_DIRECTIONAL" if ready else "OPTION_DATA_MISSING"
        elif name=="News Headlines":
            # Headlines are an independent context source, not candle data.
            state="ADAPTER_NOT_DIRECTIONAL" if news_context else "NEWS_DATA_MISSING"
        elif source!="Dhan":
            state="SOURCE_MISMATCH"
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
    # The current forming bar must not invalidate older *completed* bars.
    # Do not accept malformed or future observations as proof of readiness.
    completed=sum(1 for bar in bars
                  if isinstance(bar,(list,tuple)) and len(bar)>=6
                  and type(bar[0]) in (int,float) and isfinite(bar[0])
                  and 0<bar[0] and bar[0]+seconds<=now)
    if completed>=30:
        return "READY_FOR_QUALITY_AND_CALCULATION"
    if last[0]+seconds>now:
        return "LATEST_CANDLE_NOT_COMPLETED"
    return "CANDLE_DATA_MISSING_OR_INSUFFICIENT"


def doctor_filter_rows(rows, matrix):
    """Keep per-filter Doctor labels consistent with authoritative wiring audit.

    UI rows are derived from the *same* selected symbol/timeframe readiness
    matrix, never guessed by searching for 'unverified' in message text.
    Does not turn cached options or headlines into directional votes.
    """
    states={item.get("name"):item for item in matrix if isinstance(item,dict)}
    out=[]
    for row in rows:
        if not isinstance(row,dict):
            continue
        entry=states.get(row.get("filter"))
        if not entry:
            out.append(dict(row,status="ERROR",stage="UI_ADAPTER"))
            continue
        state=entry["state"]
        vote=entry.get("vote")
        if state=="CALCULATED":
            status="BULLISH" if vote==1 else "BEARISH" if vote==-1 else "NEUTRAL"
            stage="CALCULATED"
        elif state=="CHART_ONLY":
            status,stage="CHART_ONLY","DISPLAY"
        elif state=="ADAPTER_NOT_DIRECTIONAL":
            status,stage="CONTEXT_ONLY","INDEPENDENT_CONTEXT_NO_DIRECTIONAL_VOTE"
        else:
            status,stage="WAIT",state
        out.append(dict(row,status=status,stage=stage))
    return out


def has_recent_news_context(data, *, now, max_age_seconds=86400):
    """Check actual dated RSS headline context, not just a cached item count.

    This never authenticates news direction or generates a trading vote.
    Cached news can stay displayed as HIST even after this readiness expires.
    """
    from math import isfinite
    if (not isinstance(data,dict) or not isinstance(data.get("items"),(list,tuple))
            or type(now) not in (int,float) or not isfinite(now) or now<=0
            or type(max_age_seconds) not in (int,float) or not isfinite(max_age_seconds)
            or max_age_seconds<=0):
        return False
    fetched=data.get("fetched")
    if type(fetched) not in (int,float) or not isfinite(fetched) or not 0<=now-fetched<=max_age_seconds:
        return False
    return any(isinstance(row,dict) and isinstance(row.get("title"),str)
               and bool(row["title"].strip()) and
               type(row.get("published")) in (int,float) and
               isfinite(row["published"]) and 0<=now-row["published"]<=max_age_seconds
               for row in data["items"])


def option_filter_context_readiness(data, *, symbol, now, window_available=False, window_context=None):
    """Per-filter current Dhan expiry context, never independent direction.

    Calendar expiry is checked in IST. Historical/expired contracts can be
    shown as saved context elsewhere but must not be labeled current-ready.
    """
    from datetime import datetime, date, timezone, timedelta
    from math import isfinite
    result={name:False for name in OPTION_FILTERS}
    if (not isinstance(data,dict) or data.get("source")!="dhan"
            or not isinstance(symbol,str) or not symbol
            or data.get("symbol")!=symbol or data.get("freshness")!="unverified"
            or data.get("signal_eligible") is not False
            or type(now) not in (int,float) or not isfinite(now) or now<=0):
        return result
    expiry=data.get("expiry")
    try:
        expiry_day=date.fromisoformat(expiry)
        local_day=datetime.fromtimestamp(now,timezone(timedelta(hours=5,minutes=30))).date()
    except (TypeError,ValueError,OverflowError):
        return result
    if expiry_day<local_day:
        return result
    max_pain=data.get("max_pain")
    result["Dhan Max Pain"]=(type(max_pain) in (int,float)
                             and isfinite(max_pain) and max_pain>0)
    # A bare boolean cannot prove a valid seven-strike CE/PE Dhan chain.
    valid_window=(isinstance(window_context,dict)
                  and window_context.get("available") is True
                  and window_context.get("source")=="Dhan"
                  and window_context.get("freshness")=="unverified"
                  and window_context.get("signal_eligible") is False
                  and window_context.get("direction")=="WAIT"
                  and isinstance(window_context.get("rows"),(list,tuple))
                  and len(window_context["rows"])==7)
    if valid_window:
        for row in window_context["rows"]:
            if not isinstance(row,dict):
                valid_window=False
                break
            for side in ("ce","pe"):
                leg=row.get(side)
                if (not isinstance(leg,dict) or type(leg.get("oi")) not in (int,float)
                        or not isfinite(leg["oi"]) or leg["oi"]<0):
                    valid_window=False
                    break
            if not valid_window:
                break
    if valid_window:
        result["OI Profile"]=True
        result["OI Support"]=True
        result["OI Resistance"]=True
    return result
