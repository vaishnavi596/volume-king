#!/usr/bin/env bash
# V3 B159: deploy TWO reviewed Clone-only diagnostics files, never V1.
# No Dhan/quote/candle request, no credentials printed. Automatic rollback.
set -Eeuo pipefail
umask 077
ROOT=/home/opc/botking-clone-v2-runtime
PRIVATE=/home/opc/botking-clone-v2-private
SERVICE=botking-clone-v2.service
V1=bot-king.service
PY=/usr/bin/python3.9
FEED=dhan_feed.py
GATEWAY=clone_v2_gateway.py
OLD_FEED_BLOB=dcaab25d5b55155868efcaae1f8e7c7d14b00217
OLD_GATEWAY_BLOB=8c53eb8900564752e42b3d1d1368967ad7b1b809
NEW_FEED_BLOB=63cf68124fc1449f6ce9fc1dc8359cadf038919d
NEW_GATEWAY_BLOB=0db7edfc06134781581bf31d05db092f05bcd3b3
FEED_COMMIT=a4a8786f32284950f28e664165ea0828f6543411
GATEWAY_COMMIT=ccfe90f95aa3bb0cfc3148a499bc3c1b76f57769
echo '=== V3 B159 CLONE-ONLY SAFE DIAGNOSTICS DEPLOY ==='
test "$(id -un)" = opc || { echo "BLOCKED_USER_NOT_OPC"; exit 1; }
test -d "$ROOT" && test -d "$PRIVATE" || { echo "BLOCKED_CLONE_LAYOUT"; exit 1; }
test "$(systemctl is-active "$SERVICE")" = active || { echo "BLOCKED_CLONE_INACTIVE"; exit 1; }
test "$(systemctl is-active "$V1")" = active || { echo "BLOCKED_V1_NOT_ACTIVE"; exit 1; }
test "$(systemctl show "$SERVICE" -p User --value)" = opc || { echo "BLOCKED_SERVICE_USER"; exit 1; }
test "$(systemctl show "$SERVICE" -p WorkingDirectory --value)" = "$ROOT" || { echo "BLOCKED_CLONE_WORKDIR"; exit 1; }
test -x "$PY" || { echo "BLOCKED_PYTHON"; exit 1; }
test -f "$ROOT/$FEED" && test ! -L "$ROOT/$FEED" || { echo "BLOCKED_FEED_FILE"; exit 1; }
test -f "$ROOT/$GATEWAY" && test ! -L "$ROOT/$GATEWAY" || { echo "BLOCKED_GATEWAY_FILE"; exit 1; }
test "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://127.0.0.1:8002/clone-v2/health)" = 200 || { echo "BLOCKED_CLONE_HEALTH"; exit 1; }
test "$(curl -s -o /dev/null --max-time 5 -w '%{http_code}' http://127.0.0.1:8000/health)" = 200 || { echo "BLOCKED_V1_HEALTH"; exit 1; }
blob() {
  python3 - "$1" <<'PY'
import hashlib,sys
with open(sys.argv[1],"rb") as handle: data=handle.read()
print(hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest())
PY
}
actual_feed="$(blob "$ROOT/$FEED")"
actual_gateway="$(blob "$ROOT/$GATEWAY")"
if [[ "$actual_feed" != "$OLD_FEED_BLOB" || "$actual_gateway" != "$OLD_GATEWAY_BLOB" ]]; then
  echo "BLOCKED_DEPLOYED_BLOB_DIFFERS_FROM_REVIEWED_BASELINE"
  echo "OLD_FILES_UNCHANGED=YES"
  exit 1
fi
WORK="$(mktemp -d "$PRIVATE/b159-safe.XXXXXXXX")"
chmod 700 "$WORK"
echo "BASELINE_SOURCE_MATCH=YES"
cp -p "$ROOT/$FEED" "$WORK/$FEED.backup"
cp -p "$ROOT/$GATEWAY" "$WORK/$GATEWAY.backup"
test "$(blob "$WORK/$FEED.backup")" = "$OLD_FEED_BLOB"
test "$(blob "$WORK/$GATEWAY.backup")" = "$OLD_GATEWAY_BLOB"
echo "ROLLBACK_FILES_VERIFIED=YES"
curl --fail --silent --show-error --location --max-time 35 \
  "https://raw.githubusercontent.com/vaishnavi596/volume-king/$FEED_COMMIT/backend/$FEED" -o "$WORK/$FEED"
curl --fail --silent --show-error --location --max-time 35 \
  "https://raw.githubusercontent.com/vaishnavi596/volume-king/$GATEWAY_COMMIT/backend/$GATEWAY" -o "$WORK/$GATEWAY"
