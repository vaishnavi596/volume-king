"""V2 app-local Help / Error Doctor, adapted from V1 error_doctor.

Only sanitized codes and safe guidance. No network, server settings, tokens,
URLs, credentials, raw response bodies or automatic retry/deployment action.
"""
_RULES = (
    (("429", "rate limit", "cooldown"), "BK-DHAN-429",
     "Dhan request quota/cooldown", "Wait for cooldown; retry only when permitted"),
    (("401", "token expired", "reauthentication"), "BK-AUTH-401",
     "Provider authorization unverified", "Ask the authorized Master to check token status"),
    (("403", "key rejected"), "BK-GATEWAY-403",
     "Read-only data access denied", "Check authorized device session status"),
    (("422", "instrument", "mapping"), "BK-MAP-422",
     "Instrument or timeframe unavailable", "Verify selected symbol and timeframe"),
    (("timeout", "connection", "network"), "BK-NETWORK",
     "Network unavailable", "Check connectivity; preserve last-good prices"),
    (("502", "503", "504", "upstream"), "BK-UPSTREAM",
     "Data source temporarily unavailable", "Preserve last-good data and recheck health"),
    (("no verified candles", "no valid data", "unavailable"), "BK-CANDLES",
     "Candle history unavailable or incomplete", "Keep last valid chart; show HIST or WAIT"),
)


def diagnose(message):
    """Categorize local error; never echo input (might contain a secret)."""
    if not isinstance(message, str):
        return ("BK-UNKNOWN", "Cause not established",
                "Collect only sanitized status and retry metadata")
    s = message[:256].lower()
    for keywords, code, cause, action in _RULES:
        if any(keyword in s for keyword in keywords):
            return code, cause, action
    return ("BK-UNKNOWN", "Cause not established",
            "Collect only sanitized status and retry metadata")


def help_for(topic):
    """Safe UI help text, never server configuration steps."""
    return {
        "Dashboard": "NIFTY, BANKNIFTY and SENSEX use independent index data.",
        "Watchlist": "Up to 70 unique equities across five lists; no duplicate.",
        "Scanner": "Selected symbol/timeframe updates historical chart; LIVE is not inferred.",
        "Super Five": "Verified evidence is required; otherwise WAIT.",
        "Options": "Expiry and ATM±3 CE/PE require trusted Dhan evidence.",
        "Filters": "Five evidence-gated filters; sixth slot reserved and unscored.",
        "Settings": "Refresh, timeframes and local watchlists are app-owned.",
    }.get(topic, "Feature status depends on validated read-only market evidence.")
