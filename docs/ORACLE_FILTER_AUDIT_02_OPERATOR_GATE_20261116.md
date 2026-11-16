# ORACLE-FILTER-AUDIT-02 — production verification gate

Date: 2026-11-16. Status: **NOT EXECUTED ON ORACLE**. Working branch: `fix/botking-joint-audit-70-15-20261115`.

## Purpose and evidence boundaries

PCR-02's mapping-only GET route and the GitHub backend's five-filter placeholder have source/CI evidence only. Source files in this repository may not match the customized live Oracle `/opt/bot-king-server/server.py`. A source-declared route does not prove a live HTTP route. Never assert working PCR or five assessment signals based only on mapping, historical directional votes, or CI.

**No APK, no deployment, no restart, no Dhan mutation, no orders.** Never print or include pairing/API tokens or `/etc/bot-king/server.env` in reports.

## Operator read-only commands (run on Oracle only)

Prerequisite: trusted checkout of *this working branch* accessible on Oracle, and Python 3 available. Paths below refer to scripts in that checkout; do **not** copy/replace production server.py for the audit.

1. Confirm current source file is the intended regular file. Run `python3 scripts/audit_oracle_app_routes_readonly.py --server /opt/bot-king-server/server.py` from the checkout. Report: SHA256, 9 source routes, missing list. Missing source routes require investigation; a listed source route is not runtime proof.
2. Run `python3 scripts/audit_oracle_five_filters_readonly.py --server /opt/bot-king-server/server.py`. Record `assessment_route_source_count`, five IDs, four factors, `known_placeholder_detected`. An unknown/non-placeholder implementation is **UNKNOWN**, not PASS.
3. For protected collector GET checks, have the operator securely make `BOTKING_AUDIT_PAIRING_KEY` available as an environment variable **without echoing it or committing it**. Run `python3 scripts/audit_oracle_collector_runtime_readonly.py`. This script accesses *only* loopback GET `/health`, `/v2/server-readiness`, `/v2/snapshot`. Record HTTP codes, collector enabled/status/age, snapshot status/age and counts. `401/403` is a protected-route/auth mismatch, `404` a live route gap, `429` a rate/cooldown condition, and `0` a transport or missing-key diagnostic; do not treat these as equivalent.
4. If authentication cannot be supplied safely, omit step 3 and mark protected probes **NOT VERIFIED**. Do not test live Dhan options or all 51 equity chains in this batch.

## Decision matrix

| Evidence | Classification | Next action |
|---|---|---|
| Missing assessment route in Oracle source | SOURCE MISSING | Compare deployment sources; backup before targeted patch |
| Known `not_configured` route | PLACEHOLDER | Design a timestamped/fail-closed assessment producer using verified data, **not** invented scores |
| Route source differs | UNKNOWN IMPLEMENTATION | Inspect sanitized relevant function locally; validate response schema and freshness before claiming producer |
| Collector disabled / overdue / missing GET | COLLECTOR GAP | Inspect service configuration and recent non-secret health diagnostics; backup-first corrective change if proven |
| Options expiry not listed or unentitled | NOT ELIGIBLE / UNVERIFIED | Keep equity PCR unavailable; never infer F&O from `NSE_EQ` LTP mapping |
| 429 or Dhan provider limit | RATE LIMITED | Respect 30s cooldown; do not fan out 51 option-chain calls |
| All tests green but no Oracle results | SOURCE-ONLY PASS | Keep production and mobile status UNVERIFIED; block APK |

## Subsequent gate

Only after operator's sanitized output: compare source SHA to intended deployment, isolate actual cause, back up production source/config, apply minimum necessary Dhan-only read-only data patch, run regression CI, recheck server, and separately retest phone. Preserve `live_orders_enabled=false`. Append each observed result to `docs/BOT_KING_WORK_LOG.md` and `docs/BOT_KING_WORK_RESULT_TRACKER.md` with commit/run ID and source-vs-CI-vs-Oracle-vs-device distinction.

## ORACLE-FILTER-AUDIT-03 — deterministic joined classifier (staged on GitHub)

After collecting *sanitized* outputs from the three operator scripts into local JSON files, run:
```bash
python3 scripts/classify_oracle_audit_results.py \
  --routes routes-report.json --filters filters-report.json --collector collector-report.json
```
No broker/network calls are made by the classifier; it reads only the three local sanitized JSON files. These files must not contain secrets or raw Dhan responses. The classifier separates source route declarations, missing/duplicate assessments, known WAIT placeholder, authentication failures, missing runtime routes, rate limits, and collector freshness. It **always refuses to certify live five-filter function, equity PCR eligibility, or APK release**. This is a sorting aid for operator evidence, not a replacement for server investigation. Original production status is still UNVERIFIED until the operator runs the three audits.
