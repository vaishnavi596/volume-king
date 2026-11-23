"""Read-only three-stage filter→independent-engine→combined-vote trace.

Uses already computed Doctor rows and already published exact-frame snapshot.
Never fetches data, recomputes directional market signals or authorizes trades.
"""
from scanner_engine import OPTION_FILTERS
from v3_vote_conflict_doctor import conflict_doctor
from five_engine import ENGINE_NAMES, combine_evidence, EngineEvidence


def audit_vote_trace(*, symbol, timeframe, generation, filter_rows,
                     box_rows, snapshot=None, market_open=False):
    if not isinstance(symbol,str) or not symbol or timeframe not in ("1m","3m","5m") or type(generation) is not int:
        raise ValueError("Exact symbol/timeframe/provider generation required")
    if not isinstance(filter_rows,(list,tuple)) or not isinstance(box_rows,(list,tuple)):
        raise ValueError("Existing Doctor rows required")

    # Counts are from actual calculated rows; no second technical analysis.
    names=set()
    calculated=directional=neutral=context=waiting=error=0
    blocked_filters=[]
    for row in filter_rows:
        if not isinstance(row,dict):
            raise ValueError("Malformed filter Doctor row")
        name=row.get("filter",row.get("name"))
        if not isinstance(name,str) or name in names:
            raise ValueError("Duplicate or malformed filter")
        names.add(name)
        vote=row.get("vote")
        status=row.get("status",row.get("state","WAIT"))
        computed=(type(vote) is int and vote in (-1,0,1))
        if computed and name not in OPTION_FILTERS:
            calculated+=1
            directional+=vote!=0
            neutral+=vote==0
        elif name in OPTION_FILTERS or status in ("CONTEXT_ONLY","ADAPTER_NOT_DIRECTIONAL"):
            context+=1
            blocked_filters.append({"name":name,"stage":"OPTION_CONTEXT_NOT_INDEPENDENT_VOTE"})
        elif status=="ERROR":
            error+=1
            blocked_filters.append({"name":name,"stage":str(row.get("stage","ERROR"))[:100]})
        else:
            waiting+=1
            blocked_filters.append({"name":name,"stage":str(row.get("stage","CALCULATION_NOT_READY"))[:100]})
    observed={}
    for row in box_rows:
        if not isinstance(row,dict):
            raise ValueError("Invalid box Doctor row")
        name=row.get("engine")
        if name not in ENGINE_NAMES or name in observed:
            raise ValueError("Duplicate/unknown engine")
        observed[name]=row
    if set(observed)!=set(ENGINE_NAMES):
        raise ValueError("Five engine rows are required")

    published=False
    source_snapshot_valid=False
    combined={"state":"WAIT","coverage":0,"bullish":None,"bearish":None,
              "reason":"No exact-frame verified combined snapshot"}
    if snapshot is not None:
        if not isinstance(snapshot,dict):
            raise ValueError("Invalid snapshot")
        engines=snapshot.get("engines")
        if (isinstance(engines,(list,tuple)) and len(engines)==5 and
                all(isinstance(e,EngineEvidence) for e in engines) and
                tuple(e.name for e in engines)==ENGINE_NAMES):
            published=True
            # Only report the existing independent vote contract; do not
            # treat 13 correlated technical filters as 13 engine votes.
            actual=combine_evidence(engines)
            source_snapshot_valid=True
            if market_open:
                combined={k:actual.get(k) for k in ("state","coverage","bullish","bearish","reason")}
            else:
                combined["reason"]="MARKET_CLOSED_NO_VERIFIED_LIVE_VOTE"
        else:
            raise ValueError("Malformed snapshot evidence")
    boxes=[]
    for name in ENGINE_NAMES:
        row=observed[name]
        num=row.get("bullish_percent")
        opposite=row.get("bearish_percent")
        eligible=(market_open and published and source_snapshot_valid and
                  type(num) is int and type(opposite) is int and
                  num+opposite==100 and row.get("raw_verified") is True and
                  row.get("raw_source")=="Dhan" and
                  row.get("status") in ("BULLISH","BEARISH","NEUTRAL"))
        boxes.append({"engine":name,"calculation_state":(
            "HIST_ONLY" if row.get("historical_percent") is not None else
            "DIRECTIONAL_EVIDENCE_PRESENT" if num is not None else
            "WAIT_UNVERIFIED"),
            "vote_state":"ELIGIBLE" if eligible else "BLOCKED",
            "blocker":None if eligible else str(
                row.get("blocker",row.get("reason","VERIFIED_VOTE_UNAVAILABLE")))[:120]})
    # A cached snapshot's own combined contract may be eligible while a
    # limited Master display row has no source proof. Never claim an eligible
    # final output based on such incomplete inspection.
    eligible_count=sum(x["vote_state"]=="ELIGIBLE" for x in boxes)
    if eligible_count<3 and combined.get("state")!="WAIT":
        combined={"state":"WAIT","coverage":eligible_count,"bullish":None,
                  "bearish":None,"reason":"DISPLAY_SIDE_PROVENANCE_NOT_VERIFIED"}
    return {
        "mode":"READ_ONLY_EXISTING_CALCULATIONS",
        "identity":{"symbol":symbol,"timeframe":timeframe,"generation":generation},
        "filter_calculation":{"selected":len(names),"calculated":calculated,
                              "directional":directional,"neutral":neutral,
                              "context_only":context,"waiting":waiting,"errors":error,
                              "blocked_details":blocked_filters},
        "box_vote_gate":{"eligible":eligible_count,"required":3,"boxes":boxes,
                         "sixth_M":"STANDBY_NOT_SCORED"},
        "voting_conflict_audit":conflict_doctor(snapshot,market_open=market_open),
        "combined_vote":{"state":combined.get("state","WAIT"),
                         "coverage":combined.get("coverage",0),
                         "bullish":combined.get("bullish"),
                         "bearish":combined.get("bearish"),
                         "reason":combined.get("reason","NOT_VERIFIED"),
                         "historical_filter_agreement_is_separate":True},
        "final_screen_path":{"status":"UI_PIXEL_MATCH_NOT_MEASURED",
                             "intended_surfaces":["Dashboard","Watchlist","Scanner","Super Five"],
                             "shared_presenter_wiring":"REQUIRES_SEPARATE_RUNTIME_VERIFICATION"},
        "provider_requests":0,"orders_sent":0
    }
