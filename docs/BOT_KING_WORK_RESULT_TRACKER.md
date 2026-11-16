# BOT KING — Work, Result, Errors & Repair Tracker

**Owner decision: 2026-11-16.** This is the compact front page for the append-only `docs/BOT_KING_WORK_LOG.md`. The release gates are in `docs/BOT_KING_RELEASE_GATE_POLICY.md`. Update this table **together with each batch** so a new chat can distinguish planned work, source commits, CI proof, running Oracle proof, APK build result, phone result and follow-up fixes. The dates and statuses below are **as-of their exact check**, not forecasts.

## 1–6 joint work stages — current result

| Stage | Work / owner | Work performed (exact evidence) | Source / CI result | Oracle / actual result | APK / phone result | Remaining error, repair and next action |
|---|---|---|---|---|---|---|
| **1 — Audit** | App + GitHub + Oracle | Last eight runs checked before changes; read-only 9-route AST audit `scripts/audit_oracle_app_routes_readonly.py`, runtime GET-only collector probe `scripts/audit_oracle_collector_runtime_readonly.py`; release policy `d0bc841a` | Source AST audit 898/898 PASS #1552; runtime audit mocks 902/902 PASS #1553; **not an Oracle host test** | **NOT RUN** on customized live Oracle server; route hash, collector state, quote age unknown | #645 is a diagnostic build, phone result **NOT TESTED** | Run grouped Oracle deployed source+GET-only collector audit safely; record source hash, protected HTTP statuses, age/count and enabled flag |
| **2 — Server fixes** | GitHub backend + Oracle | Source-only authenticated `/v2/server-readiness` `f3163d4c`; fail-closed `/v2/assessment/{symbol}` `701ec398`; Dhan only / live orders OFF | Route/readiness parity 893/893 PASS #1549; assessment 894/894 PASS #1551 | **NOT DEPLOYED / NOT VERIFIED** on Oracle. Backend repository defaults collector OFF, nominal90s/min60s, **not a verified production flag** | No Oracle-specific feature acceptance | Compare actual server to GitHub without blind overwrite; backup, stage targeted fixes, syntax/health/rollback; keep order execution disabled |
| **3 — Data coordination** | App cache + Dhan/Oracle upstream | `src/refresh_coordinator.py` `916835a4`: four logical lanes; Readiness 10s cache `a0adc6e2`; equity snapshot 2s validated cache `089b11e5`; age+elapsed <=120s guard `02feb6c7`, repaired closure `24c03cb9` | 907/907 PASS #1555; readiness test repair 912/912 #1558; equity 916/916 #1560; final math fix #1565 **919/919 PASS** | Four-provider-lane collector and faster 15–30s Dhan collection **NOT DEPLOYED**; 180s bootstrap + 429 protection remain | #645 not yet verified signed/install | Verify Oracle rate limits, batch quote/index/history/option cache behavior before changing upstream refresh cadence; no unnecessary fanout |
| **4 — App/contract tests** | App + Backend | Nine route method matching; strict `/v2/snapshot` freshness and read-only assessment; mocked caching/reconnect/429 guards | #1563 **918 tests, 2 errors** due to local `math` scope; fixed `24c03cb9` and test `39b34182`; #1565 SUCCESS | Schema for running Oracle endpoints **NOT VERIFIED** | On-device Scanner, Candles, Index, Super Five, Filters **NOT VERIFIED** for latest candidate | Run full tests on intended release SHA, then actual deployed API parity and market-hours device checklist |
| **5 — APK build & diagnostics** | GitHub Actions | 2.3.129 build #644 signed PASS, artifact id 14202710472 (older source); version advanced to 2.3.130 `26455d17`, started Build #645 | Build #644 verified v2.3.129 code 74401; #645 **IN_PROGRESS at 2026-11-16 latest inspection** | No deployment from APK | #645 **DIAGNOSTIC CANDIDATE ONLY**; signed artifact/versionCode/install result not yet known | Let #645 finish. Log actual job failure/success, versionCode/signature and artifact; do not launch a new APK before all stages 1–4 are complete |
| **6 — Final release & phone acceptance** | Joint team + user device | Permanent APK-last policy and grouped audit procedure recorded; Handoff updated | **BLOCKED by missing production evidence** (not a CI failure) | Collector/indices/options actual stability pending | **NOT TESTED** for #645; no final release sign-off | Close open Oracle defects, prove contract, rerun final CI, then build a **new approved** version and log first refresh, prices, candles, scanner, Super Five, options, resume and Error Doctor |

## Error → repair → verification ledger

| Date (IST) | Scope / APK or CI | What failed or was seen | Fix / commit | Retest / result | Still open? |
|---|---|---|---|---|---|
| 2026-11-16 | CI #1546–#1548 | One stale regression asserted literal `fallback` instead of actual equity bootstrap call | `0ab3e3f4` | #1549 **893/893 PASS** | No (source test) |
| 2026-11-16 | CI #1556–#1557 | Old readiness test expected mocked network on disconnected feed | `58604f47`: test sets unit-test-only connected session and invalidates cached readiness between bad cases | #1558 **912/912 PASS** | No (source test) |
| 2026-11-16 | CI #1563 | 2 errors: `NameError` from later local `import math` used by nested snapshot-age predicate | `24c03cb9` + guard test `39b34182` | #1565 **919/919 PASS** (job 133158750736) | No at source test checkpoint; Oracle/phone not proved |
| 2026-11-16 | APK #644 v2.3.129 | **Build PASS**, not an app error; older source, new Oracle fixes absent | Next source updates and candidate #645 | APK #644 signed package/versionCode verified; not a phone PASS | Yes: outdated relative to current source |
| 2026-11-16 | APK #645 v2.3.130 | **No APK failure established** while run is in progress | `26455d17` triggered diagnostic build, no new fix presumed | Await actual build log, signing, artifact | Pending |
| User mobile reports, earlier releases | Watchlist delayed first refresh, index quote/candle gaps, WAIT filters, Super Five, options errors | Multiple app-source guards/caches documented in the append-only Work Log | Automated tests partly green; **latest phone re-test pending** | **Yes—end-to-end verification** |
| 2026-11-16 | Oracle Production | Missing evidence for nine routes, collector enabled, real snapshot age/count, Dhan cadence | Scripts `805dfce2`, `5b275ad3`; repository source-only route fixes | No Oracle host execution in latest batches | **Yes—priority 1** |

## Per-change record — mandatory compact format

| Date/time IST | Batch / stage | File & change | Commit | Test/run & exact result | Oracle source/HTTP & result | APK build/versionCode/signature | Device result | Error → repair | Status / owner / next action |
|---|---|---|---|---|---|---|---|---|---|

Append dated factual rows to `docs/BOT_KING_WORK_LOG.md`; maintain this compact 1–6 summary at each milestone. Use **PASS** only with an exact source, CI, Oracle, APK or phone proof. Use **NOT RUN**, **IN_PROGRESS**, **FAILED**, **BLOCKED**, or **UNVERIFIED** rather than filling gaps. **Do not display credentials, tokens or account identifiers.**

## Release decision

**HOLD any new APK trigger.** Finish source+Oracle fixes and end-to-end verification first. Existing #645 stays a diagnostic candidate and is not automatically a release merely because GitHub successfully signs an APK. Four logical lanes do not establish four deployed Oracle upstream pipelines. Broker live orders stay OFF.
