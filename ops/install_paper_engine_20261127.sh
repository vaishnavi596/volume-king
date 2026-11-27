#!/usr/bin/env bash
# B244 server PAPER position manager. Paper only: no orders, no order endpoints.
# Backs up, syntax-checks, restarts, rolls back on failure. Usage: bash this.sh <commit-sha>
set -Eeuo pipefail
umask 077
SRC="${1:?commit sha}"
BASE="https://raw.githubusercontent.com/vaishnavi596/volume-king"
ROOT="/home/opc/botking-clone-v2-runtime"
SERVICE="botking-clone-v2.service"
DROPIN_DIR="/etc/systemd/system/${SERVICE}.d"
test "$(id -un)" = "opc" || { echo "BLOCKED: run as opc"; exit 1; }
test "$(systemctl is-active "$SERVICE")" = active || { echo "BLOCKED: service inactive"; exit 1; }
TS="$(date +%Y%m%d%H%M%S)"
WORK="$(mktemp -d "$ROOT/.upd.XXXXXXXX")"; trap 'rm -rf "$WORK"' EXIT
FILES="clone_v2_gateway.py server_paper_positions.py"
for f in $FILES; do
  curl -fsSL -m 40 --retry 3 "$BASE/$SRC/backend/$f" -o "$WORK/$f"
  python3 -m py_compile "$WORK/$f"
done
grep -q 'B244: server-side PAPER' "$WORK/clone_v2_gateway.py" || { echo "BLOCKED: wrong candidate"; exit 1; }
grep -q 'LIVE_ORDERS_ENABLED = False' "$WORK/server_paper_positions.py" || { echo "BLOCKED: live flag"; exit 1; }
for f in $FILES; do
  [ -f "$ROOT/$f" ] && cp -p "$ROOT/$f" "$ROOT/$f.rollback-$TS"
  install -m 640 "$WORK/$f" "$ROOT/$f"
done
sudo mkdir -p "$DROPIN_DIR"
printf '[Service]\nEnvironment=BOTKING_PAPER_STATE_FILE=%s/paper_state.json\nEnvironment=BOTKING_PAPER_POLL=1\n' "$ROOT" | sudo tee "$DROPIN_DIR/paper.conf" >/dev/null
sudo systemctl daemon-reload
sudo systemctl restart "$SERVICE"
sleep 4
if test "$(systemctl is-active "$SERVICE")" = active && curl -fsS -m 8 -o /dev/null http://127.0.0.1:8002/clone-v2/health; then
  echo "PAPER_ENGINE_INSTALL_OK service=$(systemctl is-active "$SERVICE") routes=$(grep -c '/clone-v2/paper/' "$ROOT/clone_v2_gateway.py")"
else
  echo "FAILED: rolling back"
  for f in $FILES; do [ -f "$ROOT/$f.rollback-$TS" ] && cp -p "$ROOT/$f.rollback-$TS" "$ROOT/$f"; done
  sudo rm -f "$DROPIN_DIR/paper.conf"; sudo systemctl daemon-reload
  sudo systemctl restart "$SERVICE"; sleep 3
  echo "ROLLED_BACK service=$(systemctl is-active "$SERVICE")"; exit 1
fi
