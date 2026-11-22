#!/usr/bin/env bash
# V3 joint 429 audit: Clone-only staged source replacement, V1 never written.
# Default is READ-ONLY. Apply requires owner on Oracle explicitly passing
# --apply and the *observed live* Git blob SHA-1; mismatches fail closed.
set -Eeuo pipefail
umask 077
ROOT=/home/opc/botking-clone-v2-runtime
PRIVATE=/home/opc/botking-clone-v2-private
SERVICE=botking-clone-v2.service
V1=bot-king.service
TARGET=clone_v2_gateway.py
PIN=e7fde7071b77e3254430b30e5412511f69e85f85
EXPECTED_NEW=49d8d5cdd90da4c768367d9258f00414f9027291
MODE=${1:---audit}
EXPECTED_OLD=${2:-}
fail(){ echo "V3_CLONE_DEPLOY_BLOCKED: $*" >&2; exit 1; }
blob(){
 python3 - "$1" <<'PY'
import hashlib,sys
with open(sys.argv[1],"rb") as f: data=f.read()
print(hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest())
PY
}
[[ "$MODE" == --audit || "$MODE" == --apply ]] || fail "mode must be --audit or --apply"
[[ "$(id -un)" == opc ]] || fail "opc account required"
[[ -d "$ROOT" && -d "$PRIVATE" && ! -L "$ROOT/$TARGET" && -f "$ROOT/$TARGET" ]] || fail "Clone runtime layout"
[[ "$(systemctl is-active "$V1")" == active ]] || fail "V1 not active"
[[ "$(systemctl is-active "$SERVICE")" == active ]] || fail "Clone not active"
[[ "$(systemctl show "$SERVICE" -p WorkingDirectory --value)" == "$ROOT" ]] || fail "Clone working directory mismatch"
for pair in "8000:/health" "8002:/clone-v2/health"; do
 port=${pair%%:*}; route=${pair#*:}
 [[ "$(curl --noproxy '*' --silent --output /dev/null --max-time 5 --write-out '%{http_code}' "http://127.0.0.1:$port$route")" == 200 ]] || fail "local health $port"
done
LIVE_BLOB="$(blob "$ROOT/$TARGET")"
echo "V3_CLONE_LIVE_BLOB=$LIVE_BLOB"
echo "V3_CLONE_DESIRED_BLOB=$EXPECTED_NEW"
if [[ "$LIVE_BLOB" == "$EXPECTED_NEW" ]]; then
 echo "V3_CLONE_GATEWAY_SOURCE=ALREADY_CURRENT"
 exit 0
fi
if [[ "$MODE" == --audit ]]; then
 echo "V3_CLONE_GATEWAY_SOURCE=DIFFERENT_NO_WRITE"
 echo "NEXT=Review baseline and run explicitly --apply <observed blob> after approval"
 exit 0
fi
[[ "$EXPECTED_OLD" =~ ^[a-f0-9]{40}$ && "$EXPECTED_OLD" == "$LIVE_BLOB" ]] || fail "explicit observed baseline Git blob SHA required"
[[ -x /usr/bin/python3.9 ]] || fail "Python 3.9 runtime absent"
WORK="$(mktemp -d "$PRIVATE/v3-quote-pacing.XXXXXXXX")"
chmod 700 "$WORK"
echo "V3_CLONE_BACKUP=$WORK"
cp -p "$ROOT/$TARGET" "$WORK/$TARGET.rollback"
curl --fail --silent --show-error --location --max-time 40 \
  "https://raw.githubusercontent.com/vaishnavi596/volume-king/$PIN/backend/$TARGET" \
  -o "$WORK/$TARGET"
[[ "$(blob "$WORK/$TARGET")" == "$EXPECTED_NEW" ]] || fail "candidate Git blob mismatch"
chmod 600 "$WORK/$TARGET"
/usr/bin/python3.9 -m py_compile "$WORK/$TARGET"
SITE="$ROOT/.venv/lib64/python3.9/site-packages"
[[ -d "$SITE" ]] || fail "Clone 3.9 dependency environment absent"
PYTHONPATH="$WORK:$SITE" /usr/bin/python3.9 - <<'PY'
import clone_v2_gateway
assert callable(clone_v2_gateway.create_app)
print("V3_CLONE_STAGED_IMPORT=PASS")
PY
changed=0
rollback(){
 if [[ "$changed" == 1 ]]; then
  install -m 0600 "$WORK/$TARGET.rollback" "$ROOT/.$TARGET.rollback-v3"
  mv -f "$ROOT/.$TARGET.rollback-v3" "$ROOT/$TARGET"
  sudo -n systemctl restart "$SERVICE" || true
  echo "V3_CLONE_ROLLBACK_ATTEMPTED=YES"
 fi
}
trap rollback ERR
install -m 0600 "$WORK/$TARGET" "$ROOT/.$TARGET.candidate-v3"
changed=1
mv -f "$ROOT/.$TARGET.candidate-v3" "$ROOT/$TARGET"
sudo -n systemctl restart "$SERVICE"
healthy=0
for _ in $(seq 1 25); do
 if [[ "$(systemctl is-active "$SERVICE")" == active ]] && \
    [[ "$(curl --noproxy '*' --silent --output /dev/null --max-time 3 --write-out '%{http_code}' http://127.0.0.1:8002/clone-v2/health)" == 200 ]]; then
  healthy=1; break
 fi
 sleep 1
done
[[ "$healthy" == 1 ]] || fail "Clone health after restart"
[[ "$(blob "$ROOT/$TARGET")" == "$EXPECTED_NEW" ]] || fail "deployed source checksum"
[[ "$(systemctl is-active "$V1")" == active ]] || fail "V1 process changed"
[[ "$(curl --noproxy '*' --silent --output /dev/null --max-time 5 --write-out '%{http_code}' http://127.0.0.1:8000/health)" == 200 ]] || fail "V1 health changed"
changed=0
trap - ERR
echo "V3_CLONE_ONLY_DEPLOY=PASS"
echo "V3_V1_UNCHANGED_AND_HEALTHY=YES"
echo "V3_NO_DHAN_API_OR_TRADE_REQUEST=YES"
echo "NEXT=Owner verifies live 429 stage and index 3/3 during authorized market window"
