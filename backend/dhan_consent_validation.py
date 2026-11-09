"""Offline consent-token validation before any future persistence integration.

No network, token replacement, service restart or renewal is performed here.
"""
from datetime import datetime, timezone


def validate_consent_response(payload, expected_client_id, now=None):
    """Return (token, UTC expiry) only for an explicitly matching account.

    Reject absent/ambiguous expiry timestamps instead of silently accepting
    credentials that might already have expired.
    """
    if not isinstance(payload, dict):
        raise ValueError("Invalid Dhan consent response")
    if not isinstance(expected_client_id, str) or not expected_client_id:
        raise ValueError("Missing expected account")
    if str(payload.get("dhanClientId", "")) != expected_client_id:
        raise ValueError("Dhan account mismatch")
    token = payload.get("accessToken")
    if not isinstance(token, str) or not token or token != token.strip() or any(ch in token for ch in "\r\n"):
        raise ValueError("Invalid Dhan access token")
    raw_expiry = payload.get("expiryTime")
    if not isinstance(raw_expiry, str) or not raw_expiry:
        raise ValueError("Missing Dhan expiry")
    try:
        expiry = datetime.fromisoformat(raw_expiry.replace("Z", "+00:00"))
    except ValueError:
        raise ValueError("Invalid Dhan expiry") from None
    if expiry.tzinfo is None:
        raise ValueError("Ambiguous Dhan expiry timezone")
    now = now or datetime.now(timezone.utc)
    if expiry.astimezone(timezone.utc) <= now.astimezone(timezone.utc):
        raise ValueError("Expired Dhan consent token")
    return token, expiry.astimezone(timezone.utc)
