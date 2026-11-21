#!/usr/bin/env bash
# B174 consolidated, Clone-only, zero-provider-request diagnosis.
# Never print any token, paths from sync wrapper, environment, or raw journal.
set -Eeuo pipefail
umask 077
echo "=== B174 CONSOLIDATED CLONE ROOT AUDIT ==="
sudo -n /usr/bin/python3 - <<'PY'
from pathlib import Path
from datetime import datetime,timezone
import subprocess,re,stat,hashlib,collections,os

def run(*args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,text=True,timeout=25)
    return p.stdout.strip() if p.returncode==0 else ""
def prop(unit,name):
    return run("systemctl","show",unit,"-p",name,"--value")
def fileblob(p):
    d=p.read_bytes()
    return hashlib.sha1(b"blob "+str(len(d)).encode()+b"\0"+d).hexdigest()
def health(url):
    x=run("curl","--noproxy","*","--silent","--max-time","4","-o","/dev/null","-w","%{http_code}",url)
    return x if x in {"200","401","403","404","429","500","502","503"} else "NOT_200"
clone="botking-clone-v2.service";v1="bot-king.service"
sync="botking-clone-v2-dhan-sync.service";timer="botking-clone-v2-dhan-sync.timer"
print("V1_SERVICE=",prop(v1,"ActiveState") or "UNKNOWN")
print("CLONE_SERVICE=",prop(clone,"ActiveState") or "UNKNOWN")
print("SYNC_TIMER=",prop(timer,"ActiveState") or "UNKNOWN")
print("SYNC_RESULT=",prop(sync,"Result") or "UNKNOWN")
print("SYNC_EXEC_STATUS=",prop(sync,"ExecMainStatus") or "UNKNOWN")
print("SYNC_LAST_START=",prop(sync,"ExecMainStartTimestamp") or "UNKNOWN")
print("SYNC_LAST_END=",prop(sync,"ExecMainExitTimestamp") or "UNKNOWN")
print("V1_HEALTH_HTTP=",health("http://127.0.0.1:8000/health"))
print("CLONE_HEALTH_HTTP=",health("http://127.0.0.1:8002/clone-v2/health"))
root=Path("/home/opc/botking-clone-v2-runtime")
expected={"clone_v2_gateway.py":"10d2bf6f2265bfbca8a195cb742691ff541f7baf",
          "dhan_feed.py":"63cf68124fc1449f6ce9fc1dc8359cadf038919d"}
for name,sha in expected.items():
    f=root/name
    try:
        ok=f.is_file() and not f.is_symlink() and fileblob(f)==sha
        print("DEPLOYED_"+name.upper().replace(".","_")+"=", "EXPECTED" if ok else "DIFFERENT_OR_MISSING")
    except OSError:
        print("DEPLOYED_"+name.upper().replace(".","_")+"=UNREADABLE")
# Fixed path, no script body or wrapper arguments will be shown.
wrapper=Path("/usr/local/libexec/botking-clone-v2-dhan-sync")
try:
    st=wrapper.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_size>100000:
        print("SYNC_WRAPPER=BLOCKED_UNSAFE_FILE")
    else:
        src=wrapper.read_text(errors="replace")
        print("SYNC_WRAPPER=READABLE")
        print("SYNC_WRAPPER_LINES=",len(src.splitlines()))
        # Feature names only. Never echo lines, tokens, path values or secret-bearing strings.
        # More precise than B171-B173 but still only a heuristic.
        patterns={"COPY_COMMAND":r"\b(?:cp|install|rsync|dd)\b",
                  "COMPARISON_COMMAND":r"\b(?:cmp|diff|sha256sum|md5sum)\b",
                  "FILE_UPDATE_COMMAND":r"\b(?:mv|touch|tee|truncate)\b",
                  "SHELL_TEST_OR_RETURN":r"\b(?:test|exit|return)\b|\[\[?",
                  "DIRECT_INTERPRETER":r"\b(?:bash|python3?|node)\b",
                  "NETWORK_COMMAND":r"\b(?:curl|wget)\b",
                  "SOURCE_OR_DOT":r"\bsource\s+|(?:^|\n)\s*\.\s+",
                  "TOKEN_RENEWAL_LITERAL":r"renew|generate-consent|access.token"}
        for key,pat in patterns.items():
            print("WRAPPER_"+key+"=", "PRESENT" if re.search(pat,src,re.I) else "ABSENT")
except (OSError,UnicodeError):
    print("SYNC_WRAPPER=UNAVAILABLE")
# Process env: only a single exact variable; no value printed.
try:
    pid=int(prop(clone,"MainPID"))
    data=Path("/proc/%d/environ"%pid).read_bytes().split(b"\0")
    v=next((i.split(b"=",1)[1] for i in data if i.startswith(b"BOTKING_CLONE_DHAN_TOKEN_FILE=")),None)
    if v is None: print("CLONE_TOKEN_FILE=UNCONFIGURED")
    else:
        p=Path(os.fsdecode(v))
        if (not str(p).startswith("/home/opc/") or p.is_symlink() or not p.is_file()):
            print("CLONE_TOKEN_FILE=BLOCKED_OR_MISSING")
        else:
            st=p.stat()
            stamp=datetime.fromtimestamp(st.st_mtime,timezone.utc)
            print("CLONE_TOKEN_FILE=EXISTS")
            print("CLONE_TOKEN_MODE=",oct(stat.S_IMODE(st.st_mode)))
            print("CLONE_TOKEN_OWNER_MATCH_PROCESS=",str(st.st_uid==int(prop(clone,"UID"))) if prop(clone,"UID").isdigit() else "UNKNOWN")
            print("CLONE_TOKEN_MTIME_UTC=",stamp.isoformat())
            print("CLONE_TOKEN_AGE_HOURS=",round((datetime.now(timezone.utc)-stamp).total_seconds()/3600,2))
except (OSError,ValueError,UnicodeError,StopIteration):
    print("CLONE_TOKEN_FILE=METADATA_UNAVAILABLE")
# Print only tightly allowlisted diagnostics, no raw journal lines.
try:
    x=subprocess.run(["journalctl","-u",clone,"--since","60 minutes ago","--no-pager","-o","cat"],
                     capture_output=True,text=True,timeout=25).stdout
    counts=collections.Counter()
    rg=re.compile(r"^clone_market_diagnostic route=(quotes|candles) symbol=(NIFTY|BANKNIFTY|SENSEX) stage=(provider|shape|mapping|validation|cooldown) category=(missing_segment|missing_security_id|invalid_price|invalid_shape|invalid_bars|rate_limited|auth_unavailable|upstream_error|upstream_http_4xx|upstream_http_5xx|upstream_transport|upstream_payload|upstream_rejection)$")
    for line in x.splitlines():
        m=rg.fullmatch(line.strip())
        if m: counts[m.groups()]+=1
    for (route,symbol,stage,category),n in sorted(counts.items()):
        print("DIAG_60M",route,symbol,stage,category,n)
    if not counts: print("DIAG_60M=NO_MATCHING_EVENTS")
except (OSError,subprocess.TimeoutExpired):
    print("DIAG_60M=UNAVAILABLE")
print("TOKEN_CONTENT_NOT_READ_OR_PRINTED=YES")
print("NO_BROKER_REQUESTS=YES")
print("SERVER_FILES_CHANGED=NO")
print("=== B174 COMPLETE ===")
PY
