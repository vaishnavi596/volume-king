#!/usr/bin/env bash
# BOT KING V3 / V1 read-only SENSEX path audit. No Dhan/provider calls, no secrets.
set -u
export LC_ALL=C
echo "=== V3_SENSEX_V1_ROUTE_ISOLATION_READ_ONLY ==="
for unit in bot-king.service botking-clone-v2.service nginx.service; do
  state="$(systemctl is-active "$unit" 2>/dev/null || true)"
  case "$state" in active|inactive|failed|activating|deactivating) :;; *) state=unknown;; esac
  printf '%s=%s\n' "$unit" "$state"
done
for spec in 'V1|http://127.0.0.1:8000/health' 'CLONE|http://127.0.0.1:8002/clone-v2/health'; do
  label="${spec%%|*}"; url="${spec#*|}"
  code="$(curl --noproxy '*' --silent --output /dev/null --max-time 4 --write-out '%{http_code}' "$url" 2>/dev/null)" || code=000
  printf '%s_HEALTH_HTTP=%s\n' "$label" "$code"
done
# Read effective Nginx configuration IN MEMORY, but print only classified fixed path/port.
if command -v nginx >/dev/null 2>&1; then
  if command -v sudo >/dev/null 2>&1; then
    config="$(sudo -n nginx -T 2>/dev/null)" || config=""
  else
    config="$(nginx -T 2>/dev/null)" || config=""
  fi
else
  config=""
fi
if [[ -z "$config" ]]; then
  echo "NGINX_EFFECTIVE_CONFIG=NOT_READABLE"
else
  printf '%s' "$config" | python3 -c '
import re,sys
s=sys.stdin.read()
for label,kind,path in (("CLONE_QUOTES","prefix","/clone-v2/"),("LEGACY_DHAN","prefix","/dhan/"),("OAUTH_CALLBACK","exact","/dhan/callback")):
    kind_re=r"\^~\s*" if kind=="prefix" else r"=\s*"
    pattern=r"location\s+"+kind_re+re.escape(path)+r"\s*\{"
    hits=list(re.finditer(pattern,s))
    if not hits:
        print(label+"_CONFIG=NOT_EXPLICITLY_FOUND")
        continue
    destinations=[]
    for hit in hits:
        # Local inspection only, not a comprehensive parser of nested includes.
        part=s[hit.end():s.find("}",hit.end()) if "}" in s[hit.end():] else len(s)]
        match=re.search(r"proxy_pass\s+http://127\.0\.0\.1:(8000|8002)\s*;",part)
        destinations.append("PORT_"+match.group(1) if match else "OTHER_OR_UNRESOLVED")
    print(label+"_LOCATION_COUNT="+str(len(hits)))
    print(label+"_PROXY_DESTINATIONS="+",".join(destinations))
print("NGINX_SOURCE_ROUTE_CHECK=NOT_LIVE_HTTP_PROOF")
'
fi
# Validate deployed Clone gateway code identity without reading token or configuration.
# A different blob only proves runtime/source drift, not malicious routing.
if [[ -f /home/opc/botking-clone-v2-runtime/clone_v2_gateway.py &&
      ! -L /home/opc/botking-clone-v2-runtime/clone_v2_gateway.py ]]; then
  python3 - <<'PY'
import hashlib
from pathlib import Path
p=Path("/home/opc/botking-clone-v2-runtime/clone_v2_gateway.py")
expected="8c53eb8900564752e42b3d1d1368967ad7b1b809"
try:
    data=p.read_bytes()
    got=hashlib.sha1(b"blob "+str(len(data)).encode()+b"\x00"+data).hexdigest()
    print("DEPLOYED_CLONE_GATEWAY_BLOB="+("MATCH_REVIEWED_SOURCE" if got==expected else "DIFFERS_FROM_REVIEWED_SOURCE"))
    source=data.decode("utf-8")
    print("DEPLOYED_SENSEX_STAGE_LOGGER="+("PRESENT" if "clone_market_diagnostic" in source else "ABSENT"))
    print("DEPLOYED_SENSEX_REGISTRY="+("BSE_I_51_PRESENT" if '"SENSEX": ("BSE_I", 51)' in source else "REVIEW_REQUIRED"))
except (OSError,UnicodeError,ValueError):
    print("DEPLOYED_CLONE_GATEWAY_BLOB=NOT_READABLE")
PY
else
  echo "DEPLOYED_CLONE_GATEWAY_BLOB=MISSING_OR_SYMLINK"
fi
# Existing server diagnostic metadata only: filter BEFORE output, no raw provider body.
if command -v journalctl >/dev/null 2>&1; then
  journalctl -u botking-clone-v2.service --since '2026-11-20 00:00:00' --no-pager -o cat 2>/dev/null |
    python3 -c '
import re,sys
allowed={"quotes","candles"}
stages={"provider","shape","mapping","validation","cooldown"}
categories={"missing_segment","missing_security_id","invalid_price","invalid_shape","invalid_bars","rate_limited","auth_unavailable","upstream_error"}
items=[]
regex=re.compile(r"clone_market_diagnostic route=(\w+) symbol=SENSEX stage=(\w+) category=(\w+)")
for line in sys.stdin:
    m=regex.search(line)
    if m and m[1] in allowed and m[2] in stages and m[3] in categories:
        items.append("SENSEX_DIAG route="+m[1]+" stage="+m[2]+" category="+m[3])
for row in items[-25:]: print(row)
print("SENSEX_DIAGNOSTIC_ENTRIES="+str(len(items)))
print("SENSEX_PROVIDER_LIVE_PROVEN=NO")
'
else
  echo "SENSEX_DIAGNOSTIC_ENTRIES=UNAVAILABLE"
fi
echo "NO_PROVIDER_REQUESTS_SENT=YES"
echo "NO_V1_OR_CLONE_CONFIGURATION_CHANGED=YES"
