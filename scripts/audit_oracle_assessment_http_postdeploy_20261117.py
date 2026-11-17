#!/usr/bin/env python3
"""Read-only, local-only post-deploy assessment HTTP contract audit. No Dhan calls."""
import ast
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import urllib.request
import urllib.error

root=pathlib.Path("/opt/bot-king-server")
expected={
"assessment_state.py":"ea2db1787be5cddc1ff2235db6592c7858519fc97b18d8c65c011ef9c7a3e3d2",
"assessment_api.py":"f421292725adadd825cbfa2a2a14f358aa6d07f29e3d71c0aa073d4b2827a2a5",
"server.py":"c9ee8a8d1baa8ebea8efc41d3ee4c6b42aea48f4add65ab79b9518a9fcb27bac",
}
checks={}
for name,sha in expected.items():
    p=root/name
    if not p.is_file() or p.is_symlink() or hashlib.sha256(p.read_bytes()).hexdigest()!=sha:
        raise SystemExit("HOLD: deployed source mismatch "+name)
    ast.parse(p.read_text())
checks["exact_deployed_source"]="PASS"

def read_key_without_display():
    # Read local protected service config via root, not shell expansion or output.
    # Never print even key names or value; don't copy them into a report file.
    code=r"""import pathlib,os,re
p=pathlib.Path('/etc/bot-king/server.env')
if not p.is_file():raise SystemExit(3)
env={}
for line in p.read_text().splitlines():
 line=line.strip()
 if not line or line.startswith('#') or '=' not in line:continue
 k,v=line.split('=',1); k=k.strip();v=v.strip()
 if v.startswith(('"',"'")) and v.endswith(v[0]):v=v[1:-1]
 env[k]=v
preferred=['BOTKING_SERVER_PAIRING_KEY','BOTKING_PAIRING_KEY','BOT_KING_PAIRING_KEY','BOTKING_SERVER_KEY','BOT_KING_SERVER_KEY','BOTKING_API_KEY','BOTKING_KEY']
names=[k for k in preferred if env.get(k)]
if len(names)!=1:
 names=[k for k,v in env.items() if v and (('PAIR' in k.upper() and 'KEY' in k.upper()) or ('SERVER' in k.upper() and 'KEY' in k.upper()))]
if len(names)!=1:raise SystemExit(4)
print(env[names[0]],end='')
"""
    cp=subprocess.run(["sudo","-n","python3","-c",code],capture_output=True,text=True,timeout=8)
    if cp.returncode!=0 or not cp.stdout.strip():
        return None
    return cp.stdout
key=read_key_without_display()
def req(path,secret=None):
    headers={"User-Agent":"BOTKING-local-post-deploy-audit/1"}
    if secret is not None: headers["X-BotKing-Key"]=secret
    request=urllib.request.Request("http://127.0.0.1:8000"+path,headers=headers)
    try:
        with urllib.request.urlopen(request,timeout=5) as resp:
            status=resp.status; payload=resp.read(256000)
    except urllib.error.HTTPError as e:
        status=e.code;payload=e.read(256000)
    try:parsed=json.loads(payload)
    except Exception:parsed={}
    return status,parsed
status,_=req("/health")
checks["health_200"]="PASS" if status==200 else "FAIL"
status,_=req("/v2/assessment/NIFTY")
checks["missing_auth_denied"]="PASS" if status==403 else "FAIL"
if key is None:
    checks["authenticated_key_resolution"]="BLOCKED"
else:
    checks["authenticated_key_resolution"]="PASS"
    status,_=req("/v2/assessment/NIFTY","wrong-key-for-negative-test")
    checks["invalid_auth_denied"]="PASS" if status==403 else "FAIL"
    status,unqualified=req("/v2/assessment/NIFTY",key)
    checks["authorized_unqualified_http_200"]="PASS" if status==200 else "FAIL"
    if status==200:
        filters=unqualified.get("assessment_filters",unqualified.get("filters",{}))
        if isinstance(filters,dict):
            present=set(filters)
        elif isinstance(filters,list):
            present={x.get("id") for x in filters if isinstance(x,dict)}
        else: present=set()
        required={"oi_support","oi_resistance","max_pain","pcr","candle_trend"}
        checks["five_filter_response_shape"]="PASS" if required<=present else "INSPECT"
        factor=unqualified.get("factors",{})
        checks["four_factor_response_shape"]="PASS" if isinstance(factor,dict) and {"news","futures","options","candle"}<=set(factor) else "INSPECT"
        checks["unqualified_no_false_candle_options"]="PASS" if all(
            not (isinstance(x,dict) and x.get("status")=="available")
            for x in (filters.values() if isinstance(filters,dict) else (filters if isinstance(filters,list) else []))
            if isinstance(x,dict) and x.get("id") in ("oi_support","oi_resistance","max_pain","pcr","candle_trend")
        ) else "INSPECT"
    for name,path,wanted in [
        ("authenticated_1m","/v2/assessment/NIFTY?timeframe=1m",200),
        ("authenticated_3m","/v2/assessment/NIFTY?timeframe=3m",200),
        ("invalid_timeframe_422","/v2/assessment/NIFTY?timeframe=2m",422),
        ("invalid_expiry_422","/v2/assessment/NIFTY?expiry=bad-date",422),
    ]:
        s,_=req(path,key);checks[name]="PASS" if s==wanted else "FAIL"
summary={k:sum(v==k for v in checks.values()) for k in ("PASS","FAIL","INSPECT","BLOCKED")}
print(json.dumps({"audit":"BOT_KING_POST_DEPLOY_ONE_SHOT_HTTP","checks":checks,"summary":summary,"local_http_only":True,"secret_printed":False,"dhan_routes_called":False,"production_changed":False,"server_restarted":False,"orders_sent":0,"live_market_data_verified":False,"apk_built":False},indent=2,sort_keys=True))
if summary["FAIL"]:raise SystemExit(2)
