#!/usr/bin/env bash
# BOT KING Clone-only one-file gateway update; never use initial installer here.
# Safe for operator review: no trading, no Dhan calls, no secrets in output.
set -Eeuo pipefail
umask 077
EXPECTED_OLD_BLOB="56ff3fea6b6d576e316f6f3782aa140650ef4528"
SOURCE_COMMIT="e3d1f2ece1535a6d28bebdb8e7a980e721c9aa26"
SOURCE_BLOB="5085fb254d47e8f7d8e9b94068e4bbedd4b08fd3"
ROOT="/home/opc/botking-clone-v2-runtime"
PRIVATE="/home/opc/botking-clone-v2-private"
TARGET="$ROOT/clone_v2_gateway.py"
SERVICE="botking-clone-v2.service"
OLD_SERVICE="bot-king.service"
test "$(id -un)" = "opc" || { echo "BLOCKED: Run as opc"; exit 1; }
test -d "$ROOT" && test -d "$PRIVATE" || { echo "BLOCKED: Clone directories missing"; exit 1; }
test -f "$TARGET" && test ! -L "$TARGET" || { echo "BLOCKED: Gateway missing or symlink"; exit 1; }
test "$(systemctl is-active "$SERVICE")" = active || { echo "BLOCKED: Clone service inactive"; exit 1; }
test "$(systemctl is-active "$OLD_SERVICE")" = active || { echo "BLOCKED: V1 service inactive"; exit 1; }
test "$(systemctl show "$SERVICE" -p User --value)" = opc || { echo "BLOCKED: Clone user changed"; exit 1; }
test "$(systemctl show "$SERVICE" -p WorkingDirectory --value)" = "$ROOT" || { echo "BLOCKED: Clone workdir changed"; exit 1; }
test "$(readlink /proc/$(systemctl show "$SERVICE" -p MainPID --value)/exe)" = "/usr/bin/python3.9" || { echo "BLOCKED: Python runtime changed"; exit 1; }
python3 - "$TARGET" "$EXPECTED_OLD_BLOB" <<'PY'
import hashlib, pathlib, sys
src = pathlib.Path(sys.argv[1]).read_bytes()
actual = hashlib.sha1(b"blob " + str(len(src)).encode() + b"\0" + src).hexdigest()
if actual != sys.argv[2]:
    raise SystemExit("BLOCKED: Existing Clone gateway differs; do not overwrite")
print("CURRENT_CLONE_GATEWAY_BLOB=VERIFIED")
PY
curl -fsS --max-time 5 -o /dev/null http://127.0.0.1:8002/clone-v2/health || { echo "BLOCKED: Clone health failed"; exit 1; }
curl -fsS --max-time 5 -o /dev/null http://127.0.0.1:8000/health || { echo "BLOCKED: V1 health failed"; exit 1; }
WORK="$(mktemp -d "$PRIVATE/b3-gateway-patch.XXXXXXXX")"
chmod 700 "$WORK"
CANDIDATE="$WORK/clone_v2_gateway.py"
BACKUP="$WORK/clone_v2_gateway.py.rollback"
# Download only the reviewed GitHub commit's one backend file.
curl --fail --location --silent --show-error --retry 2 --max-time 40 \
  "https://raw.githubusercontent.com/vaishnavi596/volume-king/$SOURCE_COMMIT/backend/clone_v2_gateway.py" \
  --output "$CANDIDATE"
# Git blob SHA protects the downloaded bytes, independent of transport.
python3 - "$CANDIDATE" "$SOURCE_BLOB" <<'PY'
import hashlib
import pathlib
import sys
src = pathlib.Path(sys.argv[1]).read_bytes()
blob = hashlib.sha1(b"blob " + str(len(src)).encode() + b"\0" + src).hexdigest()
if blob != sys.argv[2]:
    raise SystemExit("BLOCKED: Candidate blob mismatch")
text = src.decode("utf-8")
for required in ('option_known["FINNIFTY"] = ("IDX_I", 27)',
                 '"SENSEX": ("BSE_I", 51)', "clone_market_diagnostic",
                 '"/clone-v2/market/quotes"', '"/clone-v2/market/candles"',
                 "candle_miss_locks", "candle_cache_ttl_seconds = 180",
                 "candle_cache_max_entries = 100"):
    if required not in text:
        raise SystemExit("BLOCKED: Candidate contract incomplete")
print("CANDIDATE_BLOB=VERIFIED")
PY
/usr/bin/python3.9 -m py_compile "$CANDIDATE"
SITE="$ROOT/.venv/lib64/python3.9/site-packages"
test -d "$SITE" || { echo "BLOCKED: Clone dependency path absent"; exit 1; }
PYTHONPATH="$WORK:$SITE" /usr/bin/python3.9 -c \
  'import clone_v2_gateway; assert callable(clone_v2_gateway.create_app)'
cp -p "$TARGET" "$BACKUP"
cmp -s "$BACKUP" "$TARGET" || { echo "BLOCKED: Backup mismatch"; exit 1; }
echo "BACKUP_CREATED=YES"
echo "SOURCE_VERIFIED=YES"
echo "ONLY_CLONE_GATEWAY_FILE=YES"
# Replace one file atomically; restart ONLY the Clone service.
install -m 0600 "$CANDIDATE" "$ROOT/.clone_v2_gateway.py.new"
mv -f "$ROOT/.clone_v2_gateway.py.new" "$TARGET"
restorecon "$TARGET" 2>/dev/null || true
if sudo systemctl restart "$SERVICE"; then
  healthy=0
  for attempt in $(seq 1 25); do
    if test "$(systemctl is-active "$SERVICE")" = active &&
       curl -fsS --max-time 3 -o /dev/null http://127.0.0.1:8002/clone-v2/health 2>/dev/null; then
      healthy=1
      break
    fi
    sleep 1
  done
else
  healthy=0
fi
if test "$healthy" -eq 1 &&
   test "$(systemctl is-active "$OLD_SERVICE")" = active &&
   curl -fsS --max-time 5 -o /dev/null http://127.0.0.1:8000/health; then
  echo "CLONE_GATEWAY_UPDATED=YES"
  echo "CLONE_HEALTH_HTTP=200"
  echo "V1_UNCHANGED_HEALTH_HTTP=200"
  echo "FINNIFTY_MAPPING_CODE=PRESENT"
  echo "SENSEX_DIAGNOSTIC_CODE=PRESENT"
  echo "CLONE_CANDLE_SINGLEFLIGHT_CACHE=PRESENT"
  echo "BACKUP_DIR=$WORK"
  echo "NO_MARKET_REQUEST_SENT"
  exit 0
fi
echo "DEPLOY_CHECK_FAILED=ROLLBACK"
install -m 0600 "$BACKUP" "$ROOT/.clone_v2_gateway.py.rollback-new"
mv -f "$ROOT/.clone_v2_gateway.py.rollback-new" "$TARGET"
restorecon "$TARGET" 2>/dev/null || true
sudo systemctl restart "$SERVICE" || true
if test "$(systemctl is-active "$SERVICE")" = active &&
   curl -fsS --max-time 5 -o /dev/null http://127.0.0.1:8002/clone-v2/health; then
  echo "CLONE_ROLLBACK_HEALTH_HTTP=200"
else
  echo "CLONE_ROLLBACK_HEALTH_HTTP=FAILED_MANUAL_REVIEW_REQUIRED"
fi
echo "BACKUP_DIR=$WORK"
exit 1
