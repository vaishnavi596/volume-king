#!/usr/bin/env bash
# BOT KING Clone gateway update to c197dce (+ dhan_renewal_health.py for /renewal-health).
# Read-only gateway: no orders, no Dhan calls here. Backs up, syntax-checks, restarts, rolls back on failure.
set -Eeuo pipefail
umask 077
SRC="c197dce"
BASE="https://raw.githubusercontent.com/vaishnavi596/volume-king"
ROOT="/home/opc/botking-clone-v2-runtime"
SERVICE="botking-clone-v2.service"
test "$(id -un)" = "opc" || { echo "BLOCKED: run as opc"; exit 1; }
test "$(systemctl is-active "$SERVICE")" = active || { echo "BLOCKED: service inactive"; exit 1; }
TS="$(date +%Y%m%d%H%M%S)"
WORK="$(mktemp -d "$ROOT/.upd.XXXXXXXX")"; trap 'rm -rf "$WORK"' EXIT
for f in clone_v2_gateway.py dhan_renewal_health.py; do
  curl -fsSL -m 40 --retry 3 "$BASE/$SRC/backend/$f" -o "$WORK/$f"
  python3 -m py_compile "$WORK/$f"
done
grep -q 'def regular_session_now' "$WORK/clone_v2_gateway.py" || { echo "BLOCKED: candidate lacks regular_session_now"; exit 1; }
for f in clone_v2_gateway.py dhan_renewal_health.py; do
  [ -f "$ROOT/$f" ] && cp -p "$ROOT/$f" "$ROOT/$f.rollback-$TS"
  install -m 640 "$WORK/$f" "$ROOT/$f"
done
sudo systemctl restart "$SERVICE"
sleep 4
if test "$(systemctl is-active "$SERVICE")" = active && curl -fsS -m 8 -o /dev/null http://127.0.0.1:8002/clone-v2/health; then
  echo "UPDATE_OK regular_session_now=$(grep -c regular_session_now "$ROOT/clone_v2_gateway.py") service=$(systemctl is-active "$SERVICE")"
else
  echo "FAILED: rolling back"
  for f in clone_v2_gateway.py dhan_renewal_health.py; do
    [ -f "$ROOT/$f.rollback-$TS" ] && cp -p "$ROOT/$f.rollback-$TS" "$ROOT/$f"
  done
  sudo systemctl restart "$SERVICE"; sleep 3
  echo "ROLLED_BACK service=$(systemctl is-active "$SERVICE")"; exit 1
fi
