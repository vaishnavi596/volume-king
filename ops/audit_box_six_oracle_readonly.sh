#!/usr/bin/env bash
# V3 Box Six: strictly read-only Oracle-host preflight.
# Run on host, NOT in GitHub runner; no service start, restart, reload, or writes.
# Prints only coarse safe status; never print secrets, environment, source, or tokens.
set -Eeuo pipefail
export LC_ALL=C
fail=0
echo "=== BOX_SIX_ORACLE_READONLY_PREFLIGHT_V1 ==="
for service in bot-king.service botking-clone-v2.service nginx.service; do
  state="$(systemctl is-active "$service" 2>/dev/null || true)"
  if [[ "$state" == "active" ]]; then
    echo "SERVICE ${service}=ACTIVE"
  else
    echo "SERVICE ${service}=NOT_ACTIVE"
    fail=1
  fi
done
if command -v nginx >/dev/null 2>&1; then
  if nginx -t >/dev/null 2>&1; then
    echo "NGINX_SYNTAX=PASS"
  else
    echo "NGINX_SYNTAX=UNVERIFIED_OR_INVALID"
    fail=1
  fi
else
  echo "NGINX_SYNTAX=UNVERIFIED"
  fail=1
fi
if command -v ss >/dev/null 2>&1; then
  for port in 8000 8002 8766; do
    # Do not disclose PIDs, remote IP addresses or process arguments.
    sockets="$(ss -H -ltn "( sport = :$port )" 2>/dev/null || true)"
    if [[ -z "$sockets" ]]; then
      if [[ "$port" == 8766 ]]; then
        echo "PORT_8766=FREE_FOR_SEPARATE_STAGING"
      else
        echo "PORT_${port}=NOT_LISTENING"
        fail=1
      fi
      continue
    fi
    if printf '%s\n' "$sockets" | awk -v p="$port" '
      NF {seen=1; if($4 != "127.0.0.1:" p) bad=1}
      END {exit(!seen || bad)}'; then
      if [[ "$port" == 8766 ]]; then
        echo "PORT_8766=LOOPBACK_ONLY_ALREADY_IN_USE_REVIEW"
        fail=1
      else
        echo "PORT_${port}=LOOPBACK_ONLY"
      fi
    else
      echo "PORT_${port}=UNSAFE_OR_UNEXPECTED"
      fail=1
    fi
  done
else
  echo "LISTENER_CHECK=UNAVAILABLE"
  fail=1
fi
for dir in /opt/bot-king-server /home/opc/botking-clone-v2-runtime; do
  if [[ -d "$dir" && ! -L "$dir" ]]; then
    case "$dir" in
      /opt/bot-king-server) echo "V1_RUNTIME_DIRECTORY=PRESENT" ;;
      *) echo "CLONE_RUNTIME_DIRECTORY=PRESENT" ;;
    esac
  else
    case "$dir" in
      /opt/bot-king-server) echo "V1_RUNTIME_DIRECTORY=NOT_CONFIRMED" ;;
      *) echo "CLONE_RUNTIME_DIRECTORY=NOT_CONFIRMED" ;;
    esac
    fail=1
  fi
done
# Avoid leaking available disk byte counts or mount paths; only an availability gate.
if df -P /home/opc >/dev/null 2>&1; then
  free_kb="$(df -Pk /home/opc | awk 'NR==2 {print $4}')"
  if [[ "$free_kb" =~ ^[0-9]+$ ]] && (( free_kb >= 1048576 )); then
    echo "STAGING_DISK_FREE_GE_1G=YES"
  else
    echo "STAGING_DISK_FREE_GE_1G=NO_OR_UNVERIFIED"
    fail=1
  fi
else
  echo "STAGING_DISK_FREE_GE_1G=UNVERIFIED"
  fail=1
fi
# No outbound Dhan requests, environment dump, credential inspection, or file mutation.
echo "PROVIDER_REQUESTS_SENT=0"
echo "ORDERS_SENT=0"
echo "FILES_WRITTEN=0"
echo "SERVICES_CHANGED=0"
if ((fail)); then
  echo "BOX_SIX_STAGING_HOST_GATE=HOLD"
  exit 2
fi
echo "BOX_SIX_STAGING_HOST_GATE=STATIC_PREFLIGHT_PASS_NOT_DEPLOYED"
