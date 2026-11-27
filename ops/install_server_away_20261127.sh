#!/usr/bin/env bash
# B246: server signal runner journal + gateway read-only /signals routes. Analysis only, no orders.
# Run as opc:  bash install_server_away_20261127.sh <commit-sha>
set -Eeuo pipefail
umask 077
SRC="${1:?commit sha}"
BASE="https://raw.githubusercontent.com/vaishnavi596/volume-king"
ROOT="/home/opc/botking-clone-v2-runtime"
SIG="$ROOT/signals"
SERVICE="botking-clone-v2.service"
RUNNER="botking-clone-signal-runner.service"
test "$(id -un)" = "opc" || { echo "BLOCKED: run as opc"; exit 1; }
test "$(systemctl is-active "$SERVICE")" = active || { echo "BLOCKED: gateway inactive"; exit 1; }
TS="$(date +%Y%m%d%H%M%S)"
WORK="$(mktemp -d "$ROOT/.upd.XXXXXXXX")"; trap 'rm -rf "$WORK"' EXIT
mkdir -p "$SIG"
curl -fsSL -m 40 --retry 3 "$BASE/$SRC/backend/clone_v2_gateway.py" -o "$WORK/clone_v2_gateway.py"
curl -fsSL -m 40 --retry 3 "$BASE/$SRC/backend/clone_signal_runner.py" -o "$WORK/clone_signal_runner.py"
curl -fsSL -m 40 --retry 3 "$BASE/$SRC/backend/dhan_option_metrics.py" -o "$WORK/dhan_option_metrics.py"
curl -fsSL -m 40 --retry 3 "$BASE/$SRC/backend/server_paper_positions.py" -o "$WORK/server_paper_positions.py"
python3 -m py_compile "$WORK/server_paper_positions.py"
grep -q 'def open_option' "$WORK/server_paper_positions.py" || { echo "BLOCKED: wrong paper engine candidate"; exit 1; }
python3 -m py_compile "$WORK/dhan_option_metrics.py"
grep -q 'both CE and PE' "$WORK/dhan_option_metrics.py" || { echo "BLOCKED: wrong option-metrics candidate"; exit 1; }
for f in scanner_engine.py v3_live_candle_bridge.py v3_equity_session_calendar.py v3_m_forward.py; do
  curl -fsSL -m 40 --retry 3 "$BASE/$SRC/src/$f" -o "$WORK/$f"
done
for f in clone_v2_gateway.py clone_signal_runner.py scanner_engine.py v3_live_candle_bridge.py v3_equity_session_calendar.py v3_m_forward.py; do python3 -m py_compile "$WORK/$f"; done
grep -q '/clone-v2/signals/latest' "$WORK/clone_v2_gateway.py" || { echo "BLOCKED: wrong gateway candidate"; exit 1; }
grep -q 'preview-option' "$WORK/clone_v2_gateway.py" && grep -q 'lot_by_expiry' "$WORK/clone_signal_runner.py" && grep -q 'parse_option_contracts' "$WORK/clone_signal_runner.py" && grep -q 'open-option' "$WORK/clone_v2_gateway.py" && grep -q 'def change_events' "$WORK/clone_signal_runner.py" || { echo "BLOCKED: wrong runner candidate"; exit 1; }
for f in clone_v2_gateway.py dhan_option_metrics.py server_paper_positions.py; do [ -f "$ROOT/$f" ] && cp -p "$ROOT/$f" "$ROOT/$f.rollback-$TS"; install -m 640 "$WORK/$f" "$ROOT/$f"; done
for f in clone_signal_runner.py scanner_engine.py v3_live_candle_bridge.py v3_equity_session_calendar.py v3_m_forward.py; do
  [ -f "$SIG/$f" ] && cp -p "$SIG/$f" "$SIG/$f.rollback-$TS"; install -m 600 "$WORK/$f" "$SIG/$f"
done
if ! systemctl cat "$RUNNER" >/dev/null 2>&1; then
  sudo tee /etc/systemd/system/$RUNNER >/dev/null <<'U'
[Unit]
Description=BOT KING Clone read-only signal runner (analysis only, no orders)
After=botking-clone-v2.service
Wants=botking-clone-v2.service

[Service]
Type=simple
User=opc
WorkingDirectory=/home/opc/botking-clone-v2-runtime/signals
ExecStart=/usr/bin/python3.9 /home/opc/botking-clone-v2-runtime/signals/clone_signal_runner.py
Restart=on-failure
RestartSec=30
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full

[Install]
WantedBy=multi-user.target
U
  sudo systemctl daemon-reload
fi
sudo systemctl enable "$RUNNER" >/dev/null 2>&1 || true
sudo systemctl restart "$SERVICE" "$RUNNER"
sleep 5
if test "$(systemctl is-active "$SERVICE")" = active && curl -fsS -m 8 -o /dev/null http://127.0.0.1:8002/clone-v2/health; then
  echo "SERVER_AWAY_INSTALL_OK gateway=$(systemctl is-active "$SERVICE") runner=$(systemctl is-active "$RUNNER")"
else
  echo "FAILED: rolling back gateway"
  [ -f "$ROOT/clone_v2_gateway.py.rollback-$TS" ] && cp -p "$ROOT/clone_v2_gateway.py.rollback-$TS" "$ROOT/clone_v2_gateway.py"
  sudo systemctl restart "$SERVICE"; sleep 3
  echo "ROLLED_BACK gateway=$(systemctl is-active "$SERVICE")"; exit 1
fi
