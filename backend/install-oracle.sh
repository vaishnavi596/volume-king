#!/usr/bin/env bash
# Install a reviewed, immutable GitHub revision on the existing BOT KING host.
set -euo pipefail
umask 077
release=${1:?Pass a full 40-character Git commit SHA}
[[ $release =~ ^[0-9a-f]{40}$ ]] || { echo 'Invalid release SHA'; exit 1; }
[[ $(id -u) == 0 ]] || { echo 'Run this installer with sudo'; exit 1; }
appdir=/opt/bot-king-server
nginxconf=/etc/nginx/conf.d/bot-king.conf
dropin=/etc/systemd/system/bot-king.service.d/gateway.conf
limits=/etc/nginx/conf.d/00-bot-king-limits.conf
test -x "$appdir/.venv/bin/python"
test -f "$appdir/server.py"
test -f "$nginxconf"
test -f /etc/letsencrypt/live/botkingrajesh.duckdns.org/fullchain.pem
getent passwd opc >/dev/null
stage=$(mktemp -d /tmp/botking-gateway.XXXXXX)
trap 'rm -rf "$stage"' EXIT
base="https://raw.githubusercontent.com/vaishnavi596/volume-king/$release"
curl --fail --silent --show-error --max-time 60 "$base/backend/server.py" -o "$stage/server.py"
curl --fail --silent --show-error --max-time 60 "$base/src/market_feed.py" -o "$stage/market_feed.py"
curl --fail --silent --show-error --max-time 60 "$base/backend/dhan_feed.py" -o "$stage/dhan_feed.py"
curl --fail --silent --show-error --max-time 60 "$base/backend/requirements.txt" -o "$stage/requirements.txt"
/usr/bin/python3 -m py_compile "$stage/server.py" "$stage/market_feed.py" "$stage/dhan_feed.py"

# Only these Python packages change; existing SmartAPI packages are retained.
install -o opc -g opc -m 600 "$stage/requirements.txt" "$appdir/gateway-requirements.txt"
sudo -u opc "$appdir/.venv/bin/python" -m pip install --disable-pip-version-check -r "$appdir/gateway-requirements.txt"
sudo -u opc "$appdir/.venv/bin/python" -m pip check

backup="/var/backups/bot-king/gateway-$(date -u +%Y%m%dT%H%M%SZ)-$$"
install -d -m 700 "$backup"
cp -p "$appdir/server.py" "$backup/server.py"
cp -p "$nginxconf" "$backup/nginx.conf"
for entry in market_feed.py dhan_feed.py; do
    if test -e "$appdir/$entry"; then cp -p "$appdir/$entry" "$backup/$entry"; fi
done
if test -e "$dropin"; then cp -p "$dropin" "$backup/gateway.conf"; fi
if test -e "$limits"; then cp -p "$limits" "$backup/limits.conf"; fi

rollback() {
    echo "Installation failed. Restoring previous server/configuration. Backup: $backup" >&2
    cp -p "$backup/server.py" "$appdir/server.py"
    cp -p "$backup/nginx.conf" "$nginxconf"
    for entry in market_feed.py dhan_feed.py; do
        if test -f "$backup/$entry"; then cp -p "$backup/$entry" "$appdir/$entry"; else rm -f "$appdir/$entry"; fi
    done
    if test -f "$backup/gateway.conf"; then cp -p "$backup/gateway.conf" "$dropin"; else rm -f "$dropin"; fi
    if test -f "$backup/limits.conf"; then cp -p "$backup/limits.conf" "$limits"; else rm -f "$limits"; fi
    restorecon -RF "$appdir" /etc/nginx/conf.d /etc/systemd/system/bot-king.service.d || true
    systemctl daemon-reload
    systemctl restart bot-king.service || true
    nginx -t && systemctl reload nginx || true
}
trap 'rollback' ERR

# A separate owner key protects login. Broker credentials never enter this file.
install -d -m 700 /etc/bot-king
if ! test -f /etc/bot-king/server.env; then
    /usr/bin/python3 - <<'PY'
from pathlib import Path
import secrets
value = secrets.token_urlsafe(48)
Path('/etc/bot-king/server.env').write_text('BOTKING_PAIRING_KEY=' + value + '\n')
PY
fi
chmod 600 /etc/bot-king/server.env
/usr/bin/python3 - <<'PY'
from pathlib import Path
lines = Path('/etc/bot-king/server.env').read_text().splitlines()
values = [line.partition('=')[2] for line in lines if line.startswith('BOTKING_PAIRING_KEY=')]
if len(values) != 1 or len(values[0]) < 32:
    raise SystemExit('Invalid owner key file; stopping')
