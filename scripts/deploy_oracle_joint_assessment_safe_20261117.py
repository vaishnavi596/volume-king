#!/usr/bin/env python3
"""Authorized one-shot Oracle joint assessment deployment. Atomic backup, rollback on failure."""
import ast
import contextlib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

ROOT=Path("/opt/bot-king-server")
BUNDLE=Path("/tmp/bk_oracle_joint_repair_po14ts41")
GENERATOR=Path("/tmp/bk_joint_generator_fixed.py")
EXPECTED_GENERATOR_BLOB="3cd32877b294497b8a232522403d3b0b6118ab75"
ORIGINAL={
    "server.py":"ef1f5cd971fd8129a1a704457b69014a37c7dc300178158f6b48dd91fd8d93a9",
    "assessment_api.py":"91c0fc7e3ef95a6bfb63b54ded0f56f1d429f465a11830442419472e87dee57b",
    "assessment_state.py":"b066d6d41cb0892f653e3fa18a49d3050627df34b9b8d732624f03aa40dfc8d4"
}
NAMES=("assessment_state.py","assessment_api.py","server.py")
SERVICE="bot-king.service"
backup=None
mutating=False
done=False

def sha(data):return hashlib.sha256(data).hexdigest()
def read_safe(p):
    if not p.is_file() or p.is_symlink():raise RuntimeError("HOLD: missing or symlink "+str(p))
    return p.read_bytes()
def cmd(*args):
    cp=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,timeout=40)
    if cp.returncode:raise RuntimeError("Command failed: "+" ".join(args[:3])+" (code "+str(cp.returncode)+")")
    return cp.stdout.strip()
def sudo(*args):
    return cmd("sudo","-n",*args)
def check_http(path,expected):
    request=Request("http://127.0.0.1:8000"+path,headers={"User-Agent":"BOTKING-safe-deploy-check/1"})
    try:
        with urlopen(request,timeout=3) as response:status=response.status
    except HTTPError as exc:status=exc.code
    except (URLError,TimeoutError) as exc:raise RuntimeError("Local endpoint unavailable "+path) from exc
    if status!=expected:raise RuntimeError("Unexpected HTTP "+str(status)+" for "+path+" (expected "+str(expected)+")")
    return status
def check_service():
    if sudo("systemctl","is-active",SERVICE)!="active":raise RuntimeError("Systemd service is not active")
    if check_http("/health",200)!=200:raise RuntimeError("Health check failed")
    # Missing protected pairing key MUST be denied even for a known mapped symbol.
    check_http("/v2/assessment/NIFTY",403)
def wait_health():
    error=None
    for _ in range(12):
        try:
            check_service()
            return
        except Exception as exc:
            error=exc
            time.sleep(1)
    raise RuntimeError("Post-restart health/auth check failed: "+str(error))
def install_from(path,name):
    target=ROOT/name
    tmp=ROOT/(name+".bk-deploy-pending")
    # Prevent unintended other-file overwrite and keep a root-owned 0644 destination.
    sudo("install","-o","root","-g","root","-m","0644",str(path),str(tmp))
    sudo("mv","-f",str(tmp),str(target))
def rollback():
    global backup
    if not backup:return
    for name in NAMES:install_from(backup/name,name)
    sudo("systemctl","restart",SERVICE)
    wait_health()
    print("ROLLBACK_COMPLETE=TRUE")
