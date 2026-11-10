"""Strict, offline parsing of Dhan profile token validity timestamps.

Dhan profile examples use DD/MM/YYYY HH:MM in Asia/Kolkata. Reject missing,
malformed or already-expired values; never guess a 24-hour expiry.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")


def parse_profile_expiry(value, now=None):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Dhan profile tokenValidity missing")
    try:
        parsed = datetime.strptime(value.strip(), "%d/%m/%Y %H:%M")
    except ValueError:
        raise ValueError("Unsupported Dhan tokenValidity format") from None
    parsed = parsed.replace(tzinfo=IST)
    current = datetime.now(timezone.utc) if now is None else now
    if not isinstance(current, datetime) or current.tzinfo is None:
        raise ValueError("Current time must be timezone-aware")
    if parsed.astimezone(timezone.utc) <= current.astimezone(timezone.utc):
        raise ValueError("Dhan tokenValidity is expired")
    return parsed.astimezone(timezone.utc).isoformat()
