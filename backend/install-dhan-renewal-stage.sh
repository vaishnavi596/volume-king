#!/usr/bin/env bash
# Stage reviewed Dhan renewal code without rotating credentials or enabling timer.
set -euo pipefail
umask 077
release=${1:?Pass full reviewed Git commit SHA}
[[ $release =~ ^[0-9a-f]{40}$ ]] || { echo 'Invalid commit SHA'; exit 1; }
[[ $(id -u) == 0 ]] || { echo 'Run with sudo'; exit 1; }
app=/opt/bot-king-server
test -x "$app/.venv/bin/python"
test -f /etc/bot-king/dhan-token
test -f /etc/bot-king/server.env
stage=$(mktemp -d /tmp/botking-renewal.XXXXXX)
trap 'rm -rf "$stage"' EXIT
base="https://raw.githubusercontent.com/vaishnavi596/volume-king/$release"
files=(__init__.py dhan_renewal_policy.py dhan_token_expiry.py dhan_expiry_store.py dhan_web_token_renew.py dhan_renewal_scheduler.py)
for name in "${files[@]}"; do
    curl -fsSL --max-time 60 "$base/backend/$name" -o "$stage/$name"
    if [[ "$name" != "__init__.py" ]]; then
        test -s "$stage/$name" || { echo "Missing $name"; exit 1; }
    fi
done
for name in botking-dhan-renewal.service.example botking-dhan-renewal.timer.example; do
    curl -fsSL --max-time 60 "$base/backend/systemd/$name" -o "$stage/$name"
    test -s "$stage/$name"
done
"$app/.venv/bin/python" -m compileall -q "$stage"
# No writes until downloads and compilation pass.
install -d -o root -g root -m 755 "$app/backend"
for name in "${files[@]}"; do
    install -o root -g root -m 644 "$stage/$name" "$app/backend/$name"
done
install -o root -g root -m 644 "$stage/botking-dhan-renewal.service.example" /etc/systemd/system/botking-dhan-renewal.service
install -o root -g root -m 644 "$stage/botking-dhan-renewal.timer.example" /etc/systemd/system/botking-dhan-renewal.timer
systemctl daemon-reload
# Deliberately no systemctl enable/start. This installer never calls Dhan.
echo "Renewal files staged. Timer remains disabled; no token rotated."
echo "Before enabling: validate DHAN_CLIENT_ID, trusted expiry file, token source and recovery state."
