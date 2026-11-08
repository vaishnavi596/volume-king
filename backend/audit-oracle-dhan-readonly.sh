#!/usr/bin/env bash
# Read-only Oracle Dhan readiness audit. Never prints token, key, or env values.
set -euo pipefail
appdir=/opt/bot-king-server
token=/etc/bot-king/dhan-token
service=bot-king.service
echo 'BOT KING Dhan readiness (read-only)'
if ! command -v systemctl >/dev/null; then echo 'systemd: unavailable'; exit 2; fi
user=$(systemctl show "$service" -p User --value 2>/dev/null || true)
if [[ -z "$user" ]]; then
    echo 'service user: root/default (verify unit manually)'
    user=root
else
    echo 'service user: configured'
fi
if ! id "$user" >/dev/null 2>&1; then echo 'service user: invalid'; exit 2; fi
if [[ ! -f "$token" ]]; then echo 'Dhan token file: missing'; exit 2; fi
echo 'Dhan token file: present'
# A present token is unusable if the service cannot traverse its parent directory.
if [[ $(id -u) == 0 ]] && command -v runuser >/dev/null; then
    if runuser -u "$user" -- test -x /etc/bot-king; then
        echo 'Dhan credential directory traversable by service user: yes'
    else
        echo 'Dhan credential directory traversable by service user: NO'
        exit 2
    fi
fi
# Only report whether Dhan client configuration exists; never display its value.
if [[ -f /etc/bot-king/server.env ]]; then
    if grep -Eq '^DHAN_CLIENT_ID=[^[:space:]]+' /etc/bot-king/server.env; then
        echo 'Dhan client ID setting: present'
    else
        echo 'Dhan client ID setting: missing or empty'
        exit 2
    fi
else
    echo 'Server environment file: missing'
    exit 2
fi
# Check effective readability without displaying credentials.
if [[ $(id -u) == 0 ]]; then
    if command -v runuser >/dev/null && runuser -u "$user" -- test -r "$token"; then
        echo 'Dhan token readable by service user: yes'
    else
        echo 'Dhan token readable by service user: NO'
        exit 2
    fi
else
    echo 'Service-user token readability: requires sudo (not checked)'
fi
for f in server.py market_feed.py dhan_feed.py; do
    if [[ -s "$appdir/$f" ]]; then echo "$f: present"; else echo "$f: missing or empty"; exit 2; fi
done
if command -v nginx >/dev/null; then
    if nginx -t >/dev/null 2>&1; then echo 'nginx syntax: valid'; else echo 'nginx syntax: FAILED or insufficient permissions'; exit 2; fi
fi
if curl --fail --silent --max-time 3 http://127.0.0.1:8000/health >/dev/null; then
    echo 'local gateway health: HTTP success (not Dhan market-data proof)'
else
    echo 'local gateway health: unavailable'
    exit 2
fi
echo 'Readiness checks passed; token validity and live quotes remain unverified.'
