#!/usr/bin/env bash
# BOT KING Clone: install the READ-ONLY server-side signal runner on Oracle.
# Run as root:  sudo bash install_signal_runner_20261127.sh
# Touches only: /home/opc/botking-clone-v2-runtime/signals/ and one new systemd
# unit. Does not change the gateway, tokens or any existing service.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]] || { echo "BLOCKED: run with sudo"; exit 1; }
BASE=https://raw.githubusercontent.com/vaishnavi596/volume-king/pilot/v1-pure-original-clone-phone-20261120
DIR=/home/opc/botking-clone-v2-runtime/signals
UNIT=/etc/systemd/system/botking-clone-signal-runner.service
[[ -d /home/opc/botking-clone-v2-runtime ]] || { echo "BLOCKED: runtime dir missing"; exit 1; }
install -d -o opc -g opc -m 0700 "$DIR"
fetch() { curl -fsSL "$BASE/$1" -o "$DIR/$2" && python3.9 -m py_compile "$DIR/$2"; chown opc:opc "$DIR/$2"; chmod 0600 "$DIR/$2"; }
fetch backend/clone_signal_runner.py clone_signal_runner.py
fetch src/scanner_engine.py scanner_engine.py
fetch src/v3_live_candle_bridge.py v3_live_candle_bridge.py
fetch src/v3_equity_session_calendar.py v3_equity_session_calendar.py
echo "FILES_OK"
echo "--- one test cycle (read-only) ---"
sudo -u opc env BOTKING_SIGNAL_OUT=/home/opc/botking-clone-v2-private/signals-latest.json \
  python3.9 "$DIR/clone_signal_runner.py" --once
cat > "$UNIT" <<'U'
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
systemctl daemon-reload
systemctl enable --now botking-clone-signal-runner.service
sleep 3
systemctl is-active botking-clone-signal-runner.service
echo "INSTALL_OK"
