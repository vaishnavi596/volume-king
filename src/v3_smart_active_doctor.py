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
    # B243: market-aware. After the close the live Dhan quote feed is expected to be off and
    # 0 live quotes is normal; only an SSK/Oracle problem is an error then.
    expected_closed = not market_open
    connection_ok = bool(connected) and (all(v is True for v in connected.values())
                     or (expected_closed and connected.get("Oracle") is True))
    check("CONNECTION", connection_ok, {"connected": connected})
    check("EQUITY_QUOTE_COVERAGE", expected_closed or (bool(total) and set(quote_present)==set(symbols)),
          {"available": len(quote_present), "selected": total})
    check("INDEX_QUOTE_COVERAGE", set(index_present)=={"NIFTY","BANKNIFTY","SENSEX"},
          {"available": len(index_present), "required": 3})
    check("WATCHLIST_ROSTER", len(set(symbols))==total and 0<total<=70,
          {"selected": total, "unique": len(set(symbols)), "limit": 70})
    check("WATCHLIST_SIGNAL_CACHE", bool(total) and set(signal_present)==set(symbols),
          {"available": len(signal_present), "selected": total,
           "scope": "existing signal entries only, not candle validation"})
    check("OBSERVED_ERRORS", not errors, {"errors": errors})
    def valid_monotonic_stamp(value):
        return (type(value) in (int,float) and math.isfinite(value)
                and type(now_monotonic) in (int,float) and math.isfinite(now_monotonic)
                and 0<=value<=now_monotonic)
    ages = {sym: round(now_monotonic-attempts[sym],1)
            for sym in set(symbols) if sym in attempts and valid_monotonic_stamp(attempts[sym])}
    invalid_attempts = sorted({sym for sym in symbols if sym in attempts
                               and not valid_monotonic_stamp(attempts[sym])})
    issues.append({"check": "WATCHLIST_FAIR_REFRESH", "status": "TESTING",
                   "market_open": market_open, "selected": total,
                   "attempted": len(ages), "unattempted": len(set(symbols))-len(ages),
                   "invalid_attempt_symbols":invalid_attempts,
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
    # B240: Watchlist frame is 1m, so a completed bar is "stale" after 180 s,
    # and only while the market is open (after the close every bar is old by design).
    CANDLE_STALE_SECONDS = 180
    stale = ([sym for sym in candle_ages if candle_ages[sym]>CANDLE_STALE_SECONDS]
             if market_open else [])
    # Cache observation does not certify transport success.
    issues[-1]["gate_snapshot"] = progress.get("watchlist_gate_snapshot", {})
    issues[-1]["gate_scope"] = "instantaneous periodic scheduler gates, not recorded skip history; scanner interleave can still run"
    outcomes = {sym:row for sym,row in (outcomes or {}).items()
                if isinstance(row,dict) and valid_monotonic_stamp(row.get("at"))}
    issues[-1]["recent_error_history"] = list(recent_errors or [])[-5:]
    recent_skips = [row for row in (skip_events or []) if isinstance(row,dict)
                    and row.get("generation")==generation and valid_monotonic_stamp(row.get("at"))
                    and now_monotonic-row["at"]<=180
                    and all(isinstance(row.get(k),str) for k in ("reason","lane","symbol"))]
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
    def read_problem(sym):
        state=outcomes.get(sym,{}).get("state","NOT_OBSERVED")
        return state in ("NOT_OBSERVED","DISCARDED_RESPONSE","INVALID_RESPONSE","UNKNOWN_ORIGIN") or str(state).startswith("ERROR")
    def symbol_problems(sym):
        found=[]
        cached_ok = (not market_open) and sym in candle_ages  # after close a cached candle is OK
        if sym not in ages and not cached_ok: found.append("NO_ATTEMPT")
        state=outcomes.get(sym,{}).get("state","NOT_OBSERVED")
        if read_problem(sym) and not (cached_ok and state=="NOT_OBSERVED"):
            found.append("READ_"+str(state))
        if market_open and sym not in quote_present: found.append("NO_QUOTE")
        if market_open and sym not in candle_ages: found.append("NO_CANDLE")
        if sym in stale: found.append("CANDLE_OLDER_THAN_180S")
        return found
    problem_rows = []
    for sym in symbols:
        found = symbol_problems(sym)
        if found:
            problem_rows.append({"symbol":sym, "problems":found,
             "attempt_age_seconds":ages.get(sym),
             "cached_completed_3m_age_seconds":candle_ages.get(sym),
             "quote_cached":sym in quote_present,
             "last_read_outcome":outcomes.get(sym,{}).get("state","NOT_OBSERVED"),
             "last_read_age_seconds":round(max(0,now_monotonic-outcomes[sym]["at"]),1) if sym in outcomes else None,
             "transport_success":"UNVERIFIED"})
    issues[-1]["symbols_ok_count"] = total-len(problem_rows)
    issues[-1]["symbols_with_problem_count"] = len(problem_rows)
    issues[-1]["symbol_observations"] = problem_rows[:12]
    issues[-1]["symbol_observations_scope"] = ("only symbols with a problem, max 12; healthy symbols are counted, not listed"
                                               if problem_rows else "no symbol problems observed; healthy symbols are counted only")
    issues.append({"check": "CONTINUOUS_QUOTE_AND_CANDLE_FRESHNESS",
                   "status": "UNVERIFIED", "last_quote_attempt_age_seconds": quote_attempt_age,
                   "last_quote_success_age_seconds": quote_success_age,
                   "quote_success_scope": "batch success clock; may include partial batch, not per-symbol exchange freshness",
                   "completed_3m_timestamp_count": len(candle_ages),
                   "missing_completed_3m_timestamp_count": total-len(candle_ages),
                   "older_than_180s_count": len(stale),
                   "oldest_candles": [{"symbol":sym,"age_seconds":candle_ages[sym]}
                      for sym in sorted(candle_ages,key=candle_ages.get,reverse=True)[:5]],
                   "age_scope": "cached analyzed completed candle; 1m frame: >180s is old only while market is open (not judged after close); not exchange proof",
                   "exchange_live_verified": False})
    issues.append({"check": "SCANNER_RANKING", "status": "TESTING", "progress": progress})
    if engine_observation is not None:
        compact=dict(engine_observation)
        boxes=[b for b in compact.get("boxes",[]) if isinstance(b,dict)]
        # B240: boxes that are live-eligible collapse to one word; only blocked boxes show detail.
        compact["boxes"]=[b if not b.get("live_vote_eligible") else {"box":b.get("box"),"live_vote_eligible":True}
                          for b in boxes]
        compact["boxes_live_ok"]=[b.get("box") for b in boxes if b.get("live_vote_eligible")]
        compact["boxes_blocked"]=[b.get("box") for b in boxes if not b.get("live_vote_eligible")]
        issues.append(dict(check="ML5_FIVE_ENGINE_READINESS",status="TESTING",**compact))
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
        # B243: never having run is not an error (Watchlist is 1m; this prewarm is only for 3m/5m scans).
        if matching and worker.get("last_error"):
            issues.append({"check":"HISTORICAL_EQUITY_WORKER","status":"ERROR" if matching and worker.get("last_error") else "UNVERIFIED",
                "code":"BK-HIST-WORKER-003" if matching and worker.get("last_error") else "BK-HIST-WORKER-004",
                "module":"main.py","function":"prewarm_equity_historical_indicator",
                "evidence":dict(worker) if matching else {},
                "scope":"local cache prewarm; synchronous fallback remains"})
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
    # B243: one short line per failing point: what, why, what to do next.
    next_step = {
        "CONNECTION":"Settings -> Connect Clone V2 (SSK); Doctor reconnects a saved key by itself",
        "EQUITY_QUOTE_COVERAGE":"market hours: Watchlist -> Refresh data; check Dhan connection",
        "INDEX_QUOTE_COVERAGE":"Doctor retries the index snapshot; else Connect Clone V2 (SSK)",
        "WATCHLIST_ROSTER":"Watchlist: remove duplicates / stay within 70 symbols",
        "WATCHLIST_SIGNAL_CACHE":"Watchlist -> Refresh data",
        "OBSERVED_ERRORS":"open Doctor details for the error list",
        "WATCHLIST_FAIR_REFRESH":"Doctor restarts a stalled pass; else Watchlist -> Refresh data",
        "CONTINUOUS_QUOTE_AND_CANDLE_FRESHNESS":"market hours: check Dhan connection and Watchlist refresh",
        "HISTORICAL_INDICATOR_RUNTIME":"send MASTER DIAG",
        "HISTORICAL_INDEX_WORKER":"send MASTER DIAG",
        "HISTORICAL_EQUITY_WORKER":"send MASTER DIAG",
        "FINAL_VOTE_FRAME_GUARD":"select 1m frame; send MASTER DIAG if it stays",
        "QUOTE_CONTRACT":"send Doctor report",
    }
    error_report = []
    for issue in issues:
        name = issue.get("check")
        status = issue.get("status")
        if name == "FULL_FUNCTIONAL_WIRING":
            continue
        if name == "WATCHLIST_FAIR_REFRESH":
            bad = bool(issue.get("symbols_with_problem_count"))
        else:
            bad = status in ("PENDING_OR_ERROR","ERROR") or (status == "UNVERIFIED" and market_open)
        if not bad:
            continue
        if name == "CONNECTION":
            reason = ("SSK/Oracle not connected" if not (connected or {}).get("Oracle")
                      else "Dhan live feed off (market open)")
        elif name == "EQUITY_QUOTE_COVERAGE":
            reason = str(issue.get("available"))+"/"+str(issue.get("selected"))+" live quotes (market open)"
        elif name == "WATCHLIST_FAIR_REFRESH":
            names = [str(r.get("symbol")) for r in issue.get("symbol_observations", [])[:3]]
            reason = str(issue.get("symbols_with_problem_count"))+" symbols with a problem: "+", ".join(names)
        else:
            reason = str(issue.get("reason") or issue.get("scope") or "see details above")[:120]
        error_report.append({"point": name, "status": status, "code": issue.get("code"),
                             "reason": reason, "next": next_step.get(name, "send Doctor report")})
    return {"test":"V3_SMART_ACTIVE_DOCTOR","mode":"LIGHTWEIGHT_CACHE_ONLY",
            "provider_generation": generation,"healthy_hidden_count":len(hidden),
            "error_report":error_report,"error_count":len(error_report),
            "active_count":len(issues),"active":issues,
            "source_live_verified":False,"provider_requests":0,"orders_sent":0}


def area_watch_issues(*, market_open, oracle_connected, ssk_saved, scanner_state,
                      scanner_busy, scanner_idle_seconds, chain_age, chain_symbol,
                      super_five_age, super_five_count, o_vote_age, watch_stalled_seconds,
                      server_paper_reachable=None):
    """B247 cache-only area watchers. Returns error_report rows ({point,status,code,reason,next}).

    Market-aware: age limits apply only while the market is open. Never calls a provider."""
    rows = []
    def add(point, reason, nxt, code):
        rows.append({"point": point, "status": "PENDING_OR_ERROR", "code": code,
                     "reason": reason, "next": nxt})
    if not oracle_connected and ssk_saved:
        add("GATEWAY_SSK", "SSK disconnected but a saved key exists",
            "Doctor reconnects the saved key; else Settings -> Connect", "BK-AREA-GW-001")
    if market_open and oracle_connected:
        if scanner_idle_seconds is not None and scanner_idle_seconds > 900 and not scanner_busy:
            add("SCANNER_STUCK", "no scan result for %d min while market open" % (scanner_idle_seconds // 60),
                "Scanner -> Scan now", "BK-AREA-SCAN-001")
        if chain_age is not None and chain_age > 90:
            add("OPTIONS_CHAIN_AGE", "%s option chain %ds old (limit 90s)" % (chain_symbol, int(chain_age)),
                "Doctor reloads the chain; else open Options", "BK-AREA-OPT-001")
        if super_five_count and super_five_age is not None and super_five_age > 300:
            add("SUPER_FIVE_STALE", "Super Five ranking %ds old (limit 300s)" % int(super_five_age),
                "Scanner -> Scan now", "BK-AREA-S5-001")
        if o_vote_age is not None and o_vote_age > 180:
            add("O_VOTE_AGE", "O option vote %ds old (limit 180s)" % int(o_vote_age),
                "Options chain refresh", "BK-AREA-O-001")
        if watch_stalled_seconds is not None and watch_stalled_seconds > 60:
            add("WATCHLIST_NO_PROGRESS", "Watchlist no progress for %ds" % int(watch_stalled_seconds),
                "Doctor restarts the stalled pass", "BK-AREA-WL-001")
    if oracle_connected and server_paper_reachable is False:
        add("SERVER_PAPER_ENGINE", "server paper engine not reachable",
            "check Oracle service botking-clone-v2", "BK-AREA-SRV-001")
    return rows


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
