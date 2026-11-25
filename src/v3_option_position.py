"""Read-only option positioning context; never an authenticated directional vote."""
from datetime import date, datetime, timezone, timedelta
from math import isfinite
from five_engine import option_chain_display_context

def historical_option_position(metrics, *, symbol, expiry, now):
    missing={"available":False,"code":"BK-OPT-001","reason":"Exact Dhan option context missing or invalid","live_vote_eligible":False}
    if not isinstance(metrics,dict) or metrics.get("symbol")!=symbol or metrics.get("expiry")!=expiry:
        return missing
    try:
        if type(now) not in (int,float) or not isfinite(now) or now<=0:
            return missing
        day=date.fromisoformat(expiry)
        if day.isoformat()!=expiry or day<datetime.fromtimestamp(now,timezone(timedelta(hours=5,minutes=30))).date():
            return missing
    except (TypeError,ValueError,OverflowError,OSError):
        return missing
    window=option_chain_display_context(metrics)
    if not window.get("available"):
        return dict(missing,code="BK-OPT-002",reason=window.get("reason"))
    rows=window["rows"]
    call=sum(row["ce"]["oi"] for row in rows)
    put=sum(row["pe"]["oi"] for row in rows)
    if not isfinite(call+put) or call+put<=0:
        return dict(missing,code="BK-OPT-003",reason="No usable ATM-window open interest")
    return {"available":True,"code":"BK-OPT-004","state":"HIST_CONTEXT",
            "position":"PUT_OI_HEAVY" if put>call else "CALL_OI_HEAVY" if call>put else "BALANCED",
            "call_oi":call,"put_oi":put,"expiry":expiry,
            "reason":"ATM-window OI positioning; trade direction and exchange freshness unverified",
            "live_vote_eligible":False}
