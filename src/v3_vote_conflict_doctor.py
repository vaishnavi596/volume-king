"""Pure voting-disagreement Doctor: distinguish valid minority votes from bugs.

Reads exact five-engine evidence and published combined result. Never makes
market requests, fabricates market directions, trains weights or sends orders.
"""
from five_engine import ENGINE_NAMES, EngineEvidence, combine_evidence


def conflict_doctor(snapshot, *, market_open):
    if type(market_open) is not bool:
        raise ValueError("Market session flag required")
    status={"status":"NO_SNAPSHOT","normal_disagreement":False,
            "bullish_boxes":0,"bearish_boxes":0,"neutral_boxes":0,
            "eligible_boxes":0,"minority_kept":True,"issues":[],
            "provenance_overlap":"UNMEASURED_ENGINE_SOURCE_IDS",
            "sixth_M":"STANDBY_NOT_SCORED","provider_requests":0,"orders_sent":0}
    if snapshot is None:
        return status
    if not isinstance(snapshot,dict):
        return dict(status,status="INVALID_SNAPSHOT",issues=[{"code":"INVALID_SNAPSHOT_TYPE"}])
    engines=snapshot.get("engines")
    if (not isinstance(engines,(list,tuple)) or len(engines)!=5 or
            any(not isinstance(e,EngineEvidence) for e in engines) or
            tuple(e.name for e in engines)!=ENGINE_NAMES):
        return dict(status,status="INVALID_SNAPSHOT",
                    issues=[{"code":"ENGINE_ORDER_OR_COUNT_INVALID"}])
    # Comparison must use the actual policy, never a second vote algorithm.
    expected=combine_evidence(engines)
    existing=snapshot.get("combined")
    issues=[]
    if existing is not None:
        if not isinstance(existing,dict) or any(
                existing.get(k)!=expected.get(k)
                for k in ("state","coverage","bullish","bearish")):
            issues.append({"code":"COMBINED_VOTE_PUBLISH_MISMATCH",
                           "blocked_at":"AGGREGATOR_TO_SNAPSHOT",
                           "next_action":"REBUILD_RESULT_FROM_CANONICAL_FIVE_ENGINE_EVIDENCE"})
    active=[e for e in engines if e.eligible and e.source.strip().casefold()=="dhan"]
    bulls=sum(e.bullish>e.bearish for e in active)
    bears=sum(e.bearish>e.bullish for e in active)
    neutral=len(active)-bulls-bears
    disagreement=bulls>0 and bears>0
    if not market_open:
        state="MARKET_CLOSED_NO_LIVE_VOTE"
    elif expected["coverage"]<3:
        state="WAIT_INSUFFICIENT_VERIFIED_ENGINES"
    elif expected["state"]=="WAIT":
        state=("CONFLICT_NO_CONSENSUS" if disagreement else
               "WAIT_MARGIN_OR_NEUTRAL")
    elif disagreement:
        state="MINORITY_VOTE_RETAINED"
    else:
        state="DIRECTIONAL_CONSENSUS"
    return dict(status,status=state,normal_disagreement=disagreement,
                bullish_boxes=bulls,bearish_boxes=bears,neutral_boxes=neutral,
                eligible_boxes=len(active),issues=issues,
                final_state=expected["state"] if market_open else "WAIT",
                min_engines=expected["required"],
                policy_reason=expected["reason"],
                raw_source_attestation="REQUIRES_SEPARATE_PROVIDER_PROOF",
                provenance_overlap="UNMEASURED_ENGINE_SOURCE_IDS")
