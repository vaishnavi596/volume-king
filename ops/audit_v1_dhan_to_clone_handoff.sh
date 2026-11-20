#!/usr/bin/env bash
# Read-only, sanitized V1 Dhan OAuth -> Clone B3 handoff preflight.
# Never requests/prints tokens, SSK, headers or credentials; no system changes.
set -u
export LC_ALL=C
echo "=== BOT KING V1 DHAN LOGIN TO CLONE B3 HANDOFF AUDIT ==="
for S in bot-king.service botking-clone-v2.service botking-dhan-renewal.timer botking-dhan-renewal.service; do
  printf '%s_STATE=' "$S"
  systemctl is-active "$S" 2>/dev/null || true
  printf '%s_UNIT_FILE=' "$S"
  systemctl is-enabled "$S" 2>/dev/null || true
done
echo "--- ROUTE CLASSIFICATION (NO SSK OR BROKER REQUEST) ---"
check() {
  local label="$1" method="$2" url="$3" result
  result="$(curl -sS -o /dev/null --max-time 8 -w '%{http_code}' -X "$method" \
    -H 'Accept: application/json' "$url" 2>/dev/null)" || result="000"
  printf '%s_HTTP=%s\n' "$label" "$result"
}
check V1_LOCAL_HEALTH GET http://127.0.0.1:8000/health
check CLONE_LOCAL_HEALTH GET http://127.0.0.1:8002/clone-v2/health
check V1_LOCAL_CALLBACK GET http://127.0.0.1:8000/dhan/callback
check CLONE_LOCAL_OLD_CALLBACK GET http://127.0.0.1:8002/dhan/callback
check CLONE_LOCAL_BROWSER_START POST http://127.0.0.1:8002/clone-v2/dhan/start
check PUBLIC_OLD_CALLBACK GET https://botkingrajesh.duckdns.org/dhan/callback
check PUBLIC_CLONE_BROWSER_START POST https://botkingrajesh.duckdns.org/clone-v2/dhan/start
echo "--- EXISTING V1 RUNTIME VARIABLE PRESENCE ONLY ---"
sudo python3 - <<'PY'
import os,subprocess
from pathlib import Path
from datetime import datetime,timezone
pid=subprocess.run(["systemctl","show","bot-king.service","-p","MainPID","--value"],
                   text=True,capture_output=True).stdout.strip()
try:
    rows=Path("/proc/"+str(int(pid))+"/environ").read_bytes().split(b"\x00")
    names={r.split(b"=",1)[0].decode("ascii","ignore") for r in rows if b"=" in r}
except Exception:
    names=set()
for name in ("DHAN_CLIENT_ID","DHAN_API_KEY","DHAN_API_SECRET","DHAN_SESSION_FILE"):
    print("V1_RUNTIME_"+name+"="+("SET" if name in names else "NOT_VISIBLE"))
for label,path in (("V1_TOKEN","/etc/bot-king/dhan-token"),
                   ("V1_RENEWAL_METADATA","/etc/bot-king/dhan-expiry.json"),
                   ("CLONE_OAUTH_CONFIG","/etc/bot-king/clone-dhan-oauth.env"),
                   ("CLONE_TOKEN","/home/opc/botking-clone-v2-private/dhan-token")):
    p=Path(path)
    try:
        if p.is_symlink(): raise ValueError()
        st=p.stat()
        age=round((datetime.now(timezone.utc).timestamp()-st.st_mtime)/3600,1)
        print(label+"=PRESENT AGE_HOURS="+str(age))
    except (OSError,ValueError):
        print(label+"=MISSING")
PY
echo "--- HTTPS ROUTER TYPE (NAMES ONLY) ---"
for S in nginx.service caddy.service httpd.service; do
  x="$(systemctl is-active "$S" 2>/dev/null || true)"
  if [[ "$x" == active ]]; then echo "PUBLIC_ROUTER_SERVICE=$S"; fi
done
echo "V1_TO_CLONE_HANDOFF_PREFLIGHT_COMPLETE"
