# BOT KING — Evidence ledger and minimal-command handoff runbook
Updated: 2026-11-16 IST. Canonical immutable history: [BOT_KING_WORK_LOG.md](BOT_KING_WORK_LOG.md). Current source-of-truth for requested work: [BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md](BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md) and [BOT_KING_REFRESH_DEMAND_INVENTORY_20261116.md](BOT_KING_REFRESH_DEMAND_INVENTORY_20261116.md).

## Purpose
Carry discussion, decisions, edits, GitHub commits, CI run outcomes, Oracle commands + exact summarized output, deployment gates, and phone evidence between conversations **without repeating already-proven read-only commands**. Each observation is an **as-of timestamped snapshot**, NOT perpetual live service health. Append, do not silently rewrite past results.

## Evidence grades (mandatory)
- **USER / MOBILE:** reported installed-version and screenshots; authoritative for the device symptom, not its remote HTTP root cause.
- **GITHUB SOURCE / COMMIT:** code landed on named branch; not proof of CI/Oracle deploy.
- **OFFLINE TEST / CI:** exact commit, run ID, attempt, job, pass/fail and failing assertion; not proof of on-phone behavior.
- **ORACLE OPERATOR OUTPUT:** command actually executed by owner, redacted output and timestamp; not necessarily data-feed freshness.
- **STAGED / DRY-RUN:** backup, hash, syntax, offline behavioral proof, with **production unchanged**.
- **ORACLE DEPLOYED:** guarded apply, backup and rollback location, service restart, authenticated protected route smoke; never infer from dry-run.
- **SIGNED APK:** exact build run, versionName, versionCode, package, signer SHA256 and artifact.
- **DEVICE PASS:** explicit on-phone functional check for installed exact version.

