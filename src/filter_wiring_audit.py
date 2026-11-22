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