test "$(blob "$WORK/$FEED")" = "$NEW_FEED_BLOB" || { echo "BLOCKED_CANDIDATE_FEED_BLOB"; exit 1; }
test "$(blob "$WORK/$GATEWAY")" = "$NEW_GATEWAY_BLOB" || { echo "BLOCKED_CANDIDATE_GATEWAY_BLOB"; exit 1; }
"$PY" -m py_compile "$WORK/$FEED" "$WORK/$GATEWAY"
python3 - "$WORK/$FEED" "$WORK/$GATEWAY" <<'PY'
from pathlib import Path
import sys
feed=Path(sys.argv[1]).read_text()
gateway=Path(sys.argv[2]).read_text()
for text in ('class DhanUpstreamError', 'upstream_http_4xx', 'upstream_http_5xx', 'upstream_transport', 'upstream_payload', 'upstream_rejection'):
    if text not in feed or (text != 'class DhanUpstreamError' and text not in gateway):
        raise SystemExit("BLOCKED_B159_CONTRACT_MISSING")
for text in ('clone_market_diagnostic', '"SENSEX": ("BSE_I", 51)', '/clone-v2/market/quotes', '/clone-v2/market/candles'):
    if text not in gateway: raise SystemExit("BLOCKED_CLONE_CONTRACT_MISSING")
print("B159_REVIEWED_CONTRACT=PASS")
PY
echo "ONLY_CLONE_FILES_TO_CHANGE=2"
rollback() {
  echo "DEPLOY_FAILED_ROLLBACK_BEGIN"
  install -m 0600 "$WORK/$FEED.backup" "$ROOT/.$FEED.rollback-new"
  install -m 0600 "$WORK/$GATEWAY.backup" "$ROOT/.$GATEWAY.rollback-new"
  mv -f "$ROOT/.$FEED.rollback-new" "$ROOT/$FEED"
  mv -f "$ROOT/.$GATEWAY.rollback-new" "$ROOT/$GATEWAY"
  restorecon "$ROOT/$FEED" "$ROOT/$GATEWAY" 2>/dev/null || true
  sudo -n systemctl restart "$SERVICE" || true
  if [[ "$(systemctl is-active "$V1")" == active ]] && \
     [[ "$(blob "$ROOT/$FEED")" == "$OLD_FEED_BLOB" ]] && \
     [[ "$(blob "$ROOT/$GATEWAY")" == "$OLD_GATEWAY_BLOB" ]]; then
    echo "ROLLBACK_FILES_RESTORED=YES"
  else
    echo "ROLLBACK_REQUIRES_MANUAL_REVIEW=YES"
  fi
  echo "BACKUP_DIRECTORY=$WORK"
  exit 1
}
install -m 0600 "$WORK/$FEED" "$ROOT/.$FEED.b159-new"
install -m 0600 "$WORK/$GATEWAY" "$ROOT/.$GATEWAY.b159-new"
mv -f "$ROOT/.$FEED.b159-new" "$ROOT/$FEED"
mv -f "$ROOT/.$GATEWAY.b159-new" "$ROOT/$GATEWAY"
restorecon "$ROOT/$FEED" "$ROOT/$GATEWAY" 2>/dev/null || true
sudo -n systemctl restart "$SERVICE" || rollback
healthy=0
for attempt in $(seq 1 20); do
  if [[ "$(systemctl is-active "$SERVICE")" == active ]] && \
     [[ "$(curl -s -o /dev/null --max-time 3 -w '%{http_code}' http://127.0.0.1:8002/clone-v2/health)" == 200 ]]; then
    healthy=1
    break
  fi
  sleep 1
done
if [[ "$healthy" != 1 || "$(systemctl is-active "$V1")" != active ||
      "$(blob "$ROOT/$FEED")" != "$NEW_FEED_BLOB" ||
      "$(blob "$ROOT/$GATEWAY")" != "$NEW_GATEWAY_BLOB" ||
      "$(curl -s -o /dev/null --max-time 4 -w '%{http_code}' http://127.0.0.1:8000/health)" != 200 ]]; then
  rollback
fi
echo "B159_CLONE_GATEWAY_AND_FEED_DEPLOYED=YES"
echo "CLONE_HEALTH_HTTP=200"
echo "V1_HEALTH_HTTP=200"
echo "NO_MARKET_PROVIDER_REQUESTS_SENT=YES"
echo "NO_V1_CONFIG_EDIT=YES"
echo "BACKUP_DIRECTORY=$WORK"
