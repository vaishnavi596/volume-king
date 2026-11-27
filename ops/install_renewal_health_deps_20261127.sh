#!/usr/bin/env bash
# Installs the two modules /clone-v2/renewal-health imports (fixes HTTP 500 ModuleNotFoundError dhan_expiry_store).
# No restart needed (lazy import). Read-only; no Dhan calls, no secrets.
set -Eeuo pipefail
umask 077
SRC="${1:?commit sha}"
BASE="https://raw.githubusercontent.com/vaishnavi596/volume-king"
ROOT="/home/opc/botking-clone-v2-runtime"
test "$(id -un)" = "opc" || { echo "BLOCKED: run as opc"; exit 1; }
WORK="$(mktemp -d "$ROOT/.upd.XXXXXXXX")"; trap 'rm -rf "$WORK"' EXIT
for f in dhan_expiry_store.py dhan_renewal_policy.py dhan_renewal_health.py; do
  curl -fsSL -m 40 --retry 3 "$BASE/$SRC/backend/$f" -o "$WORK/$f"
  python3 -m py_compile "$WORK/$f"
done
for f in dhan_expiry_store.py dhan_renewal_policy.py dhan_renewal_health.py; do
  [ -f "$ROOT/$f" ] && cp -p "$ROOT/$f" "$ROOT/$f.rollback-$(date +%s)"
  install -m 640 "$WORK/$f" "$ROOT/$f"
done
cd "$ROOT" && python3 -c "import dhan_renewal_health; print('IMPORT_OK')"
