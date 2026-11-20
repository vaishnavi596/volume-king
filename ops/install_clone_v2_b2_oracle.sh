#!/usr/bin/env bash
# Owner-run B2 Oracle installer. Run from clone repo root as opc in an
# interactive SSH session. Never touches original V1 or previous V2 service.
set -euo pipefail
umask 077

if [ "$(id -un)" != "opc" ]; then
  echo 'BLOCKED: run as opc'; exit 1
fi
if [ ! -f backend/clone_v2_gateway.py ]; then
  echo 'BLOCKED: run from reviewed clone repo root'; exit 1
fi
if [ ! -t 0 ] && [ ! -f /home/opc/botking-clone-v2-private/ssk ]; then
  echo 'BLOCKED: interactive SSK provisioning needed, do not pass key in arguments'; exit 1
fi
if [ "$(systemctl is-active bot-king.service || true)" != "active" ]; then
  echo 'BLOCKED: V1 service must be healthy'; exit 1
fi
if [ "$(curl -sS -o /dev/null --max-time 8 -w '%{http_code}' http://127.0.0.1:8000/health)" != "200" ]; then
  echo 'BLOCKED: original V1 health changed'; exit 1
fi
if ss -lnt '( sport = :8002 )' | grep -q LISTEN; then
  echo 'BLOCKED: 8002 already allocated; review before replacing'; exit 1
fi
if [ -e /etc/systemd/system/botking-clone-v2.service ]; then
  echo 'BLOCKED: existing unit; review before replacing'; exit 1
fi

ROOT=/home/opc/botking-clone-v2-runtime
PRIVATE=/home/opc/botking-clone-v2-private
install -d -m 700 "$ROOT" "$PRIVATE"
if [ ! -f "$PRIVATE/ssk" ]; then
  printf 'Enter approved clone Server Access Key (hidden, >=32 characters): ' >&2
  IFS= read -r -s CLONE_SSK
  printf '\n' >&2
  if [ "${#CLONE_SSK}" -lt 32 ] || [ "${#CLONE_SSK}" -gt 512 ]; then
    echo 'BLOCKED: invalid key length'; unset CLONE_SSK; exit 1
  fi
  (umask 077; printf '%s' "$CLONE_SSK" > "$PRIVATE/ssk")
  unset CLONE_SSK
  chmod 600 "$PRIVATE/ssk"
fi
if [ "$(stat -c %a "$PRIVATE")" != "700" ] || [ "$(stat -c %a "$PRIVATE/ssk")" != "600" ]; then
  echo 'BLOCKED: protected SSK permissions required'; exit 1
fi

cp backend/clone_v2_gateway.py "$ROOT/clone_v2_gateway.py"
chmod 600 "$ROOT/clone_v2_gateway.py"
python3 -m py_compile "$ROOT/clone_v2_gateway.py"
python3 -m venv "$ROOT/.venv"
"$ROOT/.venv/bin/python" -m pip install --disable-pip-version-check --no-input -q \
  'fastapi==0.115.12' 'uvicorn==0.34.2' 'httpx==0.28.1'
BOTKING_CLONE_V2_SSK_FILE="$PRIVATE/ssk" "$ROOT/.venv/bin/python" - <<'PY'
from pathlib import Path
import sys
sys.path.insert(0, '/home/opc/botking-clone-v2-runtime')
from clone_v2_gateway import create_app
from fastapi.testclient import TestClient
app = create_app()
with TestClient(app) as client:
    assert client.get('/clone-v2/health').status_code == 200
    assert client.get('/clone-v2/status').status_code == 403
    assert client.get('/dhan/status').status_code == 404
    assert client.get('/v2-pilot/health').status_code == 404
print('CLONE_B2_LOCAL_AUTH_NEGATIVE_TEST=PASS')
PY

TMP_UNIT="$(mktemp)"
trap 'rm -f "$TMP_UNIT"' EXIT
cat > "$TMP_UNIT" <<'UNIT'
[Unit]
Description=BOT KING Clone V2 SSK read-only login gateway
After=network-online.target bot-king.service
Wants=network-online.target
[Service]
Type=simple
User=opc
Group=opc
WorkingDirectory=/home/opc/botking-clone-v2-runtime
Environment=BOTKING_CLONE_V2_SSK_FILE=/home/opc/botking-clone-v2-private/ssk
ExecStart=/home/opc/botking-clone-v2-runtime/.venv/bin/uvicorn clone_v2_gateway:create_app --factory --host 127.0.0.1 --port 8002 --workers 1
Restart=on-failure
RestartSec=5
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=full
[Install]
WantedBy=multi-user.target
UNIT
sudo -n install -o root -g root -m 0644 "$TMP_UNIT" /etc/systemd/system/botking-clone-v2.service
sudo -n systemctl daemon-reload
sudo -n systemctl enable --now botking-clone-v2.service >/dev/null
if [ "$(systemctl is-active botking-clone-v2.service)" != "active" ] || \
   [ "$(curl -sS -o /dev/null --max-time 8 -w '%{http_code}' http://127.0.0.1:8002/clone-v2/health)" != "200" ] || \
   [ "$(curl -sS -o /dev/null --max-time 8 -w '%{http_code}' http://127.0.0.1:8002/clone-v2/status)" != "403" ]; then
  sudo -n systemctl stop botking-clone-v2.service || true
  sudo -n systemctl disable botking-clone-v2.service || true
  echo 'BLOCKED: clone service validation failed; stopped for review'; exit 1
fi
test "$(systemctl is-active bot-king.service)" = active
test "$(curl -sS -o /dev/null -w '%{http_code}' --max-time 8 http://127.0.0.1:8000/health)" = 200
echo 'CLONE_B2_LOCAL_SERVICE=ACTIVE'
echo 'ORIGINAL_V1=HEALTHY_UNCHANGED'
echo 'CLONE_B2_PUBLIC_HTTPS_PROXY=NOT_CONFIGURED_BY_THIS_INSTALLER'
echo 'CLONE_B2_PHONE_SSK_LOGIN=NOT_VERIFIED'
echo 'CLONE_B2_MARKET_DATA=NOT_CONNECTED'
