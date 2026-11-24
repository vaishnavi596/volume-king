#!/usr/bin/env python3
"""Clone index OHLC fallback evidence. Explicit one Dhan read-only request; never output secrets."""
import os
import pathlib
import stat
import subprocess
import sys
import math
import json
import urllib.request
import urllib.error

ROOT = pathlib.Path("/home/opc/botking-clone-v2-runtime")
EXPECTED = {"NIFTY": 13, "BANKNIFTY": 25, "SENSEX": 51}

def show(key, val):
    print(f"{key}={val}", flush=True)

def service_settings():
    result = subprocess.run(["systemctl", "show", "botking-clone-v2.service",
                             "-p", "MainPID", "--value"], check=True,
                            capture_output=True, text=True, timeout=5)
    if not result.stdout.strip().isdecimal() or int(result.stdout.strip()) < 2:
        raise ValueError("SERVICE_PID_INVALID")
    pid = int(result.stdout.strip())
    raw = pathlib.Path(f"/proc/{pid}/environ").read_bytes()
    env = {}
    for item in raw.split(b"\x00"):
        if b"=" not in item:
            continue
        name, value = item.split(b"=", 1)
        if name in (b"DHAN_CLIENT_ID", b"BOTKING_CLONE_DHAN_TOKEN_FILE"):
            env[name.decode()] = value.decode("utf-8")
    return env

def classify(response):
    if not isinstance(response, dict):
        return "INVALID_TOP_LEVEL", {}
    if response.get("status") != "success" or not isinstance(response.get("data"), dict):
        return "INVALID_ENVELOPE", {}
    seg = response["data"].get("IDX_I")
    if not isinstance(seg, dict):
        return "IDX_I_MISSING", {}
    statuses = {}
    for name, sid in EXPECTED.items():
        value = seg.get(str(sid))
        if not isinstance(value, dict):
            statuses[name] = "MISSING_SECURITY_ID"
        else:
            price = value.get("last_price")
            statuses[name] = ("VALID_UNSTAMPED_LTP" if type(price) in (int, float)
                              and math.isfinite(price) and price > 0 else "INVALID_PRICE")
    return "SUCCESS_ENVELOPE", statuses

def main():
    show("TEST", "V3_CLONE_INDEX_OHLC_FALLBACK_EVIDENCE")
    show("SOURCE", "ONE_EXPLICIT_DHAN_LTP_BATCH")
    # Do not execute as root. Only opc service owner may read private credentials.
    if os.geteuid() == 0 or os.environ.get("USER") != "opc":
        raise ValueError("NOT_OPC")
    if not (ROOT / "dhan_feed.py").is_file():
        raise ValueError("CLONE_RUNTIME_MISSING")
    env = service_settings()
    client = env.get("DHAN_CLIENT_ID", "").strip()
    path_text = env.get("BOTKING_CLONE_DHAN_TOKEN_FILE", "")
    if not client or not path_text.startswith("/home/opc/"):
        raise ValueError("CREDENTIAL_CONFIG_UNAVAILABLE")
    path = pathlib.Path(path_text)
    if (not path.is_absolute() or ".." in path.parts or path.is_symlink()
            or not path.is_file() or stat.S_IMODE(path.stat().st_mode) & 0o077):
        raise ValueError("TOKEN_FILE_NOT_PRIVATE")
    token = path.read_text(encoding="utf-8").strip()
    if not token:
        raise ValueError("TOKEN_EMPTY")
    sys.path.insert(0, str(ROOT))
    from dhan_feed import direct_dhan_https_opener
    payload = json.dumps({"IDX_I": [13, 25, 51]}).encode("utf-8")
    request = urllib.request.Request(
        "https://api.dhan.co/v2/marketfeed/ohlc", data=payload,
        headers={"Content-Type": "application/json", "Accept": "application/json",
                 "client-id": client, "access-token": token}, method="POST")
    try:
        with direct_dhan_https_opener().open(request, timeout=12) as stream:
            raw = stream.read(100001)
        if len(raw) > 100000:
            show("PROVIDER_RESULT", "OVERSIZE_RESPONSE")
            return 2
        response = json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as exc:
        show("PROVIDER_RESULT", ("AUTH_UNAVAILABLE" if exc.code in (401, 403)
                                else "RATE_LIMIT" if exc.code == 429
                                else "UPSTREAM_HTTP_5XX" if 500 <= exc.code < 600
                                else "UPSTREAM_HTTP_4XX"))
        return 2
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError):
        show("PROVIDER_RESULT", "TRANSPORT_OR_PAYLOAD_ERROR")
        return 2
    finally:
        del token
    state, statuses = classify(response)
    show("RESPONSE_SHAPE", state)
    for name, result in statuses.items():
        show(name, result)
    valid = sum(status == "VALID_UNSTAMPED_LTP" for status in statuses.values())
    show("VALIDATED_INDICES", f"{valid}/3")
    show("EXCHANGE_TIMESTAMP_VERIFIED", "NO")
    show("LIVE_VOTES_ENABLED", "NO")
    return 0 if valid else 3

if __name__ == "__main__":
    try:
        result = main()
    except (OSError, ValueError, subprocess.SubprocessError, ImportError) as error:
        show("PREFLIGHT", type(error).__name__.upper())
        result = 4
    sys.exit(result)
