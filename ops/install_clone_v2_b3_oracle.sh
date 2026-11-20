#!/usr/bin/env bash
# Clone B3: isolated, reversible Dhan read-only gateway deployment.
# Run as root with one fully reviewed Git SHA argument. No V1 writes.
set -Eeuo pipefail
umask 077
SHA="$1"
[[ "$(id -u)" == 0 && "$SHA" =~ ^[a-f0-9]{40}$ ]] || { echo 'BLOCKED: sudo and full SHA required'; exit 1; }
ROOT=/home/opc/botking-clone-v2-runtime
PRIVATE=/home/opc/botking-clone-v2-private
BASE="https://raw.githubusercontent.com/vaishnavi596/volume-king/$SHA/backend"
DROP_DIR=/etc/systemd/system/botking-clone-v2.service.d
DROP="$DROP_DIR/b3-dhan.conf"
ENVFILE=/etc/bot-king/clone-v2-dhan-client.env
SYNC=/usr/local/libexec/botking-clone-v2-dhan-sync
SYNC_UNIT=/etc/systemd/system/botking-clone-v2-dhan-sync.service
SYNC_TIMER=/etc/systemd/system/botking-clone-v2-dhan-sync.timer
TOKEN_SRC=/etc/bot-king/dhan-token
TOKEN_DST="$PRIVATE/dhan-token"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP="$PRIVATE/b3-backup-$STAMP"
STAGE="$PRIVATE/b3-candidate-$STAMP"
fail() { echo "B3_BLOCKED: $*" >&2; exit 1; }
health() { curl -fsS -o /dev/null --max-time 8 "$1"; }
[[ "$(systemctl is-active bot-king.service)" == active ]] || fail "V1 inactive"
[[ "$(systemctl is-active botking-clone-v2.service)" == active ]] || fail "Clone inactive"
health http://127.0.0.1:8000/health || fail "V1 HTTP"
health http://127.0.0.1:8002/clone-v2/health || fail "Clone HTTP"
[[ -f "$PRIVATE/ssk" && -s "$TOKEN_SRC" ]] || fail "SSK or source Dhan token missing"
for target in "$DROP" "$ENVFILE" "$SYNC" "$SYNC_UNIT" "$SYNC_TIMER"; do
  [[ ! -e "$target" ]] || fail "B3 already installed; review existing files"
done
install -d -m 0700 "$BACKUP" "$STAGE"
for file in clone_v2_gateway.py dhan_feed.py dhan_option_metrics.py; do
  curl -fLsS --retry 2 --connect-timeout 10 --max-time 35 "$BASE/$file" -o "$STAGE/$file" || fail "source download failed"
  python3 -m py_compile "$STAGE/$file" || fail "invalid Python source"
  if [[ -e "$ROOT/$file" ]]; then cp -a "$ROOT/$file" "$BACKUP/$file"; fi
done
grep -q '"/clone-v2/market/quotes"' "$STAGE/clone_v2_gateway.py" || fail "quotes missing"
grep -q '"/clone-v2/market/candles"' "$STAGE/clone_v2_gateway.py" || fail "candles missing"
grep -q '"/clone-v2/market/options/chain"' "$STAGE/clone_v2_gateway.py" || fail "option route missing"
SITE="$ROOT/.venv/lib64/python3.9/site-packages"
[[ -d "$SITE" ]] || fail "Clone Python environment missing"
PYTHONPATH="$SITE" /usr/bin/python3.9 -c 'import fastapi,uvicorn,pydantic' || fail "dependencies missing"
PID="$(systemctl show bot-king.service --property=MainPID --value)"
[[ "$PID" =~ ^[0-9]+$ && "$PID" != 0 ]] || fail "V1 process missing"
B3_V1_PID="$PID" B3_ENV_TEMP="$STAGE/client.env" python3 - <<'PY'
import os,re
from pathlib import Path
rows=Path("/proc/"+os.environ["B3_V1_PID"]+"/environ").read_bytes().split(b"\0")
values=[r.split(b"=",1)[1].decode("ascii") for r in rows if r.startswith(b"DHAN_CLIENT_ID=")]
if len(values)!=1 or not re.fullmatch(r"[A-Za-z0-9_-]{2,128}",values[0]):
    raise SystemExit("B3_BLOCKED: Dhan client ID unavailable in V1 process")
