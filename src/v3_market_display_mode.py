"""Phone-local display mode: no network, no market-open inference from stale data.

AUTO permits a last-good HIST fallback on an unexpected weekday outage, but
never describes such an outage as an official exchange holiday.
"""
MODES=("AUTO","HISTORICAL","LIVE_ONLY")

def normalized_mode(value):
    return value if value in MODES else "AUTO"

def resolve_mode(value, *, session_eligible, live_verified, history_valid):
    mode=normalized_mode(value)
    live=bool(session_eligible and live_verified)
    historical=bool(history_valid)
    if mode=="HISTORICAL":
        return "HIST" if historical else "WAIT"
    if mode=="LIVE_ONLY":
        return "LIVE" if live else "WAIT"
    if live:
        return "LIVE"
    if historical:
        return "HIST"
    return "WAIT"
