#!/usr/bin/env python3
"""T09 production cache-to-Assessment read-only probe; NEVER calls Dhan endpoints.

Only GET /health, /v2/candles/NIFTY/5, /v2/assessment/NIFTY?timeframe=5m.
A cached-candles hit may publish to Assessment without broker requests; it is
NOT proof of the newly installed POST /dhan/intraday producer.
"""
import ast
import hashlib
import json
import pathlib
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path("/opt/bot-king-server")
SOURCE_SHA = {
    "server.py": "9327e33a204e06affad383bd8af80ae0ed5f90bc79ee2b1410cadcb7fc5e12b5",
    "assessment_state.py": "ea2db1787be5cddc1ff2235db6592c7858519fc97b18d8c65c011ef9c7a3e3d2",
    "assessment_api.py": "f421292725adadd825cbfa2a2a14f358aa6d07f29e3d71c0aa073d4b2827a2a5",
}
ALLOWED_PATHS = frozenset(("/health", "/v2/candles/NIFTY/5",
                           "/v2/assessment/NIFTY?timeframe=5m"))
KEY_CODE = r"""
import pathlib,sys
p=pathlib.Path('/etc/bot-king/server.env')
if not p.is_file() or p.is_symlink():sys.exit(3)
env={}
for line in p.read_text().splitlines():
 line=line.strip()
 if not line or line.startswith('#') or '=' not in line:continue
 k,v=line.split('=',1);k=k.strip();v=v.strip()
 if len(v)>=2 and v[0] in ('"',"'") and v[-1]==v[0]:v=v[1:-1]
 env[k]=v
names=['BOTKING_SERVER_PAIRING_KEY','BOTKING_PAIRING_KEY','BOT_KING_PAIRING_KEY',
       'BOTKING_SERVER_KEY','BOT_KING_SERVER_KEY','BOTKING_API_KEY','BOTKING_KEY']
match=[k for k in names if env.get(k)]
if len(match)!=1:
 match=[k for k,v in env.items() if v and
        (('PAIR' in k.upper() and 'KEY' in k.upper()) or
         ('SERVER' in k.upper() and 'KEY' in k.upper()))]
if len(match)!=1:sys.exit(4)
sys.stdout.write(env[match[0]])
"""

def sha_preflight():
    for name, digest in SOURCE_SHA.items():
        p = ROOT/name
        if not p.is_file() or p.is_symlink():
            raise RuntimeError("SOURCE_MISSING_OR_SYMLINK_" + name)
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != digest:
            raise RuntimeError("SOURCE_SHA_DRIFT_" + name)
        ast.parse(raw.decode("utf-8"))

def resolve_key():
    cp = subprocess.run(["sudo", "-n", "python3", "-c", KEY_CODE],
                        capture_output=True, timeout=8)
    if cp.returncode or not cp.stdout:
        raise RuntimeError("AUTH_UNAVAILABLE")
    return cp.stdout.decode().strip()

def get(path, key):
    if path not in ALLOWED_PATHS:
        raise RuntimeError("NON_ALLOWLISTED_HTTP_ROUTE")
    headers = {"User-Agent": "BOTKING-T09-cache-only/1",
               "Accept": "application/json"}
    if path != "/health":
        headers["X-BotKing-Key"] = key
    req = urllib.request.Request("http://127.0.0.1:8000" + path,
                                 headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            status, raw = resp.status, resp.read(400000)
    except urllib.error.HTTPError as exc:
        status, raw = exc.code, exc.read(400000)
    try:
        obj = json.loads(raw)
    except (ValueError, UnicodeDecodeError):
        obj = {}
    return status, obj if isinstance(obj, dict) else {}

def evaluate(health, cached, assessment):
    hs, _ = health
    cs, c = cached
    astat, a = assessment
    bars = c.get("bars", [])
    count = len(bars) if isinstance(bars, list) else 0
    factors = a.get("factors")
    candle = factors.get("candle", {}) if isinstance(factors, dict) else {}
    result = {
        "health_200": hs == 200,
        "cached_http_200": cs == 200,
        "cached_source_dhan": c.get("source") == "dhan",
        "cached_history_present": count >= 2,
        "cached_historical_unverified": c.get("freshness") == "historical_unverified" if count else None,
        "assessment_http_200": astat == 200,
        "assessment_selector_5m": a.get("timeframe") == "5m",
        "assessment_signal_not_live": a.get("signal_eligible") is False,
    }
    if any(x is False for x in (result["health_200"], result["cached_http_200"],
                                  result["assessment_http_200"], result["assessment_signal_not_live"])):
        verdict = "HOLD_HTTP_OR_SAFETY"
    elif not result["cached_history_present"]:
        verdict = "NO_CACHED_HISTORY_NO_DHAN_REQUEST"
    elif not (result["cached_source_dhan"] and result["cached_historical_unverified"]
              and result["assessment_selector_5m"]):
        verdict = "HOLD_CONTRACT"
    else:
        verdict = "CACHE_AND_ASSESSMENT_HTTP_PASS_PUBLISH_CAUSALITY_UNPROVEN"
    return {"status": verdict, "checks": result, "cached_bar_count": count,
            "candle_factor_status": candle.get("status") if isinstance(candle, dict) else None,
            "production_changed": False, "server_restarted": False,
            "dhan_routes_called": False, "orders_sent": 0,
            "actual_intraday_post_proven": False, "credential_printed": False}

def main():
    report = {"audit": "T09_CACHE_ONLY_POSTDEPLOY_HTTP",
              "production_changed": False, "server_restarted": False,
              "dhan_routes_called": False, "orders_sent": 0,
              "actual_intraday_post_proven": False}
    try:
        sha_preflight()
        key = resolve_key()
        health = get("/health", key)
        cached = get("/v2/candles/NIFTY/5", key)
        assessment = get("/v2/assessment/NIFTY?timeframe=5m", key)
        report.update(evaluate(health, cached, assessment))
    except Exception as exc:
        report["status"] = "HOLD_NO_CHANGE"
        report["error_type"] = type(exc).__name__
        report["error_code"] = str(exc) if isinstance(exc, RuntimeError) else "UNEXPECTED"
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["status"] in (
        "CACHE_AND_ASSESSMENT_HTTP_PASS_PUBLISH_CAUSALITY_UNPROVEN",
        "NO_CACHED_HISTORY_NO_DHAN_REQUEST") else 2

if __name__ == "__main__":
    sys.exit(main())
