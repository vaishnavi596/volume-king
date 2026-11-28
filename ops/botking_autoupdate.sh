#!/usr/bin/env bash
# Nightly server auto-updater. Runs as opc via systemd timer. Night only (IST), never touches live orders.
set -uo pipefail
REPO="vaishnavi596/volume-king"
BRANCH="pilot/v1-pure-original-clone-phone-20261120"
PRIV="/home/opc/botking-clone-v2-private"
STATE="$PRIV/autoupdate-applied.sha"
STATUS="$PRIV/autoupdate-status.json"
mkdir -p "$PRIV"
status(){ printf '{"at":"%s","sha":"%s","result":"%s"}\n' "$(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST')" "$1" "$2" > "$STATUS.tmp" && mv "$STATUS.tmp" "$STATUS"; }
HM="$(TZ=Asia/Kolkata date +%H%M)"; HM=$((10#$HM))
if [ "${1:-}" != "--force" ] && { [ "$HM" -lt 30 ] || [ "$HM" -gt 530 ]; }; then echo "outside night window"; exit 0; fi
SHA="$(curl -fsSL -m 20 --retry 3 -H 'Accept: application/vnd.github.sha' "https://api.github.com/repos/$REPO/commits/$BRANCH" 2>/dev/null | tr -d '[:space:]')"
echo "$SHA" | grep -Eq '^[0-9a-f]{40}$' || { status "-" "CHECK_FAILED_NO_SHA"; exit 0; }
[ "$SHA" = "$(cat "$STATE" 2>/dev/null)" ] && { status "$SHA" "UP_TO_DATE"; exit 0; }
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
RAW="https://raw.githubusercontent.com/$REPO/$SHA"
curl -fsSL -m 40 --retry 3 "$RAW/ops/install_server_away_20261127.sh" -o "$W/i.sh" || { status "$SHA" "BLOCKED_NO_INSTALLER"; exit 0; }
curl -fsSL -m 40 --retry 3 "$RAW/backend/server_paper_positions.py" -o "$W/p.py" || { status "$SHA" "BLOCKED_DOWNLOAD"; exit 0; }
grep -q '^LIVE_ORDERS_ENABLED = False' "$W/p.py" || { status "$SHA" "BLOCKED_LIVE_ORDERS_GUARD"; exit 0; }
OUT="$(bash "$W/i.sh" "$SHA" 2>&1)"
if echo "$OUT" | grep -q SERVER_AWAY_INSTALL_OK; then echo "$SHA" > "$STATE"; status "$SHA" "UPDATED_OK"
else status "$SHA" "FAILED_ROLLED_BACK"; echo "$OUT" | tail -5; fi
