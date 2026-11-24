#!/usr/bin/env python3
"""BOT KING V3 single-pass root-cause audit. Read-only, ONE Dhan quote request.
No raw broker JSON, secrets, prices, IPs, personal details, or config values printed.
Does not alter services, callbacks, files, or V1. Requires opc on Oracle.
"""
import collections
import hashlib
import json
import math
import os
import pathlib
import re
import stat
import subprocess
import sys
import urllib.error
import urllib.request

ROOT=pathlib.Path("/home/opc/botking-clone-v2-runtime")
EXPECTED_NEW="3fb23267ce76a73d241d776ca32a0e51f3052985"
EXPECTED_OLD="49d8d5cdd90da4c768367d9258f00414f9027291"
SYMBOLS={"NIFTY":13,"BANKNIFTY":25,"SENSEX":51}
def emit(k,v):
    print(str(k)+"="+str(v),flush=True)
def command(args,timeout=7):
    try:
        p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,
                         text=True,timeout=timeout)
        return p.stdout.strip() if p.returncode==0 else ""
    except (OSError,subprocess.TimeoutExpired):
        return ""
def health(url):
    x=command(["curl","--noproxy","*","--silent","--max-time","4",
               "--output","/dev/null","--write-out","%{http_code}",url])
    return x if x in ("200","403","404","429","502","503") else "UNAVAILABLE"
def blob(path):
    data=path.read_bytes()
    return hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
def proc_env():
    pid=command(["systemctl","show","botking-clone-v2.service","-p","MainPID","--value"])
    if not pid.isdecimal() or int(pid)<2:
        raise RuntimeError("CLONE_PID_UNAVAILABLE")
    raw=pathlib.Path("/proc/"+pid+"/environ").read_bytes()
    out={}
    for item in raw.split(b"\x00"):
        if b"=" not in item: continue
        k,v=item.split(b"=",1)
        if k in (b"DHAN_CLIENT_ID",b"BOTKING_CLONE_DHAN_TOKEN_FILE"):
            out[k.decode()]=v.decode("utf-8")
    return out
def quote_audit():
    try:
        env=proc_env()
        client=env.get("DHAN_CLIENT_ID","").strip()
        path_text=env.get("BOTKING_CLONE_DHAN_TOKEN_FILE","")
        if not client or not path_text.startswith("/home/opc/"):
            return "CREDENTIAL_CONFIG_MISSING"
        path=pathlib.Path(path_text)
        if (not path.is_absolute() or ".." in path.parts or path.is_symlink()
            or not path.is_file() or stat.S_IMODE(path.stat().st_mode)&0o077):
            return "PRIVATE_TOKEN_PATH_INVALID"
        token=path.read_text(encoding="utf-8").strip()
        if not token: return "TOKEN_EMPTY"
        sys.path.insert(0,str(ROOT))
        from dhan_feed import direct_dhan_https_opener
        payload=json.dumps({"IDX_I":[13,25,51],"NSE_EQ":[2885]}).encode("utf-8")
        req=urllib.request.Request("https://api.dhan.co/v2/marketfeed/ltp",
            data=payload,headers={"Accept":"application/json",
            "Content-Type":"application/json","client-id":client,
            "access-token":token},method="POST")
        try:
            with direct_dhan_https_opener().open(req,timeout=12) as f:
                raw=f.read(100001)
            if len(raw)>100000: return "OVERSIZED_RESPONSE"
            reply=json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as exc:
            return ("HTTP_AUTH" if exc.code in (401,403) else
                    "HTTP_RATE_LIMIT" if exc.code==429 else
                    "HTTP_5XX" if 500<=exc.code<600 else "HTTP_4XX")
        except (urllib.error.URLError,TimeoutError,ValueError,UnicodeError):
            return "TRANSPORT_OR_PAYLOAD"
        finally:
            del token
        if not isinstance(reply,dict): return "BAD_ROOT"
        emit("DHAN_STATUS_SUCCESS",reply.get("status")=="success")
        remarks=reply.get("remarks")
        emit("DHAN_REMARKS_PRESENT",remarks is not None)
        # Do not print any raw provider-controlled error codes or body fields.
        emit("DHAN_ERROR_CODE_PRESENT",reply.get("errorCode") is not None or
             isinstance(remarks,dict) and any(k in remarks for k in ("error_code","errorCode")))
        data=reply.get("data")
        if not isinstance(data,dict): return "BAD_DATA_ENVELOPE"
        emit("DHAN_DATA_EMPTY",not bool(data))
        good=0
        for segment,items in (("IDX_I",SYMBOLS),("NSE_EQ",{"RELIANCE":2885})):
            rows=data.get(segment)
            emit(segment+"_SEGMENT", "DICT" if isinstance(rows,dict) else
                 "OTHER" if segment in data else "ABSENT")
            emit(segment+"_ROW_COUNT_BUCKET",
                 "ABSENT" if not isinstance(rows,dict) else
                 "ZERO" if not rows else "ONE" if len(rows)==1 else "MULTIPLE")
            for symbol,sid in items.items():
                row=rows.get(str(sid)) if isinstance(rows,dict) else None
                price=row.get("last_price") if isinstance(row,dict) else None
                valid=(type(price) in (int,float) and math.isfinite(price) and price>0)
                good+=bool(valid)
                emit("QUOTE_"+symbol,
                     "VALID_UNSTAMPED" if valid else
                     "MISSING_ID" if not isinstance(row,dict) else "INVALID_PRICE")
        emit("VALID_QUOTE_COUNT",str(good)+"/4")
        return "USABLE_DATA" if good else "SUCCESS_BUT_NO_VALIDATED_QUOTES"
    except (OSError,ValueError,ImportError,RuntimeError):
        return "PREFLIGHT_UNAVAILABLE"
