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
# The authenticated service can use a private persisted OAuth session
# instead of a manually provisioned legacy token. Never demand both.
envfile=/etc/bot-king/server.env
if [[ ! -f "$envfile" ]]; then echo 'Server environment file: missing'; exit 2; fi
session_file=$(sed -n 's/^DHAN_SESSION_FILE=//p' "$envfile" | head -n 1)
if [[ -n "$session_file" && "$session_file" != /* ]]; then
    echo 'OAuth session path: invalid (must be absolute)'
    exit 2
fi
has_token=0
if [[ -f "$token" ]]; then
    echo 'Legacy Dhan token file: present'
    has_token=1
else
    echo 'Legacy Dhan token file: not provisioned (OAuth may be sufficient)'
fi
has_oauth=0
if [[ -n "$session_file" && -f "$session_file" ]]; then
    echo 'Private OAuth session file: present (expiry not verified)'
    has_oauth=1
else
    echo 'Private OAuth session file: absent'
fi
if (( ! has_token && ! has_oauth )); then
    echo 'No readable token source configured; Dhan market data unavailable'
    exit 2
fi
if [[ $(id -u) == 0 ]] && command -v runuser >/dev/null; then
    if ! runuser -u "$user" -- test -x /etc/bot-king; then
        echo 'Dhan environment directory not traversable by service user'
        exit 2
    fi
fi
# Only report whether Dhan client configuration exists; never display its value.
if [[ -f "$envfile" ]]; then
    if grep -Eq '^DHAN_CLIENT_ID=[^[:space:]]+' "$envfile"; then
        echo 'Dhan client ID setting: present'
    else
        echo 'Dhan client ID setting: missing or empty'
        exit 2
    fi
else
    echo 'Server environment file: missing'
    exit 2
fi
# Check effective access to at least one configured token source; never
# print the token, session contents, paths, or sensitive environment variables.
if [[ $(id -u) == 0 ]]; then
    readable=0
    if (( has_oauth )) && runuser -u "$user" -- test -r "$session_file"; then
        echo 'Private OAuth session readable by service user: yes'
        readable=1
    fi
    if (( has_token )) && runuser -u "$user" -- test -r "$token"; then
        echo 'Legacy Dhan token readable by service user: yes'
        readable=1
    fi
    if (( ! readable )); then
        echo 'Service user cannot read either token source'
        exit 2
    fi
else
    echo 'Service-user credential readability: requires sudo (not checked)'
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
