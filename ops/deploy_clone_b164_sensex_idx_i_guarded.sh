#!/usr/bin/env bash
# B164: one-file Clone-only SENSEX IDX_I/51 mapping correction.
# No broker calls, credentials, V1 edits, or orders. Fail closed with rollback.
set -Eeuo pipefail
umask 077
ROOT=/home/opc/botking-clone-v2-runtime
PRIVATE=/home/opc/botking-clone-v2-private
TARGET=clone_v2_gateway.py
OLD=0db7edfc06134781581bf31d05db092f05bcd3b3
NEW=10d2bf6f2265bfbca8a195cb742691ff541f7baf
PIN=ea22da78b70cb68e48da8f56a1c89fad1d3e407c
echo "=== B164 CLONE-ONLY SENSEX IDX_I DEPLOY ==="
test "$(id -un)" = opc || { echo BLOCKED_USER; exit 1; }
test -d "$ROOT" && test -d "$PRIVATE" || { echo BLOCKED_LAYOUT; exit 1; }
test "$(systemctl is-active bot-king.service)" = active || { echo BLOCKED_V1; exit 1; }
test "$(systemctl is-active botking-clone-v2.service)" = active || { echo BLOCKED_CLONE; exit 1; }
test "$(systemctl show botking-clone-v2.service -p WorkingDirectory --value)" = "$ROOT" || { echo BLOCKED_WORKDIR; exit 1; }
test -f "$ROOT/$TARGET" && test ! -L "$ROOT/$TARGET" || { echo BLOCKED_SOURCE; exit 1; }
test "$(curl --noproxy '*' -s -o /dev/null --max-time 5 -w '%{http_code}' http://127.0.0.1:8000/health)" = 200 || { echo BLOCKED_V1_HEALTH; exit 1; }
test "$(curl --noproxy '*' -s -o /dev/null --max-time 5 -w '%{http_code}' http://127.0.0.1:8002/clone-v2/health)" = 200 || { echo BLOCKED_CLONE_HEALTH; exit 1; }
blob() { python3 - "$1" <<'PY'
import hashlib,sys
with open(sys.argv[1],"rb") as f: d=f.read()
print(hashlib.sha1(b"blob "+str(len(d)).encode()+b"\0"+d).hexdigest())
PY
}
test "$(blob "$ROOT/$TARGET")" = "$OLD" || { echo BLOCKED_BASELINE_MISMATCH; exit 1; }
test "$(blob "$ROOT/dhan_feed.py")" = 63cf68124fc1449f6ce9fc1dc8359cadf038919d || { echo BLOCKED_FEED_MISMATCH; exit 1; }
WORK="$(mktemp -d "$PRIVATE/b164-idx-i.XXXXXXXX")"
chmod 700 "$WORK"
cp -p "$ROOT/$TARGET" "$WORK/$TARGET.backup"
curl --fail --silent --show-error --location --max-time 35 "https://raw.githubusercontent.com/vaishnavi596/volume-king/$PIN/backend/$TARGET" -o "$WORK/$TARGET"
test "$(blob "$WORK/$TARGET")" = "$NEW" || { echo BLOCKED_CANDIDATE_SHA; exit 1; }
/usr/bin/python3.9 -m py_compile "$WORK/$TARGET"
python3 - "$WORK/$TARGET" <<'PY'
from pathlib import Path
import sys
s=Path(sys.argv[1]).read_text()
assert '"SENSEX": ("IDX_I", 51)' in s
assert '"SENSEX": ("BSE_I", 51)' not in s
assert 'clone_market_diagnostic' in s
print("MAPPING_CONTRACT_PASS=YES")
PY
changed=0
rollback() {
  if [[ "$changed" = 1 ]]; then
    install -m 0600 "$WORK/$TARGET.backup" "$ROOT/.$TARGET.restore"
    mv -f "$ROOT/.$TARGET.restore" "$ROOT/$TARGET"
    sudo -n systemctl restart botking-clone-v2.service || true
    echo "ROLLBACK_ATTEMPTED=YES"
  fi
  echo "BACKUP_DIRECTORY=$WORK"
}
trap rollback ERR
install -m 0600 "$WORK/$TARGET" "$ROOT/.$TARGET.b164"
changed=1
mv -f "$ROOT/.$TARGET.b164" "$ROOT/$TARGET"
sudo -n systemctl restart botking-clone-v2.service
healthy=0
for _ in $(seq 1 20); do
  if [[ "$(systemctl is-active botking-clone-v2.service)" = active ]] &&
     [[ "$(curl --noproxy '*' -s -o /dev/null --max-time 3 -w '%{http_code}' http://127.0.0.1:8002/clone-v2/health)" = 200 ]]; then
    healthy=1; break
  fi
  sleep 1
done
test "$healthy" = 1
test "$(blob "$ROOT/$TARGET")" = "$NEW"
test "$(systemctl is-active bot-king.service)" = active
test "$(curl --noproxy '*' -s -o /dev/null --max-time 5 -w '%{http_code}' http://127.0.0.1:8000/health)" = 200
changed=0
trap - ERR
echo "B164_CLONE_MAPPING_DEPLOYED=YES"
echo "SENSEX_MAPPING=IDX_I_51"
echo "CLONE_HEALTH_HTTP=200"
echo "V1_HEALTH_HTTP=200"
echo "NO_DHAN_PROVIDER_REQUESTS_SENT=YES"
echo "BACKUP_DIRECTORY=$WORK"
