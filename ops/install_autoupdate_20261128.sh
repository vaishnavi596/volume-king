#!/usr/bin/env bash
# One-time setup of the nightly updater. Run as opc:  bash install_autoupdate_20261128.sh <commit-sha>
set -Eeuo pipefail
SRC="${1:?commit sha}"
test "$(id -un)" = "opc" || { echo "BLOCKED: run as opc"; exit 1; }
BASE="https://raw.githubusercontent.com/vaishnavi596/volume-king/$SRC/ops"
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
curl -fsSL -m 40 --retry 3 "$BASE/botking_autoupdate.sh" -o "$W/u.sh"
bash -n "$W/u.sh"; grep -q 'LIVE_ORDERS_ENABLED = False' "$W/u.sh"
sudo install -m 755 "$W/u.sh" /usr/local/bin/botking-autoupdate.sh
sudo tee /etc/systemd/system/botking-autoupdate.service >/dev/null <<'U'
[Unit]
Description=BOT KING nightly server updater (paper only, live orders constant False)
After=network-online.target
[Service]
Type=oneshot
User=opc
ExecStart=/usr/local/bin/botking-autoupdate.sh
U
sudo tee /etc/systemd/system/botking-autoupdate.timer >/dev/null <<'U'
[Unit]
Description=BOT KING nightly updater timer
[Timer]
OnCalendar=*-*-* 20:45:00 UTC
Persistent=false
[Install]
WantedBy=timers.target
U
sudo systemctl daemon-reload
sudo systemctl enable --now botking-autoupdate.timer
/usr/local/bin/botking-autoupdate.sh --force || true
cat /home/opc/botking-clone-v2-private/autoupdate-status.json
systemctl list-timers botking-autoupdate.timer --no-pager | head -3
echo AUTOUPDATE_INSTALL_OK
