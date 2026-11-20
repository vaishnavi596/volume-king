#!/usr/bin/env bash
# OWNER-RUN Clone B3 primary browser-login cutover. Reuses the existing Dhan
# OAuth app and public URL. Does NOT stop old V1: retirement after Clone
# live-phone/quote acceptance is a separate, explicit operator action.
set -Eeuo pipefail
umask 077
SHA="${1:-}"
[[ "$(id -u)" == 0 && "$SHA" =~ ^[0-9a-f]{40}$ ]] || {
  echo "CUTOVER_BLOCKED: use sudo with pinned full Git SHA"; exit 2;
}
BASE="https://raw.githubusercontent.com/vaishnavi596/volume-king/$SHA/ops"
TMP="$(mktemp -d /tmp/botking-clone-cutover.XXXXXX)"
trap 'rm -rf "$TMP"' EXIT
fetch() {
  curl -fLsS --connect-timeout 10 --max-time 50 --retry 2 \
    "$BASE/$1" -o "$TMP/$1"
  bash -n "$TMP/$1"
}
fetch provision_clone_from_existing_dhan_oauth.sh
fetch install_clone_v2_b3_oracle.sh
[[ "$(systemctl is-active nginx.service)" == active ]] || {
  echo "CUTOVER_BLOCKED: nginx not active"; exit 2;
}
[[ "$(systemctl is-active bot-king.service)" == active ]] || {
  echo "CUTOVER_BLOCKED: source V1 OAuth process not available"; exit 2;
}
[[ "$(systemctl is-active botking-clone-v2.service)" == active ]] || {
  echo "CUTOVER_BLOCKED: Clone not active"; exit 2;
}
[[ "$(curl -s -o /dev/null --max-time 7 -w '%{http_code}' http://127.0.0.1:8000/health)" == 200 ]] || {
  echo "CUTOVER_BLOCKED: V1 baseline health"; exit 2;
}
[[ "$(curl -s -o /dev/null --max-time 7 -w '%{http_code}' http://127.0.0.1:8002/clone-v2/health)" == 200 ]] || {
  echo "CUTOVER_BLOCKED: Clone baseline health"; exit 2;
}
# Private OAuth app credential transfer does not rotate or reveal Dhan token.
if [[ ! -f /etc/bot-king/clone-dhan-oauth.env ]]; then
  bash "$TMP/provision_clone_from_existing_dhan_oauth.sh"
  echo "CUTOVER_STEP_OAUTH=TRANSFERRED_EXISTING_CREDENTIALS"
else
  echo "CUTOVER_STEP_OAUTH=EXISTING_CONFIG"
fi
# Requires the already staged clone-only Callback source at the pinned SHA.
bash "$TMP/install_clone_v2_b3_oracle.sh" "$SHA"
LOCAL_START="$(curl -s -o /dev/null --max-time 8 -w '%{http_code}' \
  -X POST http://127.0.0.1:8002/clone-v2/dhan/start)"
LOCAL_CALLBACK="$(curl -s -o /dev/null --max-time 8 -w '%{http_code}' \
  http://127.0.0.1:8002/dhan/callback)"
if [[ "$LOCAL_START" != 403 || "$LOCAL_CALLBACK" != 403 ]]; then
  echo "CUTOVER_BLOCKED: local Clone Dhan routes missing; nginx UNCHANGED"
  echo "CLONE_START_HTTP=$LOCAL_START CLONE_CALLBACK_HTTP=$LOCAL_CALLBACK"
  exit 1
fi
echo "CUTOVER_STEP_CLONE_ROUTES=PASS"

# Nginx HTTPS cutover: add ONE exact-match location to the same existing
# HTTPS server block which already contains 'location ^~ /clone-v2/'.
# Fail if zero/multiple suitable source blocks; never guess the host config.
# A portable source scanner identifies a literal single candidate file.
NGINX_CONF="$(python3 - <<'PY'
from pathlib import Path
import re
matches=[]
for base in (Path("/etc/nginx/conf.d"),Path("/etc/nginx/sites-enabled")):
    if not base.exists():
        continue
    for p in base.rglob("*"):
        if not p.is_file() or p.is_symlink():
            continue
        try:
            text=p.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        if re.search(r'(?m)^\s*location\s+\^~\s+/clone-v2/\s*\{',text):
            matches.append(str(p))
if len(matches) != 1:
    raise SystemExit("CUTOVER_BLOCKED: expected ONE HTTPS Clone location config; found "+str(len(matches)))
