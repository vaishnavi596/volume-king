# BOT KING B3 — Oracle read-only production parity handoff

**Status:** GitHub offline source CI #1668 PASS (1042/1042). Actual Oracle
production parity **NOT VERIFIED**. No production deploy is authorized by this
document. Keep live orders OFF.

## Scope and safety

The production server `/opt/bot-king-server/server.py` is customized and is
**not interchangeable** with GitHub `backend/server.py`. Never overwrite it
with the GitHub file. The B3 history single-flight is a worker-local 32-stripe
lock around `POST /dhan/intraday`, with an existing validated 180-second
history cache. It does not share locks between processes, hosts, or restarts.
A green source audit does not prove a running server has that code.

Run the following commands **on Oracle itself** from an authorized operator
shell. Do not paste secrets, environment values, tokens, or source excerpts
into tickets, chat or CI. The audit scripts must be copied from the reviewed
GitHub commit, not downloaded from an unverified URL.

## Read-only checks — no Dhan requests or restart

```bash
cd /opt/bot-king-server
python3 /path/to/reviewed/scripts/audit_oracle_b3_history_readonly.py --server /opt/bot-king-server/server.py
python3 /path/to/reviewed/scripts/audit_oracle_app_routes_readonly.py --server /opt/bot-king-server/server.py
systemctl is-active bot-king.service
systemctl show bot-king.service -p ExecStart -p MainPID -p NRestarts
sha256sum /opt/bot-king-server/server.py
```

The first two scripts parse source only. The service metadata and SHA command
do not modify the process or read credential files. Inspect the output for
source indicators, service activity and the exact production hash; record
the hash and non-secret audit JSON in the journal. Avoid copying `ExecStart`
to public logs if locally customized command-line arguments contain secrets.

Optional collector status is a **separate** audit using
`scripts/audit_oracle_collector_runtime_readonly.py`. It performs bounded
loopback GET requests only, but requires the operator to provide a pairing key
securely without printing it; do not run it if secure key injection is not
available. Never test B3 by generating a burst of real Dhan history calls.

## Decision matrix

| Actual Oracle finding | Next action |
|---|---|
| Source lacks B3 single-flight guard | Compare exact deployed handler to GitHub; prepare a **minimal** patch only after backup, review and hash pin |
| Source has guard but worker/cache behavior unknown | Inspect worker topology and cache lifecycle; do not claim multi-phone deduplication |
| Source audit passes, runtime not checked | Mark **SOURCE CHECK ONLY**, not production PASS |
| Service unhealthy, hash differs, or custom code conflicts | **STOP**; preserve production and investigate, do not restart blindly |
| Validated staged patch + rollback + health tests | Separately approve controlled deployment; capture postdeploy hash and read-only health |
| Real two-phone measurements absent | Keep Dhan request savings and mobile parity **PENDING** |

## Production apply gate (not performed)

Before any deployment: confirm exact current hash; preserve an on-host
permission-restricted, hash-verified backup; review a narrow diff against the
actual Oracle handler; check syntax and service worker count; ensure a
rollback procedure and healthy baseline. After authorized apply, verify service,
read-only local health, history cache/freshness and app behavior without order
traffic. Record outcome and evidence in `docs/BOT_KING_WORK_LOG.md`.

**No APK release** until the separate BOT KING release gate policy is met.
