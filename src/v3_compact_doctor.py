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
            symbol=state.get("symbol")
            failures.append({"area":"stock","symbol":symbol,
                             "codes":state.get("error_codes",[]),
                             "start":"Dhan API",
                             "endpoint":"Oracle Clone Gateway → Dhan quote/history → app cache",
                             "blocked_at":"required Dhan price or selected candle cache",
                             "next_action":"Check current session quote and 1m/3m history stage"})
        else:
            good+=1
    filters=[]
    healthy_filter_count=0
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
        if status=="WAIT":
            filters.append({"name":name,"status":status,"code":code,
                            "timeframe":scanner_timeframe,
                            "directional_live_verified":False})
            failures.append({"area":"filter","name":name,"code":code,
                             "start":"Dhan candle/option data",
                             "endpoint":"Oracle Gateway → per-symbol cache → Scanner filter vote",
                             "blocked_at":"verified directional evidence" if context
                                          else "selected timeframe technical candle analysis",
                             "next_action":"Inspect exact underlying/expiry and evidence provenance" if context
                                           else "Check completed candle count and timeframe"})
        else:
            # Technical HIST is already available. Do not repeat all 13
            # healthy rows as alleged errors in ERRORS_ONLY mode.
            healthy_filter_count+=1
    if quote_status in ("ERROR","UNAVAILABLE"):
        failures.append({"area":"quote","symbol":scanner_symbol,"code":quote_status,
                         "start":"Dhan quote endpoint","endpoint":"Gateway index/equity LTP → phone Price",
                         "blocked_at":"valid source-checked quote in current session",
                         "next_action":"Run focused source/segment/security-id quote probe"})
    if candle_status in ("ERROR","UNAVAILABLE"):
        failures.append({"area":"candle","symbol":scanner_symbol,"code":candle_status,
                         "start":"Dhan intraday candle endpoint",
                         "endpoint":"Oracle historical adapter → timeframe cache → Scanner",
                         "blocked_at":"completed selected-timeframe OHLC",
                         "next_action":"Check data range, source, validity and upstream error category"})
    return {"mode":"ERRORS_ONLY","scanner_symbol":scanner_symbol,
            "scanner_timeframe":scanner_timeframe,
            "selected_filter_count":len(active),
            "filter_results":filters,"healthy_filter_count_hidden":healthy_filter_count,
            "issue_count":len(failures),
            "issues":failures,"healthy_stock_count_hidden":good,
            "diagnostic_scope":"cached data only; no verified live directional votes",
            "orders_sent":0}
