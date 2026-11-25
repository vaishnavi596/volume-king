def active_report(*, generation, symbols, quote_present, index_present, connected,
                  signal_present, attempts, now_monotonic, market_open,
                  errors, progress, performance, quote_attempt_age):
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
    issues.append({"check": "CONTINUOUS_QUOTE_AND_CANDLE_FRESHNESS",
                   "status": "UNVERIFIED", "last_quote_attempt_age_seconds": quote_attempt_age,
                   "exchange_live_verified": False})
    issues.append({"check": "SCANNER_RANKING", "status": "TESTING", "progress": progress})
    issues.append({"check": "FULL_FUNCTIONAL_WIRING", "status": "NOT_RUN_IN_ACTIVE_MODE",
                   "scope": "five engines, final voting, chart, paper, lifecycle, alerts, backtest",
                   "next": "Use MASTER DIAG for full audit"})
    return {"test":"V3_SMART_ACTIVE_DOCTOR","mode":"LIGHTWEIGHT_CACHE_ONLY",
            "provider_generation": generation,"healthy_hidden_count":len(hidden),
            "active_count":len(issues),"active":issues,
            "source_live_verified":False,"provider_requests":0,"orders_sent":0}