Path(os.environ["B3_ENV_TEMP"]).write_text("DHAN_CLIENT_ID="+values[0]+"\n")
PY
[[ -s "$STAGE/client.env" ]] || fail "Dhan client ID not found"
install -d -m 0755 "$DROP_DIR" /usr/local/libexec
rollback() {
  echo "B3_DEPLOYMENT_FAILED: ROLLBACK_TO_WORKING_B2"
  for file in clone_v2_gateway.py dhan_feed.py dhan_option_metrics.py; do
    if [[ -f "$BACKUP/$file" ]]; then cp -a "$BACKUP/$file" "$ROOT/$file"
    else rm -f "$ROOT/$file"; fi
  done
  systemctl disable --now botking-clone-v2-dhan-sync.timer >/dev/null 2>&1 || true
  rm -f "$DROP" "$ENVFILE" "$SYNC" "$SYNC_UNIT" "$SYNC_TIMER" "$TOKEN_DST"
  systemctl daemon-reload
  systemctl restart botking-clone-v2.service || true
  printf 'B2_RESTORED_HTTP='
  curl -sS -o /dev/null --max-time 8 -w '%{http_code}\n' http://127.0.0.1:8002/clone-v2/health || true
  echo "B3_BACKUP=$BACKUP"
}
trap rollback ERR
for file in clone_v2_gateway.py dhan_feed.py dhan_option_metrics.py; do
  install -o opc -g opc -m 0600 "$STAGE/$file" "$ROOT/$file"
done
install -o root -g root -m 0600 "$STAGE/client.env" "$ENVFILE"
install -o opc -g opc -m 0600 "$TOKEN_SRC" "$TOKEN_DST"
cat > "$SYNC" <<'EOS'
#!/usr/bin/env bash
set -euo pipefail
source_file=/etc/bot-king/dhan-token
dest_file=/home/opc/botking-clone-v2-private/dhan-token
test -s "$source_file"
if ! cmp -s "$source_file" "$dest_file"; then
  install -o opc -g opc -m 0600 "$source_file" "$dest_file"
fi
EOS
chmod 0700 "$SYNC"
cat > "$SYNC_UNIT" <<'EOS'
[Unit]
Description=Clone B3 secure Oracle Dhan token mirror
[Service]
Type=oneshot
User=root
ExecStart=/usr/local/libexec/botking-clone-v2-dhan-sync
NoNewPrivileges=true
EOS
cat > "$SYNC_TIMER" <<'EOS'
[Unit]
Description=Update clone B3 Dhan token after provider renewal
[Timer]
OnBootSec=45s
OnUnitActiveSec=60s
AccuracySec=15s
Unit=botking-clone-v2-dhan-sync.service
[Install]
WantedBy=timers.target
EOS
cat > "$DROP" <<'EOS'
[Service]
EnvironmentFile=/etc/bot-king/clone-v2-dhan-client.env
Environment=BOTKING_CLONE_DHAN_TOKEN_FILE=/home/opc/botking-clone-v2-private/dhan-token
EOS
restorecon "$ROOT/"clone_v2_gateway.py "$ROOT/"dhan_feed.py "$ROOT/"dhan_option_metrics.py "$DROP" "$ENVFILE" "$TOKEN_DST" 2>/dev/null || true
systemctl daemon-reload
systemctl enable --now botking-clone-v2-dhan-sync.timer >/dev/null
systemctl restart botking-clone-v2.service
health http://127.0.0.1:8002/clone-v2/health
health http://127.0.0.1:8000/health
[[ "$(systemctl is-active bot-king.service)" == active ]] || fail "V1 status changed"
[[ "$(systemctl is-active botking-clone-v2.service)" == active ]] || fail "B3 service inactive"
python3 - <<'PY'
import http.client,json,math
from pathlib import Path
key=Path("/home/opc/botking-clone-v2-private/ssk").read_text().strip()
def probe(method,path,data=None,secret=None):
    c=http.client.HTTPConnection("127.0.0.1",8002,timeout=20)
    hdr={"Content-Type":"application/json"}
    if secret is not None: hdr["X-BotKing-Key"]=secret
    c.request(method,path,body=json.dumps(data) if data is not None else None,headers=hdr)
    r=c.getresponse()
    status=r.status
    raw=r.read(100000)
    c.close()
    return status,json.loads(raw) if status==200 else None
assert probe("GET","/clone-v2/status")[0]==403
assert probe("GET","/clone-v2/status",secret="wrong")[0]==403
assert probe("GET","/clone-v2/status",secret=key)[0]==200
status,body=probe("POST","/clone-v2/market/quotes",{"symbols":["NIFTY"]},key)
print("B3_NIFTY_UPSTREAM_HTTP="+str(status))
if status!=200:
    raise RuntimeError("No verified Dhan provider response; rollback required")
row=body.get("quotes",{}).get("NIFTY")
price=row.get("ltp") if isinstance(row,dict) else None
assert (body.get("source")=="dhan" and body.get("live_orders_enabled") is False
        and type(price) in (int,float) and math.isfinite(price) and price>0)
print("B3_DHAN_TWO_WAY_QUOTE=PASS")
print("B3_SSK_NEGATIVE_POSITIVE=PASS")
PY
trap - ERR
echo "B3_ORACLE_SOURCE_COMMIT=$SHA"
echo "B3_DHAN_ORACLE_GATEWAY=PASS"
echo "B3_V1_UNCHANGED=PASS"
echo "B3_TOKEN_SYNC_TIMER=ENABLED"
echo "B3_PHONE_DATA_ACCEPTANCE=PENDING"
