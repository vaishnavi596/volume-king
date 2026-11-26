"""Offline HIST voting replay, separate from validated LIVE five-engine votes.

Each of T/C/N/F/O has a slot. Real historical Dhan evidence may populate T
and independent candle-body C. Absent news impact, futures trade-flow and
options directional flow abstain. No artificial votes or provider requests.
"""
from math import isfinite
from datetime import date, datetime, timezone, timedelta
from five_engine import ENGINE_NAMES, historical_candle_balance, combine_evidence, EngineEvidence
from historical_session_window import historical_regular_session_bars
from filter_wiring_audit import CANDLE_FILTERS
from scanner_engine import analyze

OPTION_CONTEXT={"OI Support","OI Resistance","OI Profile","Dhan Max Pain"}
TIMEFRAMES={"1m":60,"3m":180,"5m":300}

# HIST evidence accepts only independently authenticated measured direction, not
# headlines count, OI, PCR, option-chain context or futures price alone.
HIST_BASES={"news":"verified_symbol_news_impact",
            "futures":"validated_futures_trade_flow",
            "options":"validated_option_trade_flow"}
HIST_BLOCKERS={"candle":"INSUFFICIENT_VALID_COMPLETED_DIRECTIONAL_CANDLES",
               "news":"VERIFIED_HISTORICAL_NEWS_IMPACT_MISSING",
               "futures":"VERIFIED_HISTORICAL_FUTURES_FLOW_MISSING",
               "options":"VERIFIED_EXPIRY_SCOPED_OPTION_FLOW_MISSING"}

def _historical_measured(name, component, *, symbol, timeframe, generation, last_bar):
    """Only explicit attested HIST directional samples; never imply LIVE proof."""
    if not isinstance(component,dict):
        return None
    if (component.get("verified") is not True or component.get("source")!="Dhan"
            or component.get("historical") is not True
            or component.get("live_verified") is True
            or component.get("verified_live") is True
            or component.get("direction_basis")!=HIST_BASES[name]
            or component.get("symbol")!=symbol
            or component.get("timeframe")!=timeframe
            or type(component.get("generation")) is not int
            or component["generation"]!=generation):
        return None
    ts=component.get("timestamp")
    if type(ts) not in (int,float) or not isfinite(ts) or ts<=0 or ts>last_bar:
        return None
    # Historical evidence must be near the session window being replayed.
    if last_bar-ts>86400:
        return None
    if name in ("futures","options"):
        if not isinstance(component.get("contract"),str) or not component["contract"].strip():
            return None
    if name=="options":
        expiry=component.get("expiry")
        try:
            expiry_day=date.fromisoformat(expiry)
            exact_expiry=(type(expiry) is str
                          and expiry_day.isoformat()==expiry
                          and expiry_day>=datetime.fromtimestamp(
                              last_bar,timezone(timedelta(hours=5,minutes=30))).date())
        except (ValueError,TypeError,OverflowError,OSError):
            exact_expiry=False
        if not exact_expiry or component.get("underlying")!=symbol:
            return None
    b,r=component.get("bullish"),component.get("bearish")
    if type(b) is not int or type(r) is not int or not 0<=b<=100 or b+r!=100:
        return None
    return {"bullish":b,"bearish":r,"historical":True,"verified_live":False,
            "evidence_timestamp":ts,"evidence_basis":HIST_BASES[name]}

