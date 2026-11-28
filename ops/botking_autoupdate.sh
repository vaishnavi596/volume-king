#!/usr/bin/env bash
# Server auto-updater. Runs as opc via a systemd timer EVERY 30 MINUTES. Checks GitHub often, but only APPLIES new code
# while the market is closed (Mon-Fri before 09:00 or from 15:45 IST, and all weekend). Never touches live orders.
set -uo pipefail
REPO="vaishnavi596/volume-king"
BRANCH="pilot/v1-pure-original-clone-phone-20261120"
PRIV="/home/opc/botking-clone-v2-private"
STATE="$PRIV/autoupdate-applied.sha"
APPLIED_AT="$PRIV/autoupdate-applied.at"
STATUS="$PRIV/autoupdate-status.json"
mkdir -p "$PRIV"
exec 9>"$PRIV/autoupdate.lock"; flock -n 9 || exit 0
RP="$PRIV/replay-latest.json"
replay(){ [ -f /home/opc/botking-clone-v2-runtime/signals/clone_replay.py ] || return 0
  # only when missing or older than 20 hours (a check every 30 min must not re-run a 5-minute replay)
  if [ ! -f "$RP" ] || [ -n "$(find "$RP" -mmin +1200 2>/dev/null)" ] || [ "${1:-}" = "now" ]; then
    (cd /home/opc/botking-clone-v2-runtime/signals && timeout 290 python3.9 clone_replay.py >/dev/null 2>&1) || true
  fi; }
status(){ printf '{"at":"%s","applied_at":"%s","sha":"%s","result":"%s"}\n' "$(TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST')" "$(cat "$APPLIED_AT" 2>/dev/null)" "$1" "$2" > "$STATUS.tmp" && mv "$STATUS.tmp" "$STATUS"; }
HM="$(TZ=Asia/Kolkata date +%H%M)"; HM=$((10#$HM)); DOW="$(TZ=Asia/Kolkata date +%u)"
MARKET=0; [ "$DOW" -le 5 ] && [ "$HM" -ge 900 ] && [ "$HM" -lt 1545 ] && MARKET=1
SHA="$(curl -fsSL -m 20 --retry 3 -H 'Accept: application/vnd.github.sha' "https://api.github.com/repos/$REPO/commits/$BRANCH" 2>/dev/null | tr -d '[:space:]')"
echo "$SHA" | grep -Eq '^[0-9a-f]{40}$' || { status "-" "CHECK_FAILED_NO_SHA"; exit 0; }
[ "$SHA" = "$(cat "$STATE" 2>/dev/null)" ] && { status "$SHA" "UP_TO_DATE"; [ "$MARKET" = 0 ] && replay; exit 0; }
if [ "${1:-}" != "--force" ] && [ "$MARKET" = 1 ]; then status "$SHA" "NEW_CODE_WAITING_FOR_MARKET_CLOSE"; exit 0; fi
W="$(mktemp -d)"; trap 'rm -rf "$W"' EXIT
RAW="https://raw.githubusercontent.com/$REPO/$SHA"
curl -fsSL -m 40 --retry 3 "$RAW/ops/install_server_away_20261127.sh" -o "$W/i.sh" || { status "$SHA" "BLOCKED_NO_INSTALLER"; exit 0; }
curl -fsSL -m 40 --retry 3 "$RAW/backend/server_paper_positions.py" -o "$W/p.py" || { status "$SHA" "BLOCKED_DOWNLOAD"; exit 0; }
grep -q '^LIVE_ORDERS_ENABLED = False' "$W/p.py" || { status "$SHA" "BLOCKED_LIVE_ORDERS_GUARD"; exit 0; }
OUT="$(bash "$W/i.sh" "$SHA" 2>&1)"
if echo "$OUT" | grep -q SERVER_AWAY_INSTALL_OK; then echo "$SHA" > "$STATE"; TZ=Asia/Kolkata date '+%Y-%m-%d %H:%M IST' > "$APPLIED_AT"; status "$SHA" "UPDATED_OK"; replay now
else status "$SHA" "FAILED_ROLLED_BACK"; echo "$OUT" | tail -5; fi
