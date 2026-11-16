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
# systemd reads EnvironmentFile as manager/root; an unprivileged service
# user does NOT need traversal access to /etc/bot-king for OAuth sessions.
# The *actual* token source is checked below under the effective service user.
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
# Port ownership and Dhan outbound 443 tests are metadata-only; do not
# send pairing keys or token headers through these network checks.
if command -v ss >/dev/null 2>&1; then
    listeners=$(ss -H -ltn '( sport = :8000 )' 2>/dev/null || true)
    if grep -Eq '127[.]0[.]0[.]1:8000([[:space:]]|$)' <<< "$listeners"; then
        echo 'FastAPI port 8000: loopback-only listener verified'
    else
        echo 'FastAPI port 8000: missing/unsafe binding (must be 127.0.0.1)'
        exit 2
    fi
else
    echo 'Port binding visibility: ss unavailable (requires manual check)'
fi
if command -v curl >/dev/null; then
    if curl --silent --show-error --output /dev/null --connect-timeout 3 --max-time 8 \
            --noproxy '*' 'https://api.dhan.co/v2/profile'; then
        echo 'Dhan API TLS 443 egress: reachable (NO authorization/entitlement checked)'
    else
        echo 'Dhan API TLS 443 egress: FAILED (DNS/TLS/route/firewall)'
        exit 2
    fi
    if curl --silent --show-error --output /dev/null --connect-timeout 3 --max-time 8 \
            --noproxy '*' 'https://auth.dhan.co/'; then
        echo 'Dhan OAuth TLS 443 egress: reachable (NO login/token requested)'
    else
        echo 'Dhan OAuth TLS 443 egress: FAILED (DNS/TLS/route/firewall)'
        exit 2
    fi
fi
if curl --fail --silent --max-time 3 http://127.0.0.1:8000/health >/dev/null; then
    echo 'local gateway health: HTTP success (not Dhan market-data proof)'
else
    echo 'local gateway health: unavailable'
    exit 2
fi
echo 'Readiness checks passed; token validity and live quotes remain unverified.'
