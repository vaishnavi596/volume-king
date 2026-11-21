#!/usr/bin/env bash
# B159/B160 SENSEX classification only: clone-owned two-file controlled rollout.
# Reviewed script. Needs operator action on Oracle; zero Dhan/API/order requests.
set -Eeuo pipefail
umask 077
ROOT=/home/opc/botking-clone-v2-runtime
PRIVATE=/home/opc/botking-clone-v2-private
SERVICE=botking-clone-v2.service
V1=bot-king.service
PYTHON=/usr/bin/python3.9
PIN=d2a8dfc30249bc2c298307703e76d9b2e7f98fbc
test "$(id -un)" = opc || { echo "BLOCKED: run as opc"; exit 1; }
test -d "$ROOT" && test -d "$PRIVATE" && test -x "$PYTHON" || { echo "BLOCKED: environment"; exit 1; }
test "$(systemctl is-active "$SERVICE")" = active || { echo "BLOCKED: clone service"; exit 1; }
test "$(systemctl is-active "$V1")" = active || { echo "BLOCKED: V1 service"; exit 1; }
test "$(systemctl show "$SERVICE" -p WorkingDirectory --value)" = "$ROOT" || { echo "BLOCKED: clone runtime path"; exit 1; }
for n in dhan_feed.py clone_v2_gateway.py; do
  test -f "$ROOT/$n" && test ! -L "$ROOT/$n" || { echo "BLOCKED: clone source absent/symlink"; exit 1; }
done
tmp="$(mktemp -d "$PRIVATE/sensex-b159.XXXXXXXX")"
chmod 700 "$tmp"
echo "ROLLBACK_DIRECTORY=$tmp"
# Never expose config, keys, token or broker response.
for name in dhan_feed.py clone_v2_gateway.py; do
  curl --fail --location --silent --show-error --retry 2 --max-time 40 \
    "https://raw.githubusercontent.com/vaishnavi596/volume-king/$PIN/backend/$name" \
    -o "$tmp/$name"
  chmod 600 "$tmp/$name"
  cp -p "$ROOT/$name" "$tmp/$name.rollback"
done
# Verify staged source identity AND exact previously reviewed runtime source.
"$PYTHON" - "$tmp" "$ROOT" <<'PY'
import hashlib,sys
from pathlib import Path
staged=Path(sys.argv[1]);live=Path(sys.argv[2])
targets={
 "dhan_feed.py":("dcaab25d5b55155868efcaae1f8e7c7d14b00217","63cf68124fc1449f6ce9fc1dc8359cadf038919d"),
 "clone_v2_gateway.py":("8c53eb8900564752e42b3d1d1368967ad7b1b809","0db7edfc06134781581bf31d05db092f05bcd3b3"),
}
def blob(p):
 d=p.read_bytes()
 return hashlib.sha1(b"blob "+str(len(d)).encode()+b"\x00"+d).hexdigest()
for name,(before,after) in targets.items():
 if blob(live/name)!=before: raise SystemExit("BLOCKED: runtime source diverged "+name)
 if blob(staged/name)!=after: raise SystemExit("BLOCKED: downloaded source diverged "+name)
print("TWO_FILE_SOURCE_AND_RUNTIME_BLOBS=VERIFIED")
PY
"$PYTHON" -m py_compile "$tmp/dhan_feed.py" "$tmp/clone_v2_gateway.py"
# Verify the clone Python 3.9 dependency context; never import old V1 backend.
SITE="$ROOT/.venv/lib64/python3.9/site-packages"
test -d "$SITE" || { echo "BLOCKED: clone dependencies"; exit 1; }
PYTHONPATH="$tmp:$SITE" "$PYTHON" - <<'PY'
import dhan_feed, clone_v2_gateway
assert hasattr(dhan_feed,"DhanUpstreamError")
assert callable(clone_v2_gateway.create_app)
print("CLONE_IMPORT_AND_ERROR_CATEGORY_GATE=PASS")
PY
# Stop on first failure; rollback BOTH files if anything goes wrong after this point.
changed=0
rollback(){
  if test "$changed" -eq 1; then
    for name in dhan_feed.py clone_v2_gateway.py; do
      install -m 600 "$tmp/$name.rollback" "$ROOT/.$name.rollback-new"
      mv -f "$ROOT/.$name.rollback-new" "$ROOT/$name"
    done
    sudo systemctl restart "$SERVICE" || true
    echo "B159_ROLLBACK=ATTEMPTED"
  fi
}
trap rollback ERR
changed=1
for name in dhan_feed.py clone_v2_gateway.py; do
  install -m 600 "$tmp/$name" "$ROOT/.$name.new"
  mv -f "$ROOT/.$name.new" "$ROOT/$name"
done
sudo systemctl restart "$SERVICE"
ok=0
for try in $(seq 1 20); do
  if test "$(systemctl is-active "$SERVICE")" = active &&
      curl -fsS --noproxy '*' --max-time 4 -o /dev/null http://127.0.0.1:8002/clone-v2/health; then
    ok=1;break
  fi
  sleep 1
done
test "$ok" -eq 1
test "$(systemctl is-active "$V1")" = active
curl -fsS --noproxy '*' --max-time 4 -o /dev/null http://127.0.0.1:8000/health
changed=0
trap - ERR
echo "B159_CLONE_ONLY_DEPLOY=PASS"
echo "V1_UNCHANGED_AND_HEALTHY=YES"
echo "SENSEX_NEW_CATEGORIES=READY_FOR_NEXT_OPT_IN_PROBE"
echo "NO_DHAN_PROVIDER_REQUEST_SENT=YES"
