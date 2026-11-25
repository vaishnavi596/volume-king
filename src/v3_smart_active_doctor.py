import math

def active_report(*, generation, symbols, quote_present, index_present, connected,
                  signal_present, attempts, now_monotonic, market_open,
                  errors, progress, performance, quote_attempt_age,
                  candle_stamps=None, now_epoch=None, quote_success_age=None, outcomes=None, recent_errors=None, skip_events=None, engine_observation=None, historical_indicator_observation=None, historical_prewarm_observation=None, historical_equity_worker_observation=None, final_vote_observation=None, quote_contract_errors=None, quote_time_observation=None):
    """Compact cache-only observation; never certify unmeasured functionality."""
    issues = []
    hidden = []
    def check(name, ok, detail):
        if ok:
            hidden.append(name)
        else:
            issues.append(dict(check=name, status="PENDING_OR_ERROR", **detail))
    total = len(symbols)
    check("CONNECTION", all(connected.values()), {"connected": connected})
    check("EQUITY_QUOTE_COVERAGE", bool(total) and len(quote_present)==total,
          {"available": len(quote_present), "selected": total})
    check("INDEX_QUOTE_COVERAGE", len(index_present)==3,
          {"available": len(index_present), "required": 3})
    check("WATCHLIST_ROSTER", len(set(symbols))==total and 0<total<=70,
          {"selected": total, "unique": len(set(symbols)), "limit": 70})
    check("WATCHLIST_SIGNAL_CACHE", bool(total) and len(signal_present)==total,
          {"available": len(signal_present), "selected": total,
           "scope": "existing signal entries only, not candle validation"})
    check("OBSERVED_ERRORS", not errors, {"errors": errors})
    ages = {sym: round(max(0, now_monotonic-attempts[sym]),1)
            for sym in symbols if sym in attempts}
    issues.append({"check": "WATCHLIST_FAIR_REFRESH", "status": "TESTING",
                   "market_open": market_open, "selected": total,
                   "attempted": len(ages), "unattempted": total-len(ages),
                   "oldest_attempt_age_seconds": max(ages.values(),default=None),
                   "oldest_attempt_symbols": sorted(ages,key=ages.get,reverse=True)[:5],
                   "attempt_is_not_success": True, "performance": performance})
    candle_stamps = candle_stamps or {}
    candle_ages = {sym: round(now_epoch-candle_stamps[sym],1)
                   for sym in symbols if sym in candle_stamps
                   and type(now_epoch) in (int,float) and math.isfinite(now_epoch)
                   and type(candle_stamps[sym]) in (int,float)
                   and math.isfinite(candle_stamps[sym])
                   and 0<candle_stamps[sym]<=now_epoch}
    stale = [sym for sym in candle_ages if candle_ages[sym]>360]
    # Cache observation does not certify transport success.
    issues[-1]["gate_snapshot"] = progress.get("watchlist_gate_snapshot", {})
    issues[-1]["gate_scope"] = "instantaneous periodic scheduler gates, not recorded skip history; scanner interleave can still run"
    outcomes = outcomes or {}
    issues[-1]["recent_error_history"] = list(recent_errors or [])[-5:]
    recent_skips = [row for row in (skip_events or []) if row.get("generation")==generation
                    and 0<=now_monotonic-row["at"]<=180]
    skip_counts = {}
    for row in recent_skips:
        reason=row["reason"]
        skip_counts[reason]=skip_counts.get(reason,0)+1
    issues[-1]["recorded_skip_counts_last_180s"] = skip_counts
    issues[-1]["recent_skip_events"] = [
        {"lane":row["lane"],"reason":row["reason"],"symbol":row["symbol"],
         "age_seconds":round(now_monotonic-row["at"],1)}
        for row in recent_skips[-12:]]
    issues[-1]["skip_history_scope"] = "bounded last 120 events; grouped guards, not exhaustive individual causes"
    issues[-1]["symbol_observations"] = [
        {"symbol":sym, "attempt_age_seconds":ages.get(sym),
         "cached_completed_3m_age_seconds":candle_ages.get(sym),
         "quote_cached":sym in quote_present,
         "last_read_outcome":outcomes.get(sym,{}).get("state","NOT_OBSERVED"),
         "last_read_age_seconds":round(max(0,now_monotonic-outcomes[sym]["at"]),1) if sym in outcomes else None,
         "transport_success":"UNVERIFIED"}
        for sym in symbols]
    issues.append({"check": "CONTINUOUS_QUOTE_AND_CANDLE_FRESHNESS",
                   "status": "UNVERIFIED", "last_quote_attempt_age_seconds": quote_attempt_age,
                   "last_quote_success_age_seconds": quote_success_age,
                   "quote_success_scope": "batch success clock; may include partial batch, not per-symbol exchange freshness",
                   "completed_3m_timestamp_count": len(candle_ages),
                   "missing_completed_3m_timestamp_count": total-len(candle_ages),
                   "older_than_360s_count": len(stale),
                   "oldest_candles": [{"symbol":sym,"age_seconds":candle_ages[sym]}
                      for sym in sorted(candle_ages,key=candle_ages.get,reverse=True)[:5]],
                   "age_scope": "cached analyzed completed candle; 360s diagnostic threshold, not exchange proof",
                   "exchange_live_verified": False})
    issues.append({"check": "SCANNER_RANKING", "status": "TESTING", "progress": progress})
    if engine_observation is not None:
        issues.append(dict(check="ML5_FIVE_ENGINE_READINESS",status="TESTING",**engine_observation))
    if historical_indicator_observation is not None:
        observed=historical_indicator_observation
        matching=observed.get("generation")==generation
        if not matching or not observed.get("successes") or observed.get("last_error"):
            issues.append({"check":"HISTORICAL_INDICATOR_RUNTIME",
                "code":"BK-HIST-001" if matching and observed.get("last_error") else "BK-HIST-002",
                "status":"ERROR" if matching and observed.get("last_error") else "UNVERIFIED",
                "module":"main.py","function":"historical_indicator_result",
                "evidence":dict(observed) if matching else {},
                "scope":"local calculation only; not live source or complete wiring proof"})
        else:
            hidden.append("HISTORICAL_INDICATOR_RUNTIME")
    if historical_prewarm_observation is not None:
        worker=historical_prewarm_observation
        matching=worker.get("generation")==generation
        if not matching or not worker.get("successes") or worker.get("last_error"):
            issues.append({"check":"HISTORICAL_INDEX_WORKER","status":"ERROR" if matching and worker.get("last_error") else "UNVERIFIED",
                "code":"BK-HIST-WORKER-001" if matching and worker.get("last_error") else "BK-HIST-WORKER-002",
                "module":"main.py","function":"prewarm_index_historical_indicator",
                "evidence":dict(worker) if matching else {},
                "scope":"index 1m local prewarm only; synchronous fallback remains"})
        else:
            hidden.append("HISTORICAL_INDEX_WORKER")
    if historical_equity_worker_observation is not None:
        worker=historical_equity_worker_observation
        matching=worker.get("generation")==generation
        if not matching or not worker.get("successes") or worker.get("last_error"):
            issues.append({"check":"HISTORICAL_EQUITY_WORKER","status":"ERROR" if matching and worker.get("last_error") else "UNVERIFIED",
                "code":"BK-HIST-WORKER-003" if matching and worker.get("last_error") else "BK-HIST-WORKER-004",
                "module":"main.py","function":"prewarm_equity_historical_indicator",
                "evidence":dict(worker) if matching else {},
                "scope":"3m/5m local cache prewarm; synchronous fallback remains"})
        else:
            hidden.append("HISTORICAL_EQUITY_WORKER")
    if final_vote_observation is not None:
        if final_vote_observation.get("generation") != generation:
            issues.append({"check":"FINAL_VOTE_FRAME_GUARD","status":"UNVERIFIED",
                           "code":"BK-FINAL-FRAME-002","scope":"selected frame observation generation mismatch"})
        elif final_vote_observation.get("status") == "FRAME_SUPPORTED":
            hidden.append("FINAL_VOTE_FRAME_GUARD")
        else:
            issues.append(dict(check="FINAL_VOTE_FRAME_GUARD",**final_vote_observation))
    if quote_time_observation is not None:
        issues.append(dict(check="QUOTE_TIMESTAMP_OBSERVATION",**quote_time_observation))
    for row in quote_contract_errors or ():
        if row.get("generation")==generation and row.get("code")=="BK-QUOTE-001":
            issues.append(dict(check="QUOTE_CONTRACT",**row))
    issues.append({"check": "FULL_FUNCTIONAL_WIRING", "status": "NOT_RUN_IN_ACTIVE_MODE",
                   "scope": "five engines, final voting, chart, paper, lifecycle, alerts, backtest",
                   "next": "Use MASTER DIAG for full audit"})
    return {"test":"V3_SMART_ACTIVE_DOCTOR","mode":"LIGHTWEIGHT_CACHE_ONLY",
            "provider_generation": generation,"healthy_hidden_count":len(hidden),
            "active_count":len(issues),"active":issues,
            "source_live_verified":False,"provider_requests":0,"orders_sent":0}


