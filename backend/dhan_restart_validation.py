"""Fail-closed restart validation of a persisted Dhan token.

Offline reusable policy: the caller supplies a Dhan profile lookup function.
No network is performed here, no renewal, and no token is logged. A stored
token is only a candidate until Dhan confirms the expected account and a
timezone-aware future expiry. Do not treat file presence as authentication.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

try:
    from .dhan_token_storage import read_persisted_token
except ImportError:
    from dhan_token_storage import read_persisted_token


def verify_persisted_session(token_path, expected_client_id, profile_lookup, now=None, provider_timezone=None):
    """Return validated token and UTC expiry or raise ValueError.

    profile_lookup(token) must return Dhan profile fields including dhanClientId
    and tokenValidity. Any failed network request must propagate as failure;
    callers must not silently downgrade to file-presence-based success.
    """
    if not isinstance(expected_client_id, str) or not expected_client_id:
        raise ValueError("Expected Dhan account missing")
    token = read_persisted_token(token_path)
    profile = profile_lookup(token)
    if not isinstance(profile, dict):
        raise ValueError("Invalid Dhan profile")
    if str(profile.get("dhanClientId", "")) != expected_client_id:
        raise ValueError("Dhan profile account mismatch")
    raw = profile.get("tokenValidity")
    if not isinstance(raw, str) or not raw:
        raise ValueError("Dhan profile expiry missing")
    try:
        expiry = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        expiry = None
    if expiry is None:
        for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S"):
            try:
                expiry = datetime.strptime(raw, fmt)
                break
            except ValueError:
                continue
    if expiry is None:
        raise ValueError("Invalid Dhan profile expiry")
    if expiry.tzinfo is None:
        if not provider_timezone:
            raise ValueError("Dhan profile expiry timezone unverified")
        try:
            expiry = expiry.replace(tzinfo=ZoneInfo(provider_timezone))
        except (KeyError, ValueError):
            raise ValueError("Invalid verified Dhan timezone") from None
    current = now if now is not None else datetime.now(timezone.utc)
    if current.tzinfo is None:
        raise ValueError("Current time must have timezone")
    expiry = expiry.astimezone(timezone.utc)
    if expiry <= current.astimezone(timezone.utc):
        raise ValueError("Dhan token expired")
    return token, expiry


def verify_persisted_session_with_dhan(token_path, expected_client_id, now=None, provider_timezone=None, profile_lookup=None):
    """Explicit read-only Dhan profile verification; never renew or write tokens.

    Network adapter is injected for deterministic offline tests. The caller
    must opt in to using this function; it is not wired into production.
    """
    if profile_lookup is None:
        try:
            from .dhan_profile_lookup import fetch_dhan_profile
        except ImportError:
            from dhan_profile_lookup import fetch_dhan_profile
        profile_lookup = fetch_dhan_profile
    return verify_persisted_session(
        token_path, expected_client_id, profile_lookup,
        now=now, provider_timezone=provider_timezone,
    )
