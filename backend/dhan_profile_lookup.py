"""Bounded read-only Dhan profile lookup for explicitly authorized verification.

This module is not wired into the production server. Never print token or
response body; no renewal, file changes or trading requests.
"""
import json
from urllib.request import Request, urlopen

PROFILE_URL = "https://api.dhan.co/v2/profile"


def fetch_dhan_profile(token, opener=urlopen):
    if not isinstance(token, str) or not token or token != token.strip() or "\n" in token or "\r" in token:
        raise ValueError("Invalid Dhan token")
    request = Request(PROFILE_URL, headers={"access-token": token, "Accept": "application/json"}, method="GET")
    with opener(request, timeout=12) as response:
        if response.status != 200:
            raise ValueError("Dhan profile HTTP status not accepted")
        raw = response.read(65537)
    if len(raw) > 65536:
        raise ValueError("Dhan profile response too large")
    try:
        profile = json.loads(raw)
    except (ValueError, UnicodeError):
        raise ValueError("Invalid Dhan profile response") from None
    if not isinstance(profile, dict):
        raise ValueError("Invalid Dhan profile response")
    return profile