def ml5_engine_observation(*, symbol, timeframe, generation, history, news, futures,
                           options, snapshot, now, connected, technical_agreement=None,
                           quote=None):
    """Cache-only exact identity audit. No new signal or authorization."""
    from five_engine import ENGINE_NAMES, snapshot_for_display, independent_engine_source_contract
    from v3_four_box_source_readiness import four_box_source_readiness
    from filter_wiring_audit import diagnostic_candle_readiness
    from math import isfinite
    identity={"symbol":symbol,"timeframe":timeframe,"generation":generation}
    if timeframe not in ("1m","3m","5m"):
        return {"identity":identity,"comparison_status":"UNVERIFIED",
                "reason":"ML5 audit requires 1m/3m/5m","boxes":[]}
    readiness=four_box_source_readiness(symbol=symbol,timeframe=timeframe,
        generation=generation,history=history,news_cache=news,
        futures_cache=futures,option_context=options,now=now)
    stage=diagnostic_candle_readiness(history,timeframe,now=now)
    rows=readiness["box_sources"]
    rows["T"]={"cache_present":bool(history.get("bars")) and history.get("source")=="Dhan"
              and history.get("_scanner_timeframe")==timeframe,
              "historical_direction_available":technical_agreement is not None,
              "historical_bullish":technical_agreement[0] if technical_agreement else None,
              "historical_bearish":technical_agreement[1] if technical_agreement else None,
              "blocker":stage}
    display=snapshot_for_display(snapshot if connected else None,now=now)
    contract=independent_engine_source_contract()
    boxes=[]
    for short,name,evidence in zip("TCNFO",ENGINE_NAMES,display["engines"]):
        eligible=evidence.eligible and evidence.source=="Dhan"
        row=dict(rows[short])
        row.update(box=short,engine=name,adapter=contract[name]["adapter"],
                   source_wiring=contract[name]["readiness"],
                   live_vote_eligible=eligible,live_direction_verified=eligible,
                   live_bullish=evidence.bullish if eligible else None,
                   live_bearish=evidence.bearish if eligible else None,
                   live_gate_reason=evidence.reason)
        boxes.append(row)
    timestamp_observation=quote_timestamp_observation(symbol=symbol,quote=quote,now=now)
    valid_stamp=timestamp_observation["timestamp_observed"]
    return {"identity":identity,"boxes":boxes,"combined":display["combined"],
            "sixth_M":"INERT_NOT_SCORED",
            "quote_timestamp_observed":bool(valid_stamp),
            "quote_timestamp_age_seconds":timestamp_observation["timestamp_age_seconds"],
            "quote_timestamp_scope":"existing cache field; not independent exchange proof",
            "comparison_status":"UNVERIFIED",
            "comparison_scope":"compare same symbol/frame/roster/session across build reports",
            "provider_requests":0,"orders_sent":0}


