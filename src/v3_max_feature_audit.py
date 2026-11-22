"""Read-only V3 whole-app feature readiness diagnosis.

No network calls, no broker side effects, no synthetic market data, no
unverified PCR/Max Pain/news/OI promoted to a directional filter vote.
"""
from __future__ import annotations
import math
import time

FILTER_IDS=("oi_support","oi_resistance","max_pain","pcr","candle_trend")

def _number(x,positive=False):
    return type(x) in (int,float) and math.isfinite(x) and (x>0 if positive else x>=0)

def audit_features(*, news_cache, option_metrics, assessment_cache,
                   selected_symbol, selected_expiry, generation,
                   scanner_symbol, scanner_timeframe, active_filters,
                   now=None):
    now=time.time() if now is None else now
    report={"scope":"LOCAL_CACHE_ONLY","provider_requests":0,"live_trading":False,
            "features":{},"issues":[]}
    def emit(name,state,code,details=None):
        item={"state":state,"code":code}
        if details:item.update(details)
        report["features"][name]=item
        if state in ("ERROR","UNAVAILABLE","UNVERIFIED","NOT_CONNECTED"):
            report["issues"].append({"feature":name,"code":code})
    for key in ("GLOBAL",scanner_symbol,selected_symbol):
        snap=news_cache.get(key) if isinstance(news_cache,dict) else None
        items=snap.get("items",[]) if isinstance(snap,dict) else []
        fresh=[a for a in items if isinstance(a,dict) and _number(a.get("published"))
               and 0<=now-a["published"]<=86400 and isinstance(a.get("title"),str)]
        status=str(snap.get("status","CACHE_EMPTY"))[:72] if isinstance(snap,dict) else "CACHE_EMPTY"
        safe_key="global" if key=="GLOBAL" else ("scanner" if key==scanner_symbol else "selected_option")
        if "news_"+safe_key in report["features"]:continue
        if fresh:
            emit("news_"+safe_key,"AVAILABLE_CONTEXT","NEWS_HEADLINES_CONTEXT_ONLY",
                 {"count":len(fresh),"source":str(snap.get("source","RSS"))[:55],
                  "feed_status":status,"directional_vote":False})
        else:
            emit("news_"+safe_key,"UNAVAILABLE",
                 "NEWS_CACHE_EMPTY" if not items else "NEWS_HEADLINES_STALE_OR_INVALID",
                 {"count":0,"feed_status":status,"directional_vote":False})
    emit("news_sentiment_vote","NOT_CONNECTED","NEWS_DIRECTIONAL_ENGINE_UNVERIFIED",
         {"reason":"RSS headline context does not verify trading impact"})
    matching=(isinstance(option_metrics,dict) and
              option_metrics.get("symbol")==selected_symbol and
              option_metrics.get("expiry")==selected_expiry and
              option_metrics.get("source")=="dhan" and
              option_metrics.get("freshness")=="unverified" and
              option_metrics.get("signal_eligible") is False)
    if not matching:
        # A same-symbol/expiry cache may exist but fail provenance requirements.
        # Report that accurately instead of calling the chain entirely missing.
        scoped=(isinstance(option_metrics,dict) and
                option_metrics.get("symbol")==selected_symbol and
                option_metrics.get("expiry")==selected_expiry)
        code="OPTION_CHAIN_PROVENANCE_UNVERIFIED" if scoped else "OPTION_CHAIN_CONTEXT_MISSING"
        for feature in ("pcr","max_pain","oi_support","oi_resistance"):
            emit(feature,"UNVERIFIED" if scoped else "UNAVAILABLE",code,
                 {"symbol":str(selected_symbol)[:30],"expiry":str(selected_expiry)[:16],
                  "directional_vote":False})
    else:
        for feature,field in (("pcr","pcr"),("max_pain","max_pain")):
            value=option_metrics.get(field)
            if _number(value,positive=(field=="max_pain")):
                emit(feature,"UNVERIFIED","DHAN_METRIC_CONTEXT_ONLY",
                     {"value":value,"symbol":str(selected_symbol)[:30],
                      "expiry":str(selected_expiry)[:16],"directional_vote":False})
            else:
                emit(feature,"ERROR","DHAN_METRIC_INVALID_OR_MISSING",{"directional_vote":False})
        for feature in ("oi_support","oi_resistance"):
            emit(feature,"NOT_CONNECTED","OI_DIRECTIONAL_EVIDENCE_NOT_WIRED",
                 {"reason":"OI level or PCR alone cannot prove market direction",
                  "directional_vote":False})
    # The actual app cache key includes expiry; never read another expiry's
    # assessment. The validated provider response lives inside record["data"].
    record=(assessment_cache.get((generation,scanner_symbol,scanner_timeframe,selected_expiry))
            if isinstance(assessment_cache,dict) else None)
    data=record.get("data") if isinstance(record,dict) else None
    valid=(isinstance(record,dict) and
           record.get("timeframe")==scanner_timeframe and
           record.get("expiry")==selected_expiry and
           isinstance(data,dict) and data.get("symbol")==scanner_symbol and
           data.get("source","dhan")=="dhan" and
           data.get("freshness","unverified")=="unverified" and
           data.get("signal_eligible") is False and
           data.get("live_orders_enabled") is False and
           data.get("bullish_score") is None and
           data.get("bearish_score") is None)
    rows=data.get("assessment_filters") if valid else None
    # A partial or duplicate five-filter payload is not evidence. Match the
    # strict UI contract before reporting even informational availability.
    complete=(isinstance(rows,list) and len(rows)==len(FILTER_IDS) and
              all(isinstance(row,dict) and isinstance(row.get("id"),str) and
                  row["id"] in FILTER_IDS and
                  row.get("status") in ("available","unavailable") for row in rows) and
              {row["id"] for row in rows}==set(FILTER_IDS))
    by_id={row["id"]:row for row in rows} if complete else {}
    for key in FILTER_IDS:
        row=by_id.get(key)
        if row and row.get("status")=="available":
            emit("assessment_"+key,"AVAILABLE_CONTEXT","ORACLE_ASSESSMENT_UNVERIFIED",
                 {"timeframe":scanner_timeframe,"directional_vote":False})
        else:
            emit("assessment_"+key,"UNAVAILABLE","ASSESSMENT_EVIDENCE_NOT_AVAILABLE",
                 {"timeframe":scanner_timeframe,"directional_vote":False})
    emit("analysis_filter_settings","CONFIGURED","SELECTED_FILTERS_NOT_ALL_LIVE",
         {"selected_count":len(active_filters),"selected_names":[str(x)[:45] for x in active_filters],
          "scanner_candle_filters_only":True})
    report["issue_count"]=len(report["issues"])
    report["all_features_live_ready"]=False
    report["notice"]="News RSS, option OI/PCR/Max Pain and Oracle assessment WAIT do not prove a live five-filter directional signal."
    return report
