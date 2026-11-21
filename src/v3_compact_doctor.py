"""V3 concise error-first diagnostics with complete selected-filter inventory.

Read-only; no data fetch, no synthetic votes. Distinguish absent evidence from
technical cached analysis; successful modules are omitted from the issue list.
"""
from scanner_engine import ALL_FILTERS, OPTION_FILTERS

def compact_doctor(stock_states, selected_filters, filter_rows, *,
                   scanner_symbol, scanner_timeframe, provider_connected,
                   quote_status=None, candle_status=None):
    active=list(dict.fromkeys(x for x in selected_filters if x in ALL_FILTERS))
    by_name={x.get("name"):x for x in filter_rows if isinstance(x,dict)}
    failures=[]
    good=0
    for state in stock_states:
        if state.get("state")=="ERROR":
            failures.append({"area":"stock","symbol":state.get("symbol"),
                             "codes":state.get("error_codes",[])})
        else:
            good+=1
    filters=[]
    for name in active:
        row=by_name.get(name) or {}
        vote=row.get("vote")
        context=(name in OPTION_FILTERS or name=="News Headlines")
        if not provider_connected:
            status,code="WAIT","DHAN_SESSION_REQUIRED"
        elif context:
            status,code="WAIT",("UNVERIFIED_OPTION_EVIDENCE" if name in OPTION_FILTERS
                                else "NEWS_DIRECTION_NOT_VERIFIED")
        elif vote in (-1,0,1) and type(vote) is int:
            status,code="CACHED_UNVERIFIED","NO_LIVE_TIMESTAMP_PROOF"
        else:
            status,code="WAIT","TECHNICAL_CANDLES_OR_FILTER_EVIDENCE_MISSING"
        filters.append({"name":name,"status":status,"code":code,
                        "timeframe":scanner_timeframe,
                        "directional_live_verified":False})
        if status=="WAIT":
            failures.append({"area":"filter","name":name,"code":code})
    if quote_status in ("ERROR","UNAVAILABLE"):
        failures.append({"area":"quote","symbol":scanner_symbol,"code":quote_status})
    if candle_status in ("ERROR","UNAVAILABLE"):
        failures.append({"area":"candle","symbol":scanner_symbol,"code":candle_status})
    return {"mode":"ERRORS_ONLY","scanner_symbol":scanner_symbol,
            "scanner_timeframe":scanner_timeframe,
            "selected_filter_count":len(active),
            "filter_results":filters,"issue_count":len(failures),
            "issues":failures,"healthy_stock_count_hidden":good,
            "diagnostic_scope":"cached data only; no verified live directional votes",
            "orders_sent":0}
