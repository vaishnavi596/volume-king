#!/usr/bin/env bash
# BOT KING CLONE: finish ONLY existing Dhan OAuth callback Nginx handoff.
# Does not reinstall B3, alter tokens, stop V1, or affect unrelated routes.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]] || { echo "CALLBACK_BLOCKED=ROOT_REQUIRED"; exit 2; }
status() { curl -s -o /dev/null --connect-timeout 4 --max-time 12 -w '%{http_code}' "$@"; }
[[ "$(systemctl is-active botking-clone-v2.service)" == active ]] || { echo "CALLBACK_BLOCKED=CLONE_INACTIVE"; exit 2; }
[[ "$(status http://127.0.0.1:8002/clone-v2/health)" == 200 ]] || { echo "CALLBACK_BLOCKED=CLONE_HEALTH"; exit 2; }
[[ "$(status -X POST http://127.0.0.1:8002/clone-v2/dhan/start)" == 403 ]] || { echo "CALLBACK_BLOCKED=LOCAL_START"; exit 2; }
[[ "$(status http://127.0.0.1:8002/dhan/callback)" == 403 ]] || { echo "CALLBACK_BLOCKED=LOCAL_CALLBACK"; exit 2; }
nginx -t >/dev/null 2>&1 || { echo "CALLBACK_BLOCKED=NGINX_BASELINE"; exit 2; }
BACKUP_DIR="/etc/nginx/botking-clone-callback-backup-$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -m 0700 "$BACKUP_DIR"
# Python changes ONLY a unique exact callback location in a uniquely identified
# DuckDNS server block containing the Clone route. Existing proxy must be a
# literal loopback V1 (8000) or Clone (8002) upstream; anything else blocks.
if ! BACKUP_DIR="$BACKUP_DIR" python3 - <<'PY'
import os, re, shutil
from pathlib import Path
host="botkingrajesh.duckdns.org"
files=[]
for directory in (Path("/etc/nginx/conf.d"),Path("/etc/nginx/sites-enabled")):
    if directory.exists():
        for p in directory.rglob("*"):
            if p.is_file() and not p.is_symlink() and os.access(p,os.R_OK):
                files.append(p)
def locations(s):
    pat=re.compile(r'(?m)^\s*location\s+=\s*/dhan/callback\s*\{')
    for match in pat.finditer(s):
        depth=1
        i=match.end()
        while i < len(s) and depth:
            if s[i]=="{": depth+=1
            elif s[i]=="}": depth-=1
            i+=1
        if depth: raise RuntimeError("unterminated callback block")
        yield match.start(),i,s[match.start():i]
def containing_server(s,pos):
    stack=[]
    for m in re.finditer(r'[{}]',s[:pos]):
        if m.group()=="{":
            pre=s[max(0,m.start()-100):m.start()]
            stack.append((m.start(),bool(re.search(r'\bserver\s*$',pre))))
        elif stack: stack.pop()
    return next((idx for idx,is_server in reversed(stack) if is_server),None)
targets=[]
for p in files:
    try: s=p.read_text(encoding="utf8")
    except (OSError,UnicodeError): continue
    for start,end,block in locations(s):
        server=containing_server(s,start)
        if server is None: continue
        # Require same HTTPS vhost, and clone prefix inside this server.
        prefix=s[server:start]
        if not re.search(r'\bserver_name\s+[^;]*\bbotkingrajesh\.duckdns\.org\b',prefix): continue
        if not re.search(r'(?m)^\s*location\s+\^~\s+/clone-v2/\s*\{',s[server:]): continue
        targets.append((p,s,start,end,block))
if len(targets)!=1:
    raise SystemExit("CALLBACK_BLOCKED=EXPECTED_ONE_EXISTING_HOST_CALLBACK_FOUND_"+str(len(targets)))
p,s,start,end,block=targets[0]
proxy=re.findall(r'(?m)^\s*proxy_pass\s+(http://127\.0\.0\.1:(?:8000|8002))\s*;',block)
if len(proxy)!=1:
    raise SystemExit("CALLBACK_BLOCKED=UNRECOGNIZED_CALLBACK_PROXY")
if proxy[0].endswith(":8002"):
    print("CALLBACK_ROUTE_ALREADY_CLONE=YES")
else:
    newblock=block.replace("http://127.0.0.1:8000","http://127.0.0.1:8002")
    if newblock==block: raise SystemExit("CALLBACK_BLOCKED=NO_SAFE_REPLACEMENT")
    backup=Path(os.environ["BACKUP_DIR"])/"original.conf"
    shutil.copy2(p,backup)
    (Path(os.environ["BACKUP_DIR"])/"path.txt").write_text(str(p))
    temp=p.with_name(p.name+".clone-callback-tmp")
    temp.write_text(s[:start]+newblock+s[end:],encoding="utf8")
    shutil.copymode(p,temp)
    os.replace(temp,p)
    print("CALLBACK_ROUTE_CHANGED=V1_TO_CLONE")
print("CALLBACK_TARGET_FILE="+str(p))
PY
then
  echo "CALLBACK_CHANGE_FAILED=YES"
  exit 2
fi
restore() {
  if [[ -s "$BACKUP_DIR/path.txt" && -f "$BACKUP_DIR/original.conf" ]]; then
    target="$(cat "$BACKUP_DIR/path.txt")"
    cp -p "$BACKUP_DIR/original.conf" "$target"
    nginx -t >/dev/null 2>&1 && systemctl reload nginx.service || true
    echo "CALLBACK_NGINX_ROLLBACK=RESTORED"
  fi
}
if ! nginx -t >/dev/null 2>&1; then
  restore; echo "CALLBACK_BLOCKED=NGINX_SYNTAX"; exit 1
fi
if ! systemctl reload nginx.service; then
  restore; echo "CALLBACK_BLOCKED=NGINX_RELOAD"; exit 1
fi
cb="$(status https://botkingrajesh.duckdns.org/dhan/callback)"
start="$(status -X POST https://botkingrajesh.duckdns.org/clone-v2/dhan/start)"
echo "PUBLIC_CALLBACK_HTTP=$cb"
echo "PUBLIC_BROWSER_START_HTTP=$start"
if [[ "$cb" != 403 || "$start" != 403 ]]; then
  restore; echo "CALLBACK_BLOCKED=PUBLIC_CHECK"; exit 1
fi
echo "ORACLE_PRIMARY_CLONE_BROWSER_LOGIN_ROUTE=READY"
echo "B3_DHAN_BROWSER_CONSENT=PENDING"
echo "V1_SERVICE_UNCHANGED=YES"
echo "CALLBACK_CUTOVER_COMPLETE"
