#!/usr/bin/env bash
# V3 Clone-only diagnostic three-header repair.
# Defaults to --check (no deployment). --apply is deliberate and rollback guarded.
set -Eeuo pipefail
umask 077
MODE=--check
if [[ "$#" -gt 0 ]]; then MODE="$1"; fi
[[ "$MODE" == --check || "$MODE" == --apply ]] || { echo "USE --check OR --apply"; exit 2; }
ROOT=/home/opc/botking-clone-v2-runtime
PRIVATE=/home/opc/botking-clone-v2-private
TARGET="$ROOT/clone_v2_gateway.py"
SERVICE=botking-clone-v2.service
EXPECTED=49d8d5cdd90da4c768367d9258f00414f9027291
[[ "$(id -un)" == opc ]] || { echo BLOCKED_USER; exit 1; }
[[ -d "$ROOT" && -d "$PRIVATE" && -f "$TARGET" && ! -L "$TARGET" ]] || { echo BLOCKED_LAYOUT; exit 1; }
for unit in bot-king.service "$SERVICE" nginx.service; do
  [[ "$(systemctl is-active "$unit")" == active ]] || { echo "BLOCKED_SERVICE=$unit"; exit 1; }
done
[[ "$(systemctl show "$SERVICE" -p WorkingDirectory --value)" == "$ROOT" ]] || { echo BLOCKED_WORKDIR; exit 1; }
http_code() { curl --noproxy '*' --silent --max-time 4 --output /dev/null --write-out '%{http_code}' "$1"; }
[[ "$(http_code http://127.0.0.1:8000/health)" == 200 ]] || { echo BLOCKED_V1_HEALTH; exit 1; }
[[ "$(http_code http://127.0.0.1:8002/clone-v2/health)" == 200 ]] || { echo BLOCKED_CLONE_HEALTH; exit 1; }
WORK="$(mktemp -d "$PRIVATE/v3-quote-stage.XXXXXXXX")"
chmod 700 "$WORK"
python3 - "$TARGET" "$WORK" "$EXPECTED" <<'PY'
import hashlib,pathlib,sys
target=pathlib.Path(sys.argv[1]);work=pathlib.Path(sys.argv[2]);expected=sys.argv[3]
data=target.read_bytes()
blob=lambda b: hashlib.sha1(b"blob "+str(len(b)).encode()+b"\0"+b).hexdigest()
if blob(data)!=expected:
    print("BLOCKED_BASELINE_DRIFT="+blob(data));raise SystemExit(1)
s=data.decode("utf-8")
edits=[
 ('raise HTTPException(502, "Clone read-only Dhan quote unavailable") from None',
  'raise HTTPException(502, "Clone read-only Dhan quote unavailable",\n                                    headers={"X-BotKing-Quote-Failure-Stage": "PROVIDER"}) from None'),
 ('raise HTTPException(502, "Invalid clone Dhan quote response")',
  'raise HTTPException(502, "Invalid clone Dhan quote response",\n                                    headers={"X-BotKing-Quote-Failure-Stage": "RESPONSE"})'),
 ('raise HTTPException(502, "No validated clone quotes")',
  'raise HTTPException(502, "No validated clone quotes",\n                                    headers={"X-BotKing-Quote-Failure-Stage": "RESPONSE"})')
]
for before,after in edits:
    if s.count(before)!=1: raise SystemExit("BLOCKED_PATCH_CONTRACT")
    s=s.replace(before,after)
if s.count("X-BotKing-Quote-Failure-Stage")!=3: raise SystemExit("BLOCKED_HEADER_COUNT")
candidate=work/"clone_v2_gateway.py"
candidate.write_text(s,encoding="utf-8");candidate.chmod(0o600)
backup=work/"clone_v2_gateway.py.backup"
backup.write_bytes(data);backup.chmod(0o600)
print("BASELINE_BLOB_MATCH=YES")
print("THREE_STAGE_HEADERS=STAGED")
print("CANDIDATE_BLOB="+blob(candidate.read_bytes()))
PY
PYTHON=/usr/bin/python3.9
[[ -x "$PYTHON" ]] || PYTHON=python3
"$PYTHON" - "$WORK/clone_v2_gateway.py" <<'PY'
import ast,sys
with open(sys.argv[1],encoding="utf-8") as f: ast.parse(f.read())
print("PYTHON_SYNTAX=PASS")
PY
if [[ "$MODE" == --check ]]; then
  echo "PREFLIGHT_PASS=YES"
  echo "ORACLE_UNCHANGED=YES"
  exit 0
fi
changed=0
rollback() {
  if [[ "$changed" == 1 ]]; then
    install -m 0600 "$WORK/clone_v2_gateway.py.backup" "$ROOT/.clone_v2_gateway.py.restore"
    mv -f "$ROOT/.clone_v2_gateway.py.restore" "$TARGET"
    sudo -n systemctl restart "$SERVICE" || true
    echo "ROLLBACK_ATTEMPTED=YES"
  fi
  echo "PRIVATE_BACKUP_RETAINED=YES"
}
trap rollback ERR
install -m 0600 "$WORK/clone_v2_gateway.py" "$ROOT/.clone_v2_gateway.py.staged"
changed=1
mv -f "$ROOT/.clone_v2_gateway.py.staged" "$TARGET"
sudo -n systemctl restart "$SERVICE"
healthy=0
for attempt in $(seq 1 20); do
  if [[ "$(systemctl is-active "$SERVICE")" == active ]] && [[ "$(http_code http://127.0.0.1:8002/clone-v2/health)" == 200 ]]; then
    healthy=1; break
  fi
  sleep 1
done
[[ "$healthy" == 1 ]] || { echo BLOCKED_POSTDEPLOY_CLONE_HEALTH; exit 1; }
[[ "$(http_code http://127.0.0.1:8000/health)" == 200 ]] || { echo BLOCKED_POSTDEPLOY_V1_HEALTH; exit 1; }
unauth_code="$(curl --noproxy '*' --silent --max-time 5 --output /dev/null --write-out '%{http_code}' -X POST -H 'Content-Type: application/json' --data '{"symbols":["NIFTY"]}' http://127.0.0.1:8002/clone-v2/market/quotes)"
[[ "$unauth_code" == 403 ]] || { echo BLOCKED_POSTDEPLOY_SSK_GATE; exit 1; }
changed=0
trap - ERR
echo "CLONE_THREE_HEADER_DEPLOY=PASS"
echo "V1_HEALTH=200"
echo "UNAUTH_QUOTES=403"
echo "NO_DHAN_PROVIDER_REQUESTS_SENT=YES"
echo "PRIVATE_BACKUP_RETAINED=YES"
