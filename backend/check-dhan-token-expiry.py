#!/usr/bin/env python3
"""Read-only Dhan token expiry monitor. Never prints credentials or account data.

Run on Oracle with permissions to read /etc/bot-king/dhan-token.
Does not renew tokens, write files, restart services, or place orders.
Exit: 0 accepted and not expired; 2 rejected/expired; 3 unknown/error.
"""
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import sys

TOKEN_PATH = Path("/etc/bot-king/dhan-token")
PROFILE_URL = "https://api.dhan.co/v2/profile"


def parse_expiry(value):
    if not isinstance(value, str) or not value.strip():
        return None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return None


def expiry_alert(expiry, now, timezone_name, warning_seconds=21600):
    """Compute a warning only with an explicitly configured IANA timezone."""
    tz = ZoneInfo(timezone_name)
    remaining = (expiry.replace(tzinfo=tz) - now.astimezone(timezone.utc)).total_seconds()
    return max(0, int(remaining // 3600)), remaining <= warning_seconds


def expiry_assessment(expiry, timezone_name, now=None):
    """Classify expiry only with an explicitly verified IANA timezone.

    Returns (status, hours_remaining); status is expired, warning or healthy.
    """
    tz = ZoneInfo(timezone_name)
    now = now if now is not None else datetime.now(timezone.utc)
    remaining = (expiry.replace(tzinfo=tz) - now).total_seconds()
    if remaining <= 0:
        return "expired", 0
    if remaining <= 6 * 3600:
        return "warning", int(remaining // 3600)
    return "healthy", int(remaining // 3600)


def main():
    try:
        token = TOKEN_PATH.read_text(encoding="utf-8").strip()
        if not token:
            print("DHAN_TOKEN_STATUS=missing")
            return 3
        req = Request(PROFILE_URL, headers={"access-token": token, "Accept": "application/json"})
        with urlopen(req, timeout=12) as response:
            if response.status != 200:
                print("DHAN_TOKEN_STATUS=profile_unavailable")
                return 3
            raw = response.read(65537)
        if len(raw) > 65536:
            print("DHAN_TOKEN_STATUS=invalid_response")
            return 3
        data = json.loads(raw)
        if not isinstance(data, dict):
            print("DHAN_TOKEN_STATUS=invalid_response")
            return 3
        expiry = parse_expiry(data.get("tokenValidity"))
        if expiry is None:
            print("DHAN_TOKEN_STATUS=expiry_unknown")
            return 3
        # Dhan's profile string does not carry an offset. Never assume it is UTC.
        # Report the provider's expiry clock and ask for a verified timezone before scheduling.
        print("DHAN_TOKEN_STATUS=accepted")
        print("DHAN_TOKEN_EXPIRY_PROVIDER_LOCAL=" + expiry.strftime("%Y-%m-%d %H:%M"))
        configured_tz = os.environ.get("DHAN_PROFILE_TIMEZONE", "").strip()
        if configured_tz:
            try:
                status, hours_left = expiry_assessment(expiry, configured_tz)
                print("DHAN_EXPIRY_TIMEZONE=configured:" + configured_tz)
                print("DHAN_TOKEN_HOURS_REMAINING=" + str(hours_left))
                print("DHAN_TOKEN_EXPIRY_STATE=" + status)
                print("DHAN_TOKEN_EXPIRY_ALERT=" + ("yes" if status != "healthy" else "no"))
                if status == "expired":
                    print("DHAN_AUTO_RENEWAL=not_enabled")
                    return 2
            except (KeyError, ValueError):
                print("DHAN_EXPIRY_TIMEZONE=invalid_configuration")
                return 3
        else:
            print("DHAN_EXPIRY_TIMEZONE=unverified")
        print("DHAN_AUTO_RENEWAL=not_enabled")
        return 0
    except HTTPError as exc:
        print("DHAN_TOKEN_STATUS=" + ("rejected" if exc.code in (401, 403) else "profile_http_error"))
        return 2 if exc.code in (401, 403) else 3
    except (OSError, URLError, TimeoutError, ValueError, UnicodeError):
        print("DHAN_TOKEN_STATUS=check_failed")
        return 3


if __name__ == "__main__":
    sys.exit(main())
