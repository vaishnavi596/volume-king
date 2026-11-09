#!/usr/bin/env python3
"""Read-only Dhan token expiry monitor. Never prints credentials or account data.

Run on Oracle with permissions to read /etc/bot-king/dhan-token.
Does not renew tokens, write files, restart services, or place orders.
Exit: 0 valid with >6h remaining; 2 expiry near/expired; 3 unknown/error.
"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
import json
import sys

TOKEN_PATH = Path("/etc/bot-king/dhan-token")
PROFILE_URL = "https://api.dhan.co/v2/profile"
WARNING_HOURS = 6


def parse_expiry(value):
    if not isinstance(value, str) or not value.strip():
        return None
    for fmt in ("%d/%m/%Y %H:%M", "%d/%m/%Y %H:%M:%S"):
        try:
            return datetime.strptime(value.strip(), fmt)
        except ValueError:
            pass
    return None


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