## Already-proven Oracle checks — do not reissue unless config changed, a symptom contradicts the snapshot, or a fresh before/after deployment baseline is needed
1. **Nginx syntax and listeners (owner result, Nov 16):** `sudo nginx -t; sudo ss -lntp | grep -E ':(443|8000)([[:space:]]|$)'` → nginx syntax PASS; Uvicorn `127.0.0.1:8000` LISTEN; Nginx `0.0.0.0:443` LISTEN. This proves listen configuration at observation time, not broker entitlement.
2. **Public TLS health from Oracle host (owner result, Nov 16):** `curl --noproxy '*' -sS --connect-timeout 3 --max-time 10 -o /dev/null -w 'PUBLIC_HTTPS=%{http_code} TLS_VERIFY=%{ssl_verify_result}\\n' https://botkingrajesh.duckdns.org/health` → `PUBLIC_HTTPS=200 TLS_VERIFY=0`. Do not repetitively check this merely to diagnose Candle starvation.
3. **Original deployed adapter SHA256 (owner):** `/opt/bot-king-server/dhan_feed.py` → `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`.
4. **Staged candidate exact SHA256 and syntax (owner):** `beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c`; exact one-file diff reviewed: contextlib import + class-shared quote lock/1.05s spacing, preserving preexisting historical/option guards.
5. **Staged module behavior (owner isolated local fake-input probe):** `scripts/audit_oracle_s2d_staged_offline.py` → `S2D_OFFLINE_BEHAVIOR_PASS: YES`, `QUOTES_TESTED: 2`, `QUOTE_START_GAP_SECONDS: 1.051`, `429_SHARED_COOLDOWN: PASS`, `ORACLE_HISTORICAL_OPTION_FIELDS: PRESENT`, `NETWORK_REQUESTS: 0`, `PRODUCTION_CHANGED: NO`.
6. **Guarded deploy dry-run (owner):** `sudo python3 /tmp/deploy_oracle_s2d_quote_gate.py` **without** `--apply` → `SOURCE_HASH: PASS`, `STAGED_HASH: PASS`, `PYTHON_SYNTAX: PASS`, `PREDEPLOY_HEALTH: PASS`, `DRY_RUN_PASS: YES`, `PRODUCTION_CHANGED: NO`. **Production 1.05s gate deployment not proven.** NEVER casually repeat/apply without fresh authorized preflight and verified branch/test.
7. **Offline CI as-of commits:** [run 43796217369 attempt 2](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) at `fc442e94`: **850 tests PASS**. [run 43802182219](https://github.com/vaishnavi596/volume-king/actions/runs/43802182219) at `a1efbb3f`: **855 tests PASS**, 09:10–15:45/manual/closed-market guards. These runs do NOT certify later commits.
8. **Signed v2.3.127:** [run 43805532600](https://github.com/vaishnavi596/volume-king/actions/runs/43805532600) #642, **862/862 PASS**, package `com.botking.bot_king`, versionName `2.3.127`, versionCode `74201`, pinned signer SHA256 `5b529741cc4bf98c29de81d292f54cbeb71ca559974cc0e9968cd3d19eabde91`, artifact `volume-king-apk` ID `14198317482`. **Mobile v2.3.127 subsequently FAIL, so CI cannot close runtime issue.**
9. **Phone 16 Nov 10:38–10:41 IST:** 7 health issues, 54-symbol filters 0 analyzed / 3 errors / 51 insufficient, index 3 candle failures, stale/invalid Oracle snapshot, multiple `FeedError` classes including index, Watchlist, Options and Scanner; no sanitized underlying HTTP status in screenshot.
10. **v2.3.128:** source Candle/Super Five continuity [70defe99](https://github.com/vaishnavi596/volume-king/commit/70defe9947c06d84d0d28bc7b1b930b39eda0ec8), structural regression [2bb5fb2c](https://github.com/vaishnavi596/volume-king/commit/2bb5fb2c751f70a7f0a4b405b296b9d4d54fcb9b), version trigger [48182f1b](https://github.com/vaishnavi596/volume-king/commit/48182f1b0b97705523d93287fdc1b4fd37f36259). **Owner reports Build FAILED.** Exact failing run/job/step not yet available in source audit; do not claim corrected/installed.
11. **WatchlistStore global 70 cross-list uniqueness:** S18 source staging versus actual Oracle deployment **PENDING**. Do not replace Oracle-custom production server.py from repository wholesale.

## User-approved conversation decisions not yet implemented
- Data-only refresh, not page redraw; static symbol/header/nav stays mounted. Watchlist local mounted cells are observed every 2s in code, whereas some other pages still render whole page.
- Market auto window **09:10 inclusive–15:45 exclusive IST, weekdays**; exchange-live signal eligibility separate **09:15–15:30**. Outside window use last-valid cache; user wants **one global BOT KING Manual Data Refresh** rather than many per-screen buttons. Existing manual function covers equity+indices, not all domains.
- **Four LOGICAL channels** mobile ↔ Oracle (proposed and accepted direction, **NOT FOUR simultaneous requests every 2s**): (1) equity+index quotes; (2) completed candles / Scanner / Super Five; (3) selected Options / OI / assessed futures when verified; (4) News, Assessment and health. Oracle owns central rate limiter, shared cache and one request per new revision, components reuse instead of fanout. No v2.3.128 deployment of this design.
- Conditional faster targets after measuring actual healthy collector: local Scanner/Super Five update **2–5s**, index quote **10–15s**, Watchlist aggregated quote **15–30s**, selected Options chain **30s** (trial 15s only after 429-free proof), News RSS **300–600s**. Completed **5m candles** update only after genuinely closed bars; Oracle Assessment target **30–60s**. Targets are NOT current applied timers; quote API published maximum is not an Oracle production guarantee.
- Current observed source timings (as-of v2.3.128 branch): Watchlist & Index LTP auto **60s**, selected Options **60s** + 3.25s expiry→chain pacing, Oracle Assessment **180s**, index candle **180s**, full historical 54-symbol scan plus **180s REST** with ~1.5s network pacing, visible chart **60s**, local Scanner **2s**, local Super Five **10s**, local Watchlist **2s**, News cache **600s**.
- Dhan-only market data; no silent Yahoo/Angel fallback, no token changes without proof, preserve HIST/unverified and last valid quotes/votes, 429 global cooldown, paper mode only, live orders OFF. Five saved Watchlists have at most 70 **unique equities total**, one symbol belongs to one list.

## Minimal NEXT checks (do not run a full generic audit again)
**Before any command** read the last 2–3 Work Log sections, this runbook, latest GitHub branch head, and exact changed file diff. Issue only the next missing-evidence probe and append exact result.

### GitHub FIRST: no Oracle command needed
- Open [Build APK workflow](https://github.com/vaishnavi596/volume-king/actions/workflows/build.yml) and find failed run for commit `48182f1b` / v2.3.128. Read **failed job step/log**; do not guess dependency/test/signing failure. Fix source+tests, run regression, only then new version bump (higher versionCode) and signer/artifact validation.
- Read [joint work log](BOT_KING_WORK_LOG.md) for exact completed tests rather than rerunning all old commands; run the narrow failing regression and full release suite once.
- Inspect `scripts/deploy_oracle_s2d_quote_gate.py` and its **current SHA guards** before considering any deployment. No unattended production apply in this document.

### Oracle ONLY IF new backend evidence required
Read-only, bounded, no secret output; commands intentionally **do not print pairing keys or OAuth tokens**. Group 2–4 checks per session, only if previous snapshots are too old/contradict current app symptoms:
```bash
# A. Local public/unprotected health plus deployed adapter hash (post-change or newly failed service only)
curl --noproxy '*' -fsS --max-time 8 http://127.0.0.1:8000/health
sudo sha256sum /opt/bot-king-server/dhan_feed.py
# B. Service freshness and logs: redact keys/tokens before sharing, inspect only recent errors
sudo systemctl is-active bot-king.service
sudo journalctl -u bot-king.service --since '-15 min' --no-pager -n 80 | sed -E 's/(access[_-]?token|client[_-]?id|X-BotKing-Key|Authorization)([=: ]+)[^ ,;]+/\1\2[REDACTED]/Ig'
```
Do not paste `server.env`, `dhan-token`, auth headers or full secure responses. A sanitized **authenticated**, intentionally bounded market-data probe must use the known existing Oracle protected-access procedure from the work log (not a guessed key). Check only the changed/failed route first: `/v2/snapshot` collection_status/age/quote count, `/dhan/index-ltp-batch` 3 availability, one `/dhan/intraday` sample only if cooldown 0, selected chain expiry+metric only when verifying options. Avoid periodic 51-history retests merely to prove HTTP server health.

## Repeat-avoidance decision
- If same source SHA, same running service, and latest journal already proves listening/TLS → **SKIP** nginx, ss, curl TLS and syntax checks.
- If proposed SHA matches but production SHA is old → **DO NOT** claim deployed; only guarded deployment after CI and operator approval policy.
- If Oracle snapshot stale but index batch succeeds → investigate collector/snapshot storage independently; do NOT blame overall connection.
- If an authenticated endpoint returns HTTP429 → global cooldown, no immediate retry or extra fanout. HTTP 403 → check pairing-key/session without rotating Dhan OAuth; HTTP 422 → check instrument/expiry. 5xx → check server-side redacted stage and entitlement.
- If all upstream prices succeed but Candle filters disappear → investigate same-source completed-history cache, partial replacement and local filter vote fallback independently.
- If source code merged but signed build failed → no new installation claim and no production-change claim.

## Batch journal template — append exact facts
```text
## YYYY-MM-DD HH:MM IST — <batch title>
Goal / user decision:
GitHub branch HEAD before edits:
Files changed (+/-), commits and intended effects:
CI workflow run ID / job / attempt / concluded status and key assertion:
Oracle command executed? (exact sanitized command, timestamp, summary output):
Backup/staged/prod SHA and production changed?:
Broker probe (route, status, count, age, freshness; no secret):
APK (run/versionName/versionCode/package/signer/artifact):
Device (installed exact version, PASS/FAIL and photo symptom):
Open blockers, next minimum commands, rollback / safety:
Evidence level: SOURCE / CI / STAGED / ORACLE DEPLOYED / BROKER PROBED / APK / DEVICE
```

## Documentation consistency rule
Historical journal entries are snapshots. Old references to v2.3.125/126/127 in the checklist, handoff or prior-chats audit are **historically true as-of their dated point**, not latest-state declarations. This runbook and current Work Log continuation supersede the STATUS, never erase history. Where a prior assistant asserted a PASS without exact log, label it prior-reported/unverified.


## 2026-11-16 — One grouped Oracle collector audit, no fresh Dhan requests
New source `scripts/audit_oracle_collector_runtime_readonly.py` provides three bounded GET-only localhost checks (`/health`, `/v2/server-readiness`, `/v2/snapshot`) from **one operator command**. The protected two endpoints require `BOTKING_AUDIT_PAIRING_KEY` **already supplied by the authorized Oracle operator through their secure local environment**; this script never discovers/opens token files, never logs a secret, does not call Dhan and does not submit orders. Without the variable, it reports HTTP code zero for protected paths, which is **not proof Oracle rejected the key**.

**Operator usage after script is present on the host:** `python3 scripts/audit_oracle_app_routes_readonly.py --server /opt/bot-king-server/server.py` (static deployed file route count and hash) and `python3 scripts/audit_oracle_collector_runtime_readonly.py` (three GETs; use the authorized key in secure local process environment before invoking). Run these as one grouped, read-only batch; redact any shell history/terminal traces and do not paste/export the value of the pairing key into GitHub or chat. If no safe key injection is available, run only the source audit and record the protected part as **NOT RUN** rather than guessing. Do not copy any credential into the script, shell command literal, output log, or journal.

The runtime script returns **no prices or symbol names**: `collector_enabled`, `collector_status`, `collector_interval_seconds`, `collector_last_success_age_seconds`, `snapshot_status`, `snapshot_age_seconds`, equity quote count, unavailable count, route HTTP statuses. It explicitly reports `quote_freshness_exchange_verified=false` because successful Oracle cache collection alone is not exchange-timestamp verification. Source audit and GET-only audit are **read-only** but do not establish index/option/intraday Dhan entitlement. No additional index/chain requests should be sent until collector/429 findings justify them.

**Next decision:** If collector disabled or missing, investigate its deployed process flag and expected service user before any change; if enabled but `collection_overdue` inspect only ingestion stage/cooldown with sanitized recent logs; if 200/recently_collected, compare against App Snapshot constraints and watchlist ages. Do not change `BOTKING_226_INGEST_SECONDS` below source's min60 or increase client polling before rate-limit verification. Existing 1.05s Oracle quote gate remains *staged/not proven deployed*.
