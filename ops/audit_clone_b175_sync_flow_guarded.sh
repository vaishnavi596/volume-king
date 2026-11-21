#!/usr/bin/env bash
# B175: one-shot classified sync-wrapper flow and token provenance audit.
# No contents of private scripts, tokens, environ or service arguments printed.
set -Eeuo pipefail
sudo -n /usr/bin/python3 - <<'PY'
import os,re,stat,subprocess,shlex,hashlib
from pathlib import Path
from datetime import datetime,timezone

print("=== B175 TOKEN SYNC DECISION GATE ===")
P=Path("/usr/local/libexec/botking-clone-v2-dhan-sync")
def show(*args):
    p=subprocess.run(args,capture_output=True,text=True,timeout=10)
    return p.stdout.strip() if p.returncode==0 else ""
try:
    s=P.lstat()
    if not stat.S_ISREG(s.st_mode) or s.st_size>100000 or s.st_uid!=0:
        print("WRAPPER=UNTRUSTED_FILE"); raise SystemExit(0)
    lines=P.read_text(encoding="utf-8",errors="replace").splitlines()
except (OSError,UnicodeError):
    print("WRAPPER=UNREADABLE");raise SystemExit(0)
print("WRAPPER=READABLE_ROOT_OWNED")
print("WRAPPER_LINE_COUNT=",len(lines))
# Operator sees control-flow categories only; no variables, paths, filenames, or values.
for i,line in enumerate(lines,1):
    t=line.strip()
    if not t or t.startswith("#"): typ="COMMENT_OR_BLANK"
    elif re.search(r"\b(cp|install|rsync)\b",t): typ="COPY_STEP"
    elif re.search(r"\b(cmp|diff|sha256sum)\b",t): typ="COMPARE_STEP"
    elif re.search(r"\b(exit|return)\b",t): typ="EXIT_STEP"
    elif re.search(r"\b(test|stat)\b|\[\[?",t): typ="GUARD_STEP"
    elif re.search(r"\b(curl|wget|python3?|bash|sh)\b",t): typ="DELEGATE_OR_EXTERNAL_STEP"
    elif "=" in t: typ="VARIABLE_ASSIGNMENT"
    else: typ="OTHER_STEP"
    print("WRAPPER_LINE_%02d=%s"%(i,typ))
print("SYNC_LATEST_RESULT=",show("systemctl","show","botking-clone-v2-dhan-sync.service","-p","Result","--value") or "UNKNOWN")
print("SYNC_LATEST_EXIT=",show("systemctl","show","botking-clone-v2-dhan-sync.service","-p","ExecMainStatus","--value") or "UNKNOWN")
print("SYNC_LATEST_START=",show("systemctl","show","botking-clone-v2-dhan-sync.service","-p","ExecMainStartTimestamp","--value") or "UNKNOWN")
# Token path from running service: output only its metadata.
try:
    pid=int(show("systemctl","show","botking-clone-v2.service","-p","MainPID","--value"))
    entry=next((e.split(b"=",1)[1] for e in Path("/proc/%d/environ"%pid).read_bytes().split(b"\0")
        if e.startswith(b"BOTKING_CLONE_DHAN_TOKEN_FILE=")),None)
    if entry is None:print("TARGET=NOT_CONFIGURED")
    else:
        p=Path(os.fsdecode(entry))
        if not str(p).startswith("/home/opc/") or p.is_symlink() or not p.is_file():
            print("TARGET=BLOCKED_OR_MISSING")
        else:
            st=p.stat()
            print("TARGET=EXISTS")
            print("TARGET_PERMISSIONS=",oct(stat.S_IMODE(st.st_mode)))
            print("TARGET_MTIME_UTC=",datetime.fromtimestamp(st.st_mtime,timezone.utc).isoformat())
            print("TARGET_AGE_HOURS=",round((datetime.now(timezone.utc).timestamp()-st.st_mtime)/3600,2))
except (OSError,ValueError,UnicodeError,StopIteration):
    print("TARGET=METADATA_UNAVAILABLE")
# Nothing changes; a safe token source and entitlement cannot be verified from
# wrapper keyword scans. Never perform conditional token copies blindly.
print("TOKEN_RENEWAL_PROVEN=NO")
print("AUTOMATIC_TOKEN_REPLACEMENT=BLOCKED_UNTIL_SOURCE_AND_AUTH_VERIFIED")
for unit,label in (("bot-king.service","V1"),("botking-clone-v2.service","CLONE")):
    print(label+"_ACTIVE=",show("systemctl","is-active",unit) or "UNKNOWN")
print("NO_TOKEN_CONTENT_READ=YES")
print("NO_DHAN_REQUESTS_SENT=YES")
print("NO_RUNTIME_CHANGES=YES")
print("=== B175 COMPLETE ===")
PY