def historical_vote_replay(*, symbol, timeframe, generation, source, bars,
                           filter_rows, history_timestamp=None, historical_context=None):
    if (not isinstance(symbol,str) or not symbol or timeframe not in TIMEFRAMES
            or type(generation) is not int or generation<0 or not isinstance(filter_rows,(list,tuple))):
        raise ValueError("Exact replay identity and computed filter rows required")
    result={"mode":"HIST_REPLAY_READ_ONLY","symbol":symbol,
            "timeframe":timeframe,"generation":generation,
            "historical":True,"verified_live":False,"orders_sent":0,
            "provider_requests":0,"fifth_engine_policy":"EXACT_FIVE_SLOTS_SIXTH_M_STANDBY",
            "boxes":[],"technical_vote":None,"candle_vote":None,
            "technical_recomputed_from_completed_bars":False,
            "combined":{"state":"WAIT","coverage":0,
                        "reason":"HIST replay needs three independent directional sources"},
            "historical_combined":{"state":"WAIT","coverage":0,"required":3,
                                   "bullish":None,"bearish":None,
                                   "reason":"HIST_REPLAY_QUORUM_NOT_MET",
                                   "mode":"HIST_ONLY_NOT_LIVE"},
            "blockers":[], "partial_technical_direction":None}
    if source!="Dhan" or not isinstance(bars,(list,tuple)):
        result["blockers"].append("MATCHING_DHAN_HISTORY_REQUIRED")
        return result
    # Validate row shape before any session/timestamp indexing. Malformed
    # cache payloads must abstain, not crash the shared HIST renderer.
    if any(not isinstance(row,(list,tuple)) or len(row)<6
           or type(row[0]) not in (int,float) or not isfinite(row[0])
           or row[0]<=0 for row in bars):
        result["blockers"].append("COMPLETED_SESSION_HISTORY_INVALID_OR_LT_30")
        return result
    try:
        session=historical_regular_session_bars(list(bars),timeframe)
    except (ValueError, OverflowError, OSError):
        result["blockers"].append("COMPLETED_SESSION_HISTORY_INVALID_OR_LT_30")
        return result
    result["excluded_forming_candle_bars"]=0
    if history_timestamp is not None:
        if (type(history_timestamp) not in (int,float)
                or not isfinite(history_timestamp) or history_timestamp<=0):
            raise ValueError("Valid replay observation timestamp required")
        # The phone's clock is a completion cutoff, not source-live proof.
        if session and session[-1][0]>history_timestamp:
            result["blockers"].append("FUTURE_DATED_HIST_CANDLE_NOT_VERIFIED")
            return result
        if session and session[-1][0]+TIMEFRAMES[timeframe]>history_timestamp:
            if (len(session)<31 or
                    session[-1][0]-session[-2][0]!=TIMEFRAMES[timeframe]):
                result["blockers"].append("FORMING_CANDLE_PREDECESSOR_UNVERIFIED")
                return result
            session=session[:-1]
            result["excluded_forming_candle_bars"]=1
            # Filter rows were calculated upstream and may include forming bar.
            result["blockers"].append("TECHNICAL_FILTERS_RECALC_ON_COMPLETED_BARS_REQUIRED")
    valid=(len(session)>=30 and all(
        isinstance(b,(tuple,list)) and len(b)>=6 and
        all(type(v) in (int,float) and isfinite(v) for v in b[:6])
        for b in session))
    if not valid:
        result["blockers"].append("COMPLETED_SESSION_HISTORY_INVALID_OR_LT_30")
        return result
    if any(min(b[1:5])<=0 or b[5]<0 or b[2]<max(b[1],b[3],b[4]) or b[3]>min(b[1],b[4]) for b in session):
        result["blockers"].append("HIST_OHLCV_INVALID")
        result["boxes"]=[{"engine":name,"state":"WAIT","direction":"WAIT",
                          "bullish":None,"bearish":None,
                          "reason":"HIST_OHLCV_INVALID","eligible_live":False}
                         for name in ENGINE_NAMES]
        return result
    if history_timestamp is not None:
        # In real B178/Master phone doctors the clock is always supplied.
        # Recalculate technical input from the validated completed Dhan
        # series, even when its final bar was already closed. Never trust an
        # upstream cached integer vote from another scan or generation.
        selected=[row.get("name",row.get("filter"))
                  for row in filter_rows if isinstance(row,dict)
                  and row.get("name",row.get("filter")) in CANDLE_FILTERS]
        recomputed=(analyze(session,selected,timeframe) if selected else {})
        if (recomputed.get("timestamp")==session[-1][0]
                and recomputed.get("count")==len(session)
                and isinstance(recomputed.get("votes"),list)):
            filter_rows=recomputed["votes"]
            result["technical_recomputed_from_completed_bars"]=True
            if result["excluded_forming_candle_bars"]:
                result["blockers"].remove(
                    "TECHNICAL_FILTERS_RECALC_ON_COMPLETED_BARS_REQUIRED")
        else:
            # A failed recomputation must not reuse stale upstream votes.
            # Preserve selected row names for transparent replay diagnostics.
            filter_rows=[{"name":row.get("name",row.get("filter"))}
                         for row in filter_rows if isinstance(row,dict)]
    unique=set()
    bull=bear=neutral=0
    for row in filter_rows:
        if not isinstance(row,dict):
            raise ValueError("Malformed filter row")
        name=row.get("name",row.get("filter"))
        if not isinstance(name,str) or not name or name in unique:
            raise ValueError("Duplicate or malformed computed filter")
        unique.add(name)
        # Only the 13 candle-derived technical indicators belong to T.
        # News headlines and four option-chain filters are separate evidence
        # lanes and must never inflate a technical ratio, even if a cached or
        # malformed adapter row happens to carry a directional integer.
        if name not in CANDLE_FILTERS:
            continue
        vote=row.get("vote")
        if type(vote) is int and vote in (-1,0,1):
            bull+=vote==1
            bear+=vote==-1
            neutral+=vote==0
    technical=None
    if bull+bear and (history_timestamp is None
                     or result["technical_recomputed_from_completed_bars"]):
        technical={"bullish":round(100*bull/(bull+bear)),
                   "bearish":100-round(100*bull/(bull+bear)),
                   "directional_count":bull+bear,"neutral_count":neutral,
                   "historical":True,"verified_live":False}
    # Match the normal phone C-HIST gate: the last eight completed bars
    # must have exact in-session spacing for the requested timeframe.
    # A timestamp gap is not a bearish/bullish candle and cannot be skipped.
    seconds=TIMEFRAMES[timeframe]
    tail=session[-8:]
    contiguous=(len(tail)==8 and all(
        type(row[0]) in (int,float) and isfinite(row[0]) and row[0]>0
        for row in tail) and all(
        tail[i][0]-tail[i-1][0]==seconds for i in range(1,8)))
    candle=historical_candle_balance(tail,sample_size=8) if contiguous else None
    result["technical_vote"]=technical
    # Useful display-only direction even when independent combined quorum fails.
    # Do not manufacture a combined vote or increase source coverage.
    if technical:
        result["partial_technical_direction"]={
            "state":"BULLISH" if bull>bear else "BEARISH" if bear>bull else "NEUTRAL",
            "bullish":technical["bullish"],"bearish":technical["bearish"],
            "directional_count":bull+bear,"mode":"TECHNICAL_HIST_ONLY_NOT_LIVE"}
    result["candle_vote"]=candle
    measured={}
    for engine in HIST_BASES:
        measured[engine]=_historical_measured(engine,
            historical_context.get(engine) if isinstance(historical_context,dict) else None,
            symbol=symbol,timeframe=timeframe,generation=generation,
            last_bar=session[-1][0])
    for name in ENGINE_NAMES:
        context=(technical if name=="technical" else candle if name=="candle" else
                 measured.get(name))
        missing=("HIST_CANDLE_SAMPLE_NONCONTIGUOUS" if name=="candle" and not contiguous
                 else HIST_BLOCKERS.get(name,"NO_TECHNICAL_DIRECTIONAL_FILTER_VOTES"))
        result["boxes"].append({
            "engine":name,"state":("HIST_VOTE" if context else "WAIT"),
            "direction":("BULLISH" if context and context["bullish"]>context["bearish"]
                          else "BEARISH" if context and context["bearish"]>context["bullish"]
                          else "NEUTRAL" if context else "WAIT"),
            "bullish":context["bullish"] if context else None,
            "bearish":context["bearish"] if context else None,
            "reason":("VERIFIED_DIRECTIONAL_HIST_NOT_LIVE" if name in measured and context else
                      "COMPUTED_HIST_NOT_LIVE" if context else missing),
            "eligible_live":False})
    # HIST observations are not LIVE votes. Missing independent historical
    # inputs remain WAIT; never synthesize an N/F/O vote from context data.
    available=sum(r["state"]=="HIST_VOTE" for r in result["boxes"])
    result["combined"]={"state":"WAIT","coverage":available,"required":3,
                        "reason":"HIST_REPLAY_QUORUM_NOT_MET" if available<3
                                 else "HIST_REPLAY_NOT_LIVE_CERTIFICATION"}
    # Apply the already-audited 3/5 policy to actual replay evidence in a
    # DISTINCT historical-only result. Neither an HIST engine nor this
    # result is eligible for live trading, and no simulated missing N/F/O
    # inputs may be supplied implicitly.
    hist_rows=tuple(
        EngineEvidence(row["engine"],
                       row["bullish"] if row["state"]=="HIST_VOTE" else None,
                       row["bearish"] if row["state"]=="HIST_VOTE" else None,
                       verified=row["state"]=="HIST_VOTE",
                       timestamp=session[-1][0] if row["state"]=="HIST_VOTE" else None,
                       source="Dhan" if row["state"]=="HIST_VOTE" else "")
        for row in result["boxes"])
    historical_policy=combine_evidence(hist_rows)
    result["historical_combined"]={
        "state":historical_policy["state"],
        "coverage":historical_policy["coverage"],
        "required":historical_policy["required"],
        "bullish":historical_policy["bullish"],
        "bearish":historical_policy["bearish"],
        "reason":historical_policy["reason"],
        "mode":"HIST_ONLY_NOT_LIVE"}
    result["historical_session_bars"]=len(session)
    result["removed_outside_session_bars"]=len(bars)-len(session)
    return result


def simulated_conflict_policy_matrix():
    """Synthetic POLICY SELF-TEST ONLY: never represent as historical Dhan votes."""
    patterns={"FOUR_BULL_ONE_BEAR":"BBBBS",
              "THREE_BULL_TWO_BEAR":"BBBSS",
              "FOUR_BEAR_ONE_BULL":"SSSSB"}
    results={}
    for title,pattern in patterns.items():
        rows=[EngineEvidence(name,80 if vote=="B" else 20,
                             20 if vote=="B" else 80,
                             verified=True,timestamp=1795000000,source="Dhan")
              for name,vote in zip(ENGINE_NAMES,pattern)]
        results[title]=combine_evidence(tuple(rows))["state"]
    return {"mode":"SYNTHETIC_POLICY_SELF_TEST_NO_REAL_MARKET_SIGNALS",
            "results":results,"live_verified":False,"orders_sent":0}
