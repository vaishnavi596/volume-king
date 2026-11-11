"""Safe, offline Dhan renewal eligibility checks.

This module never reads credentials, calls Dhan, or changes tokens.
Actual renewal must use a verified token provenance and secure storage.
"""
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
SUPPORTED_SOURCES = frozenset({"dhan_web", "oauth_consent", "totp_generated", "unknown"})


def renewal_decision(token_source, expiry_time, now=None, lead_minutes=90):
    """Return a conservative renewal plan without attempting authentication.

    Only active Dhan Web tokens are eligible for the documented RenewToken API.
    OAuth and unknown tokens must never be submitted to that endpoint.
    """
    if token_source not in SUPPORTED_SOURCES:
        raise ValueError("Unrecognized token source")
    if not isinstance(lead_minutes, int) or isinstance(lead_minutes, bool) or not 1 <= lead_minutes <= 720:
        raise ValueError("Invalid renewal lead time")
    if not isinstance(expiry_time, datetime):
        raise ValueError("Expiry must be a datetime")
    if expiry_time.tzinfo is None:
        expiry_time = expiry_time.replace(tzinfo=IST)
    current = now if now is not None else datetime.now(timezone.utc)
    if not isinstance(current, datetime) or current.tzinfo is None:
        raise ValueError("Current time must have a timezone")
    remaining = expiry_time.astimezone(timezone.utc) - current.astimezone(timezone.utc)
    if remaining <= timedelta(0):
        return {"state": "expired", "action": "reauthenticate", "renew_token_allowed": False}
    if token_source != "dhan_web":
        return {"state": "provenance_unverified" if token_source == "unknown" else "renew_api_unsupported",
                "action": "use_verified_authentication_flow", "renew_token_allowed": False}
    if remaining > timedelta(minutes=lead_minutes):
        return {"state": "valid", "action": "wait", "renew_token_allowed": True}
    return {"state": "renewal_due", "action": "renew_before_expiry", "renew_token_allowed": True}