def final_vote_frame_observation(*, symbol, timeframe, generation, display_mode):
    """Selected-frame policy observation only; never certify screen parity."""
    supported = timeframe in ("1m", "3m", "5m")
    return {"feature_id":"B4.05", "symbol":symbol, "timeframe":timeframe,
            "generation":generation, "display_mode":display_mode,
            "status":"FRAME_SUPPORTED" if supported else "UNVERIFIED",
            "code":None if supported else "BK-FINAL-FRAME-001",
            "module":"main.py", "function":"scanner_historical_final_vote",
            "expected_frames":["1m","3m","5m"],
            "scope":"selected frame eligibility only; actual four-screen parity not measured",
            "next":None if supported else "Select 1m, 3m or 5m for final voting",
            "provider_requests":0, "orders_sent":0}


class QuoteContractObservation:
    """Bounded two-lane runtime observation; no I/O, raw errors or LIVE proof."""
    def __init__(self):
        self._active = {}

    def failed(self, lane, generation, current_generation, exc):
        from clone_v2_gateway import FeedError
        if (lane not in ("indices","equities") or generation != current_generation
                or not isinstance(exc, FeedError)
                or not str(exc).startswith("BK-QUOTE-001:")):
            return
        self._active[lane] = {"code":"BK-QUOTE-001","status":"ERROR",
            "feature_id":"B1.03","generation":generation,"lane":lane,
            "module":"clone_v2_gateway.py","function":"market_quotes",
            "expected":"unavailable list contains requested symbol strings",
            "observed":"invalid unavailable symbol rejected",
            "scope":"local transport contract; not exchange proof",
            "next":"Inspect sanitized gateway response contract; retain last good quotes"}

    def recovered(self, lane, generation, current_generation):
        if generation == current_generation:
            row=self._active.get(lane)
            if row and row["generation"]==generation:
                self._active.pop(lane,None)

    def active(self, generation):
        return [dict(row) for row in self._active.values()
                if row["generation"]==generation]


def quote_timestamp_observation(*, symbol, quote, now):
    """Read-only cached timestamp evidence; not independent exchange proof."""
    q=quote if isinstance(quote,dict) else {}
    stamp=q.get("quote_timestamp")
    valid=(q.get("source")=="Dhan" and q.get("symbol",symbol)==symbol
           and type(now) in (int,float) and math.isfinite(now)
           and type(stamp) in (int,float) and math.isfinite(stamp)
           and 946684800<=stamp<=now)
    return {"symbol":symbol,"feature_id":"B1.01",
            "code":None if valid else "BK-QUOTE-TIME-001",
            "status":"OBSERVED_UNVERIFIED" if valid else "UNVERIFIED",
            "timestamp_observed":valid,
            "cached_quote":q.get("cached") is True,
            "quote_session_scope":"RESTORED_CACHE" if q.get("cached") is True else "UNVERIFIED_CURRENT_SESSION",
            "timestamp_age_seconds":round(now-stamp,1) if valid else None,
            "scope":"cached Dhan trade timestamp only; not exchange or LIVE verification",
            "source_live_verified":False,"provider_requests":0,"orders_sent":0}