Path('/home/opc/bot-king-pairing-key.txt').write_text(values[0] + '\n')
PY
chown opc:opc /home/opc/bot-king-pairing-key.txt
chmod 600 /home/opc/bot-king-pairing-key.txt
install -o opc -g opc -m 644 "$stage/server.py" "$appdir/server.py"
install -o opc -g opc -m 644 "$stage/market_feed.py" "$appdir/market_feed.py"
install -o opc -g opc -m 644 "$stage/dhan_feed.py" "$appdir/dhan_feed.py"
install -d -m 755 /etc/systemd/system/bot-king.service.d
cat > "$dropin" <<'UNIT'
[Service]
EnvironmentFile=/etc/bot-king/server.env
ExecStart=
ExecStart=/opt/bot-king-server/.venv/bin/python -m uvicorn server:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log --limit-concurrency 8 --timeout-keep-alive 5
UNIT
chmod 644 "$dropin"

cat > "$limits" <<'NGINX'
limit_req_zone $binary_remote_addr zone=botking_login:1m rate=5r/m;
NGINX
chmod 644 "$limits"
/usr/bin/python3 - <<'PY'
from pathlib import Path
path = Path('/etc/nginx/conf.d/bot-king.conf')
text = path.read_text()
marker = '# BOT KING gateway v1'
if marker not in text:
    target = 'location / { return 404; }'
    if text.count(target) != 1 or 'botkingrajesh.duckdns.org' not in text or 'listen 443 ssl' not in text:
        raise SystemExit('Unexpected Nginx configuration; stopping without guessing')
    block = '''# BOT KING gateway v1
    location = /v1/login {
        limit_req zone=botking_login burst=2 nodelay;
        limit_req_status 429;
        client_max_body_size 8k;
        access_log off;
        proxy_connect_timeout 3s;
        proxy_read_timeout 45s;
        proxy_pass http://127.0.0.1:8000/v1/login;
    }
    location /v1/ {
        client_max_body_size 8k;
        access_log off;
        proxy_connect_timeout 3s;
        proxy_read_timeout 45s;
        proxy_pass http://127.0.0.1:8000;
    }
    location / { return 404; }'''
    path.write_text(text.replace(target, block))
PY
# Expose only the reserved Dhan OAuth callback; disable access logs so
# OAuth tokenId query strings are never written to the Nginx access log.
/usr/bin/python3 - <<'PY'
from pathlib import Path
path = Path('/etc/nginx/conf.d/bot-king.conf')
config = path.read_text()
if 'location = /dhan/callback' not in config:
    anchor = 'location / { return 404; }'
    if config.count(anchor) != 1 or 'botkingrajesh.duckdns.org' not in config:
        raise SystemExit('Unexpected Nginx configuration; Dhan callback not added')
    block = '''location = /dhan/callback {
        access_log off;
        proxy_connect_timeout 3s;
        proxy_read_timeout 10s;
        proxy_pass http://127.0.0.1:8000/dhan/callback;
    }
    '''
    path.write_text(config.replace(anchor, block + anchor))
PY
# Route authenticated Dhan read-only endpoints to the same local gateway.
# Exact /dhan/callback location above takes precedence over this prefix.
/usr/bin/python3 - <<'PY'
from pathlib import Path
path = Path('/etc/nginx/conf.d/bot-king.conf')
config = path.read_text()
if 'location /dhan/ {' not in config:
    anchor = 'location / { return 404; }'
    if config.count(anchor) != 1 or 'botkingrajesh.duckdns.org' not in config:
        raise SystemExit('Unexpected Nginx configuration; Dhan proxy not added')
    block = '''location /dhan/ {
        client_max_body_size 8k;
        access_log off;
        proxy_connect_timeout 3s;
        proxy_read_timeout 45s;
        proxy_pass http://127.0.0.1:8000;
    }
    '''
    path.write_text(config.replace(anchor, block + anchor))
PY
restorecon -RF "$appdir" /etc/nginx/conf.d /etc/systemd/system/bot-king.service.d /etc/bot-king
nginx -t
systemctl daemon-reload
systemctl restart bot-king.service
ready=0
for attempt in {1..15}; do
    if curl --fail --silent --max-time 3 http://127.0.0.1:8000/health | /usr/bin/python3 -c 'import json,sys; assert json.load(sys.stdin).get("protocol") == 1' 2>/dev/null; then
        ready=1
        break
    fi
    sleep 1
done
test "$ready" = 1
systemctl reload nginx
sleep 1
curl --fail --silent --show-error --max-time 10 --resolve botkingrajesh.duckdns.org:443:127.0.0.1 https://botkingrajesh.duckdns.org/health
printf '\n'
code=$(curl --silent --max-time 10 --output /dev/null --write-out '%{http_code}' --resolve botkingrajesh.duckdns.org:443:127.0.0.1 -H 'Content-Type: application/json' -d '{"symbol":"NIFTY"}' https://botkingrajesh.duckdns.org/v1/expiries)
test "$code" = 401
trap - ERR
echo 'BOT KING gateway installed. Protected market-data endpoint returned 401 without a session, as expected.'
echo 'Owner key is in /home/opc/bot-king-pairing-key.txt. Do not paste it into chat.'
echo "Backup: $backup"
