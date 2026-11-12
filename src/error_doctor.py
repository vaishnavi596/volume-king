"""Local, read-only BOT KING error triage. No secrets or remote AI calls."""

def diagnose(message):
    """Return stable code, likely cause and safe next action from a visible error."""
    s = str(message or "").lower()
    if "429" in s or "rate limit" in s or "cooldown" in s:
        return ("BK-DHAN-429", "Dhan request quota/cooldown", "Wait for the reported cooldown; retry one request, not the entire scan")
    if "401" in s or "token expired" in s or "reauthentication" in s:
        return ("BK-AUTH-401", "Provider authorization needs verification", "Check Dhan status in Settings; do not rotate keys automatically")
    if "403" in s or "key rejected" in s:
        return ("BK-GATEWAY-403", "Gateway access denied", "Verify server pairing status in Settings")
    if "422" in s or "instrument" in s or "mapping" in s:
        return ("BK-MAP-422", "Instrument or interval unsupported", "Check symbol mapping and candle interval")
    if "timeout" in s or "connection" in s or "network" in s:
        return ("BK-NETWORK", "Request timed out or network unavailable", "Check HTTPS connectivity before retrying")
    if "502" in s or "503" in s or "504" in s or "upstream" in s:
        return ("BK-UPSTREAM", "Gateway/upstream data failure", "Check Oracle and Dhan response logs")
    if "no verified candles" in s or "no valid data" in s or "unavailable" in s:
        return ("BK-CANDLES", "Candle data unavailable or incomplete", "Check historical response and scan progress")
    return ("BK-UNKNOWN", "Cause not established from current evidence", "Collect sanitized error and endpoint diagnostics")