def main():
    global backup,mutating,done
    print("===== BOT KING AUTHORIZED JOINT DEPLOY =====",flush=True)
    # Exact original source version, preflight before the FIRST write.
    for name,expected in ORIGINAL.items():
        raw=read_safe(ROOT/name)
        if sha(raw)!=expected:raise RuntimeError("HOLD: current production source changed "+name)
        ast.parse(raw.decode())
    print("PRODUCTION_BASELINE_SHA PASS",flush=True)
    if cmd("systemctl","is-active",SERVICE)!="active":raise RuntimeError("HOLD: service inactive before deployment")
    check_service()
    sudo("true")
    if os.geteuid()==0:raise RuntimeError("HOLD: run as opc, not root")
    if not BUNDLE.is_dir() or BUNDLE.is_symlink():raise RuntimeError("HOLD: staged bundle missing")
    srcs={name:read_safe(BUNDLE/name) for name in NAMES}
    for name,raw in srcs.items():ast.parse(raw.decode())
    g=read_safe(GENERATOR)
    git_blob=hashlib.sha1(b"blob "+str(len(g)).encode()+b"\\0"+g).hexdigest()
    if git_blob!=EXPECTED_GENERATOR_BLOB:raise RuntimeError("HOLD: fixed generator SHA mismatch")
    # Deterministically re-generate from exact producer and compare every candidate's hash.
    import runpy
    out=io.StringIO()
    with contextlib.redirect_stdout(out):runpy.run_path(str(GENERATOR),run_name="__main__")
    regeneration=json.loads(out.getvalue())
    if regeneration.get("result")!="ORACLE_JOINT_REPAIR_BUNDLE_STAGED":
        raise RuntimeError("HOLD: generator failed")
    for name in NAMES:
        generated=read_safe(Path(regeneration["files"][name]["path"]))
        if sha(generated)!=sha(srcs[name]):raise RuntimeError("HOLD: previously tested bundle differs from regenerated fixed candidate: "+name)
    print("BUNDLE_REGENERATION_MATCH PASS",flush=True)
    # Confirm critical route ownership, not just Python syntax.
    server_tree=ast.parse(srcs["server.py"].decode())
    def only_fn(name):
        found=[n for n in ast.walk(server_tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
        if len(found)!=1:raise RuntimeError("HOLD: ambiguous function "+name)
        return found[0]
    helper=only_fn("_assessment_bars_completed")
    route=only_fn("cached_candles")
    if helper.decorator_list or len(route.decorator_list)!=1:
        raise RuntimeError("HOLD: FastAPI candle route lost decorator")
    dec=route.decorator_list[0]
    if not (isinstance(dec,ast.Call) and isinstance(dec.func,ast.Attribute) and dec.func.attr=="get"
        and isinstance(dec.func.value,ast.Name) and dec.func.value.id=="app"):
        raise RuntimeError("HOLD: candle decorator incorrect")
    print("FASTAPI_ROUTE_RETENTION PASS",flush=True)

    backup=Path.home()/"botking-deploy-backups"/("joint-assessment-"+datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ"))
    backup.mkdir(parents=True,mode=0o700,exist_ok=False)
    for name in NAMES:
        dest=backup/name
        dest.write_bytes(read_safe(ROOT/name))
        dest.chmod(0o600)
        if sha(dest.read_bytes())!=ORIGINAL[name]:raise RuntimeError("HOLD: backup checksum mismatch "+name)
    print("BACKUP_VERIFIED",str(backup),flush=True)

    mutating=True
    for name in NAMES:install_from(BUNDLE/name,name)
    for name in NAMES:
        if sha(read_safe(ROOT/name))!=sha(srcs[name]):raise RuntimeError("HOLD: deployed SHA mismatch "+name)
    sudo("systemctl","restart",SERVICE)
    wait_health()
    done=True
    print(json.dumps({"result":"DEPLOY_HEALTH_AUTH_PASS","backup":str(backup),
      "deployed_sha256":{name:sha(srcs[name]) for name in NAMES},
      "health_http":200,"unauth_assessment_http":403,
      "production_changed":True,"server_restarted":True,
      "authenticated_assessment_tested":False,"live_dhan_verified":False,
      "orders_sent":0,"apk_built":False},indent=2),flush=True)
if __name__=="__main__":
    try:main()
    except Exception as exc:
        print("DEPLOY_GATE_FAIL",type(exc).__name__,str(exc),flush=True)
        if mutating and not done:
            try:rollback()
            except Exception as rollback_error:
                print("CRITICAL_ROLLBACK_FAILED",type(rollback_error).__name__,str(rollback_error),flush=True)
        sys.exit(2)
