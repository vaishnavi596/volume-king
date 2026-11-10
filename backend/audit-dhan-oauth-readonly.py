"""Read-only, secret-safe Oracle diagnostic for BOT KING Dhan OAuth.

No OAuth consent generated, no token rotated, no secrets printed.
Run as root on the Oracle host. Exit status is nonzero for a definite mismatch.
"""
import json
import os
from pathlib import Path
import urllib.error
import urllib.request

ENV = Path("/etc/bot-king/server.env")
TOKEN = Path("/etc/bot-king/dhan-token")

def main():
    values = {}
    for raw in ENV.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip().removeprefix("export ").strip()] = value.strip().strip('"').strip("'")
    client = values.get("DHAN_CLIENT_ID", "")
    for key in ("DHAN_CLIENT_ID", "DHAN_API_KEY", "DHAN_API_SECRET"):
        print(key + ":", "PRESENT" if values.get(key) else "MISSING")
    if not client or not TOKEN.is_file():
        print("PROFILE ACCOUNT CHECK: BLOCKED (missing client or token)")
        return 2
    try:
        request = urllib.request.Request(
            "https://api.dhan.co/v2/profile",
            headers={"access-token": TOKEN.read_text(encoding="utf-8").strip()},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            profile = json.load(response)
        if not isinstance(profile, dict):
            print("PROFILE ACCOUNT CHECK: INVALID RESPONSE")
            return 2
        matches = str(profile.get("dhanClientId", "")).strip() == client
        print("PROFILE ACCOUNT MATCH:", "YES" if matches else "NO")
        print("PROFILE DATA PLAN:", "ACTIVE" if str(profile.get("dataPlan", "")).lower() == "active" else "NOT CONFIRMED")
        print("OAUTH APP KEY VALIDITY: NOT VERIFIED (requires consent exchange)")
        print("REGISTERED CALLBACK URL: VERIFY IN DHAN DEVELOPER PORTAL")
        return 0 if matches else 2
    except urllib.error.HTTPError as error:
        print("PROFILE HTTP STATUS:", error.code)
        return 2
    except (OSError, ValueError, urllib.error.URLError, json.JSONDecodeError) as error:
        print("PROFILE CHECK FAILED:", type(error).__name__)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
