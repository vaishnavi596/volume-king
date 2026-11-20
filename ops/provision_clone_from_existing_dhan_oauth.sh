#!/usr/bin/env bash
# Clone-only handoff: reuse owner-approved existing V1 Dhan OAuth application.
# Does not rotate any token, stop any service, or change Dhan developer portal.
set -Eeuo pipefail
umask 077
[[ "$(id -u)" == 0 ]] || { echo "BLOCKED: run with sudo"; exit 1; }
target=/etc/bot-king/clone-dhan-oauth.env
[[ ! -e "$target" && ! -L "$target" ]] || { echo "BLOCKED: Clone OAuth env exists; do not overwrite"; exit 1; }
[[ "$(systemctl is-active bot-king.service)" == active ]] || { echo "BLOCKED: original OAuth runtime not active"; exit 1; }
pid="$(systemctl show bot-king.service -p MainPID --value)"
[[ "$pid" =~ ^[0-9]+$ && "$pid" != 0 ]] || { echo "BLOCKED: invalid runtime PID"; exit 1; }
# Only derive existing three credential fields from active V1 process, not shell.
# No values or hashes printed; token/session files are never read.
temp="$(mktemp /etc/bot-king/.clone-oauth-handoff.XXXXXX)"
trap 'rm -f "$temp"' EXIT
BKH_PID="$pid" BKH_TARGET="$temp" python3 - <<'PY'
import os,re
from pathlib import Path
rows=Path("/proc/"+os.environ["BKH_PID"]+"/environ").read_bytes().split(b"\0")
wanted={"DHAN_CLIENT_ID":"", "DHAN_API_KEY":"", "DHAN_API_SECRET":""}
for row in rows:
    if b"=" not in row: continue
    key,value=row.split(b"=",1)
    k=key.decode("ascii","ignore")
    if k in wanted:
        if wanted[k]: raise SystemExit("BLOCKED: duplicate Dhan auth environment")
        v=value.decode("ascii","strict")
        if not re.fullmatch(r"[A-Za-z0-9_.=-]{6,512}",v):
            raise SystemExit("BLOCKED: unsupported Dhan app credential format")
        wanted[k]=v
if not all(wanted.values()): raise SystemExit("BLOCKED: V1 OAuth env incomplete")
dest=Path(os.environ["BKH_TARGET"])
with dest.open("w") as stream:
    for name,key in (("BOTKING_CLONE_DHAN_APP_ID","DHAN_API_KEY"),
                     ("BOTKING_CLONE_DHAN_APP_SECRET","DHAN_API_SECRET")):
        stream.write(name+"="+wanted[key]+"\n")
    stream.write("BOTKING_CLONE_DHAN_CALLBACK_URL=https://botkingrajesh.duckdns.org/dhan/callback\n")
    stream.write("BOTKING_CLONE_DHAN_CALLBACK_APPROVED=1\n")
print("V1_EXISTING_DHAN_OAUTH_REUSED=YES")
print("NEW_DHAN_API_APP_REQUIRED=NO")
print("V1_SERVICE_UNCHANGED=YES")
PY
install -o root -g root -m 0600 "$temp" "$target"
echo "CLONE_OAUTH_CONFIG=READY"
echo "CLONE_CALLBACK_PUBLIC_ROUTE=NOT_YET_SWITCHED"