def main():
    emit("TEST","V3_SINGLE_PASS_ROOT_CAUSE_20261124")
    emit("MODE","READ_ONLY_ONE_DHAN_LTP_REQUEST")
    if os.geteuid()==0 or os.environ.get("USER")!="opc":
        emit("AUDIT_RESULT","BLOCKED_NOT_OPC")
        return 4
    for tag,unit in (("V1","bot-king.service"),("CLONE","botking-clone-v2.service"),
                     ("NGINX","nginx.service"),("TOKEN_TIMER","botking-clone-v2-dhan-sync.timer")):
        state=command(["systemctl","is-active",unit])
        emit(tag+"_SERVICE",state if state in ("active","inactive","failed") else "UNKNOWN")
    emit("V1_HEALTH_HTTP",health("http://127.0.0.1:8000/health"))
    emit("CLONE_HEALTH_HTTP",health("http://127.0.0.1:8002/clone-v2/health"))
    try:
        h=blob(ROOT/"clone_v2_gateway.py")
        emit("CLONE_PATCH_INSTALLED",h==EXPECTED_NEW)
        emit("CLONE_OLD_VERSION",h==EXPECTED_OLD)
    except OSError:
        emit("CLONE_PATCH_INSTALLED","UNKNOWN")
    try:
        s=(ROOT/"clone_v2_gateway.py").read_text(encoding="utf-8")
        emit("IDX_I_REGISTRY_PRESENT",all(x in s for x in
             ('"NIFTY": ("IDX_I", 13)','"BANKNIFTY": ("IDX_I", 25)','"SENSEX": ("IDX_I", 51)')))
        emit("QUOTE_STAGE_HEADERS_PRESENT",s.count("X-BotKing-Quote-Failure-Stage")>=3)
        emit("EMPTY_QUOTES_GATE_PRESENT",'No validated clone quotes' in s)
    except (OSError,UnicodeError):
        emit("SOURCE_CONTRACT","UNKNOWN")
    # No SSK: verifies the boundary, MUST NOT call broker.
    test=command(["curl","--noproxy","*","--silent","--max-time","5",
        "--output","/dev/null","--write-out","%{http_code}","-X","POST",
        "-H","Content-Type: application/json",
        "--data",'{"symbols":["NIFTY"]}',
        "http://127.0.0.1:8002/clone-v2/market/quotes"])
    emit("CLONE_UNAUTH_QUOTE_HTTP",test if test in ("403","200","502","503","000") else "OTHER")
    journal=command(["sudo","-n","journalctl","-u","botking-clone-v2.service",
                     "--since","24 hours ago","--no-pager","-o","cat"],timeout=12)
    pat=re.compile(r"clone_market_diagnostic route=(quotes|candles) symbol=(NIFTY|BANKNIFTY|SENSEX) stage=(provider|mapping|cooldown|validation|shape) category=([a-z0-9_]+)")
    counts=collections.Counter((m.group(1),m.group(3),m.group(4))
             for line in journal.splitlines() if (m:=pat.search(line)))
    for (route,stage,reason),count in sorted(counts.items()):
        emit("LOG_"+route+"_"+stage+"_"+reason,count)
    emit("LOG_MATCHING_COUNT",sum(counts.values()) if journal else "UNAVAILABLE")
    if (health("http://127.0.0.1:8002/clone-v2/health")!="200"):
        emit("PROVIDER_RESULT","SKIPPED_CLONE_UNHEALTHY")
        return 3
    emit("PROVIDER_RESULT",quote_audit())
    emit("SOURCE_LIVE_VERIFIED","NO")
    emit("ORDERS_SENT",0)
    return 0
if __name__=="__main__":
    sys.exit(main())
