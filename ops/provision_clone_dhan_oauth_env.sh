#!/usr/bin/env bash
# One-time owner-controlled provisioning of a DISTINCT Clone Dhan OAuth app.
# Must NOT repoint/reconfigure the production V1 developer-app callback.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 && -t 0 ]] || { echo "BLOCKED: root interactive Oracle SSH required"; exit 1; }
target=/etc/bot-king/clone-dhan-oauth.env
callback=https://botkingrajesh.duckdns.org/clone-v2/dhan/callback
[[ ! -e "$target" && ! -L "$target" ]] || { echo "BLOCKED: Clone OAuth configuration already exists; no overwrite"; exit 1; }
[[ "$(systemctl is-active bot-king.service)" == active ]] || { echo "BLOCKED: V1 not healthy"; exit 1; }
printf 'The independent Clone Dhan API app must be registered with EXACT callback:\n%s\n' "$callback"
printf 'Confirm the separate Clone callback is registered in Dhan developer portal (type APPROVED): '
IFS= read -r approved
[[ "$approved" == APPROVED ]] || { echo "BLOCKED: callback not registered/approved"; exit 1; }
printf 'Enter Clone-only Dhan API app ID (hidden): ' >&2
IFS= read -rs app_id
printf '\nEnter Clone-only Dhan API app secret (hidden): ' >&2
IFS= read -rs app_secret
printf '\n' >&2
# No shell eval/source, no untrusted newlines or environment injection.
if [[ ! "$app_id" =~ ^[A-Za-z0-9_.-]{6,256}$ ||
      ! "$app_secret" =~ ^[A-Za-z0-9_.=-]{10,512}$ ]]; then
  echo "BLOCKED: invalid app credentials format"; exit 1
fi
tmp="$(mktemp /etc/bot-king/.clone-dhan-oauth.XXXXXX)"
trap 'rm -f "$tmp"' EXIT
chmod 0600 "$tmp"
printf 'BOTKING_CLONE_DHAN_APP_ID=%s\nBOTKING_CLONE_DHAN_APP_SECRET=%s\nBOTKING_CLONE_DHAN_CALLBACK_URL=%s\nBOTKING_CLONE_DHAN_CALLBACK_APPROVED=1\n' \
  "$app_id" "$app_secret" "$callback" > "$tmp"
unset app_id app_secret
install -o root -g root -m 0600 "$tmp" "$target"
echo "CLONE_DHAN_OAUTH_PRIVATE_CONFIG=READY"
echo "V1_AUTH_CONFIG=UNTOUCHED"