print(matches[0])
PY
)" || exit 2
NGINX_BACKUP="$TMP/nginx-original.conf"
cp -p "$NGINX_CONF" "$NGINX_BACKUP"
# Modify only the owner-identified file; ensure exact public URL server
# explicitly belongs to this file (not a second server block elsewhere).
BKC_NGINX_CONF="$NGINX_CONF" python3 - <<'PY'
import os,re
from pathlib import Path
p=Path(os.environ["BKC_NGINX_CONF"])
s=p.read_text(encoding="utf-8")
marker=re.search(r'(?m)^\s*location\s+\^~\s+/clone-v2/\s*\{',s)
if not marker or len(re.findall(r'(?m)^\s*location\s+\^~\s+/clone-v2/\s*\{',s))!=1:
    raise SystemExit("CUTOVER_BLOCKED: ambiguous Clone Nginx location")
if re.search(r'(?m)^\s*location\s+=\s*/dhan/callback\s*\{',s):
    raise SystemExit("CUTOVER_BLOCKED: callback routing already configured; review manually")
# The original config may contain other server blocks. Ensure that the active
# /clone-v2/ route occurs within a server {} that contains the expected name.
def scopes_at(txt,offset):
    stack=[]
    for m in re.finditer(r'[{}]',txt[:offset]):
        if m.group()=="{":stack.append(m.start())
        elif stack:stack.pop()
    return stack
stack=scopes_at(s,marker.start())
servers=[start for start in stack if re.search(r'(?:^|\n)\s*server\s*$',s[max(0,start-20):start])]
if not servers:
    raise SystemExit("CUTOVER_BLOCKED: cannot prove active HTTPS server block")
# Accept only if the containing server scope mentions the exact host before
# the Clone location. No rewriting /dhan/ routes or other location blocks.
start=servers[-1]
prefix=s[start:marker.start()]
if "botkingrajesh.duckdns.org" not in prefix:
    raise SystemExit("CUTOVER_BLOCKED: unexpected server_name; no nginx change")
insertion='''    # Clone-only handoff of existing registered Dhan OAuth callback.
    location = /dhan/callback {
        proxy_pass http://127.0.0.1:8002;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header Connection "";
        proxy_connect_timeout 5s;
        proxy_read_timeout 25s;
        proxy_redirect off;
        add_header Cache-Control "no-store" always;
    }
'''
p.write_text(s[:marker.start()]+insertion+s[marker.start():],encoding="utf-8")
PY
# Restore Nginx automatically for a broken config or failed public handoff.
restore_nginx() {
  cp -p "$NGINX_BACKUP" "$NGINX_CONF"
  nginx -t >/dev/null 2>&1 && systemctl reload nginx.service || true
  echo "CUTOVER_NGINX_ROLLBACK=RESTORED"
}
if ! nginx -t >/dev/null 2>&1; then
  restore_nginx
  echo "CUTOVER_BLOCKED: nginx config syntax failed"
  exit 1
fi
if ! systemctl reload nginx.service; then
  restore_nginx
  echo "CUTOVER_BLOCKED: nginx reload failed"
  exit 1
fi
PUBLIC_CB="$(curl -s -o /dev/null --max-time 12 -w '%{http_code}' \
  https://botkingrajesh.duckdns.org/dhan/callback)"
PUBLIC_START="$(curl -s -o /dev/null --max-time 12 -w '%{http_code}' \
  -X POST https://botkingrajesh.duckdns.org/clone-v2/dhan/start)"
if [[ "$PUBLIC_CB" != 403 || "$PUBLIC_START" != 403 ]]; then
  echo "PUBLIC_CALLBACK_HTTP=$PUBLIC_CB PUBLIC_BROWSER_START_HTTP=$PUBLIC_START"
  restore_nginx
  echo "CUTOVER_BLOCKED: public route check failed"
  exit 1
fi
echo "PUBLIC_CALLBACK_HTTP=$PUBLIC_CB"
echo "PUBLIC_BROWSER_START_HTTP=$PUBLIC_START"
echo "ORACLE_PRIMARY_CLONE_BROWSER_LOGIN_ROUTE=READY"
echo "EXISTING_DHAN_API_APP_REUSED=YES"
echo "V1_SERVICE_NOT_STOPPED_FOR_PHONE_VERIFICATION=YES"
echo "REAL_DHAN_BROWSER_CONSENT_AND_QUOTE=PHONE_TEST_PENDING"
echo "CLONE_PRIMARY_CUTOVER_COMPLETE"
