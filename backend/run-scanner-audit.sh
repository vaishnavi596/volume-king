#!/usr/bin/env bash
# Download only pinned diagnostic sources; never install/restart the server.
set -euo pipefail
umask 077
release=${1:?Pass the full reviewed 40-character GitHub commit SHA}
[[ $release =~ ^[0-9a-f]{40}$ ]] || { echo 'Invalid commit SHA; no requests made'; exit 2; }
shift
python_bin=$(command -v python3)
if test -x /opt/bot-king-server/.venv/bin/python; then
    python_bin=/opt/bot-king-server/.venv/bin/python
fi
command -v curl >/dev/null
stage=$(mktemp -d /tmp/botking-scanner-audit.XXXXXX)
trap 'rm -rf "$stage"' EXIT
mkdir -p "$stage/backend" "$stage/src"
base="https://raw.githubusercontent.com/vaishnavi596/volume-king/$release"
echo "Preparing read-only scanner audit • revision $release"
for file in backend/audit-dhan-51-candles.py backend/check-dhan-live.py src/server_feed.py src/scanner_engine.py; do
    curl --proto '=https' --tlsv1.2 --fail --silent --show-error --max-time 60 \
        "$base/$file" -o "$stage/$file"
    test -s "$stage/$file"
done
"$python_bin" -m py_compile "$stage/backend/audit-dhan-51-candles.py" \
    "$stage/backend/check-dhan-live.py" "$stage/src/scanner_engine.py"
echo "READ-ONLY scanner audit • revision $release"
echo 'No service restart, deployment, broker orders or credential output'
"$python_bin" "$stage/backend/audit-dhan-51-candles.py" --all-symbols "$@"
