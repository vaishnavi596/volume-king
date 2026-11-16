# BOT KING — Work, Result, Errors & Repair Tracker

**Owner decision: 2026-11-16.** This is the compact front page for the append-only `docs/BOT_KING_WORK_LOG.md`. The release gates are in `docs/BOT_KING_RELEASE_GATE_POLICY.md`. Update this table **together with each batch** so a new chat can distinguish planned work, source commits, CI proof, running Oracle proof, APK build result, phone result and follow-up fixes. The dates and statuses below are **as-of their exact check**, not forecasts.

## 1–6 joint work stages — current result

| Stage | Work / owner | Work performed (exact evidence) | Source / CI result | Oracle / actual result | APK / phone result | Remaining error, repair and next action |
|---|---|---|---|---|---|---|
| **1 — Audit** | App + GitHub + Oracle | Last eight runs checked before changes; read-only 9-route AST audit `scripts/audit_oracle_app_routes_readonly.py`, runtime GET-only collector probe `scripts/audit_oracle_collector_runtime_readonly.py`; release policy `d0bc841a` | Source AST audit 898/898 PASS #1552; runtime audit mocks 902/902 PASS #1553; **not an Oracle host test** | **NOT RUN** on customized live Oracle server; route hash, collector state, quote age unknown | #645 is a diagnostic build, phone launch **PASS**; live-data tests **FAIL/PARTIAL** | Run grouped Oracle deployed source+GET-only collector audit safely; record source hash, protected HTTP statuses, age/count and enabled flag |
| **2 — Server fixes** | GitHub backend + Oracle | Source-only authenticated `/v2/server-readiness` `f3163d4c`; fail-closed `/v2/assessment/{symbol}` `701ec398`; Dhan only / live orders OFF | Route/readiness parity 893/893 PASS #1549; assessment 894/894 PASS #1551 | **NOT DEPLOYED / NOT VERIFIED** on Oracle. Backend repository defaults collector OFF, nominal90s/min60s, **not a verified production flag** | No Oracle-specific feature acceptance | Compare actual server to GitHub without blind overwrite; backup, stage targeted fixes, syntax/health/rollback; keep order execution disabled |
| **3 — Data coordination** | App cache + Dhan/Oracle upstream | `src/refresh_coordinator.py` `916835a4`: four logical lanes; Readiness 10s cache `a0adc6e2`; equity snapshot 2s validated cache `089b11e5`; age+elapsed <=120s guard `02feb6c7`, repaired closure `24c03cb9` | 907/907 PASS #1555; readiness test repair 912/912 #1558; equity 916/916 #1560; final math fix #1565 **919/919 PASS** | Four-provider-lane collector and faster 15–30s Dhan collection **NOT DEPLOYED**; 180s bootstrap + 429 protection remain | #645 signed and launched on phone; Oracle data faults persist | Verify Oracle rate limits, batch quote/index/history/option cache behavior before changing upstream refresh cadence; no unnecessary fanout |
| **4 — App/contract tests** | App + Backend | Nine route method matching; strict `/v2/snapshot` freshness and read-only assessment; mocked caching/reconnect/429 guards | #1563 **918 tests, 2 errors** due to local `math` scope; fixed `24c03cb9` and test `39b34182`; #1565 SUCCESS | Schema for running Oracle endpoints **NOT VERIFIED** | Phone tested: Historical candles visible; Scanner/Filters/Super Five **FAIL/PARTIAL**; BankNifty/Sensex LTP unavailable | Run full tests on intended release SHA, then actual deployed API parity and market-hours device checklist |
| **5 — APK build & diagnostics** | GitHub Actions | 2.3.129 build #644 signed PASS, artifact id 14202710472 (older source); version advanced to 2.3.130 `26455d17`, started Build #645 | Build #644 verified v2.3.129 code 74401; #645 **SUCCESS at later verified 2026-11-16 inspection**, 919/919 offline PASS, signed package `com.botking.bot_king`, `versionCode=74501`, phone shows v2.3.130; DATA ACCEPTANCE FAILED | No deployment from APK | #645 **signed BUILD PASS** (artifact 14206624325, versionCode 74501); user phone launched, but live data FAILURE/PARTIAL | #645 complete and signed; diagnose device/Oracle failures before any new APK |
| **6 — Final release & phone acceptance** | Joint team + user device | Permanent APK-last policy and grouped audit procedure recorded; Handoff updated | **BLOCKED by missing production evidence** (not a CI failure) | Collector/indices/options actual stability pending | **TESTED ON PHONE**: launch PASS, watchlist refresh/index 2/3/filter/429 FAIL; no final release sign-off | Close open Oracle defects, prove contract, rerun final CI, then build a **new approved** version and log first refresh, prices, candles, scanner, Super Five, options, resume and Error Doctor |

## Error → repair → verification ledger

| Date (IST) | Scope / APK or CI | What failed or was seen | Fix / commit | Retest / result | Still open? |
|---|---|---|---|---|---|
| 2026-11-16 | CI #1546–#1548 | One stale regression asserted literal `fallback` instead of actual equity bootstrap call | `0ab3e3f4` | #1549 **893/893 PASS** | No (source test) |
| 2026-11-16 | CI #1556–#1557 | Old readiness test expected mocked network on disconnected feed | `58604f47`: test sets unit-test-only connected session and invalidates cached readiness between bad cases | #1558 **912/912 PASS** | No (source test) |
| 2026-11-16 | CI #1563 | 2 errors: `NameError` from later local `import math` used by nested snapshot-age predicate | `24c03cb9` + guard test `39b34182` | #1565 **919/919 PASS** (job 133158750736) | No at source test checkpoint; Oracle/phone not proved |
| 2026-11-16 | APK #644 v2.3.129 | **Build PASS**, not an app error; older source, new Oracle fixes absent | Next source updates and candidate #645 | APK #644 signed package/versionCode verified; not a phone PASS | Yes: outdated relative to current source |
| 2026-11-16 | APK #645 v2.3.130 | **No APK failure established** while run is in progress | `26455d17` triggered diagnostic build, no new fix presumed | Build/signing validated; record and repair observed device FeedErrors | Pending |
| User mobile reports, earlier releases | Watchlist delayed first refresh, index quote/candle gaps, WAIT filters, Super Five, options errors | Multiple app-source guards/caches documented in the append-only Work Log | Automated tests partly green; **latest phone re-test pending** | **Yes—end-to-end verification** |
| 2026-11-16 | Oracle Production | Missing evidence for nine routes, collector enabled, real snapshot age/count, Dhan cadence | Scripts `805dfce2`, `5b275ad3`; repository source-only route fixes | No Oracle host execution in latest batches | **Yes—priority 1** |

## Per-change record — mandatory compact format

| Date/time IST | Batch / stage | File & change | Commit | Test/run & exact result | Oracle source/HTTP & result | APK build/versionCode/signature | Device result | Error → repair | Status / owner / next action |
|---|---|---|---|---|---|---|---|---|---|

Append dated factual rows to `docs/BOT_KING_WORK_LOG.md`; maintain this compact 1–6 summary at each milestone. Use **PASS** only with an exact source, CI, Oracle, APK or phone proof. Use **NOT RUN**, **IN_PROGRESS**, **FAILED**, **BLOCKED**, or **UNVERIFIED** rather than filling gaps. **Do not display credentials, tokens or account identifiers.**

## Release decision

**HOLD any new APK trigger.** Finish source+Oracle fixes and end-to-end verification first. Existing #645 stays a diagnostic candidate and is not automatically a release merely because GitHub successfully signs an APK. Four logical lanes do not establish four deployed Oracle upstream pipelines. Broker live orders stay OFF.

## 2026-11-16 13:39–13:40 IST — Actual device v2.3.130 market-session evidence (7 screenshots)

**Evidence:** Owner screenshots at 13:39–13:40 IST from a phone visibly running `BOT KING v2.3.130`. This is **device observation**, not CI or Oracle process proof. Preserve the status labels literally; do not call historical votes live probabilities. Phone screenshots show six navigation tabs (Home, Options, Settings, Scanner, Watchlist, Chart), which also conflicts with the earlier 3-tab desired UI: mark a design-alignment task, not a server fault.

| Device area | Observed result on phone | Classification / key uncertainty | Next repair/audit owner |
|---|---|---|---|
| Version and APK | Title clearly shows `v2.3.130`; Android phone launched. GitHub Build #645 [43825726713](https://github.com/vaishnavi596/volume-king/actions/runs/43825726713) succeeded, 919/919 offline PASS, package `com.botking.bot_king`, versionCode `74501`, permanent signing verified, artifact [14206624325](https://github.com/vaishnavi596/volume-king/actions/runs/43825726713/artifacts/14206624325) | **APK BUILD PASS + DEVICE LAUNCH PASS**, NOT market-data acceptance | Preserve this as diagnostic candidate; don't start another APK until all release gates |
| Index LTP | NIFTY `25,063.70` shown, labeled `LTP last collected 28 sec old, exchange timestamp unverified`; BANKNIFTY and SENSEX `Dhan LTP unavailable` | **INDEX PARTIAL / FAIL 2 of 3** at screenshot; exact cause unknown | Oracle actual index batch route/mapping/upstream 429/cache, isolated from watchlist |
| System Health | `2 issue(s) need attention`; `Candle/filter audit: 2 active failure(s) • BANKNIFTY, LT`; `Dhan watchlist batch: Oracle snapshot stale or invalid; last Dhan prices retained, check server collection`; 54-symbol filters: 52 analyzed / 2 errors / 0 insufficient / 0 pending | **FAIL**, historical scan coverage is not verified live quote coverage | Oracle snapshot collector enabled/age/last collection, LT candle path, BANKNIFTY; retain last good values but label not-live |
| Error history | `dhan_index_ltp_batch: FeedError` recovered at 13:38:27; `dhan_options: FeedError` 13:38:27 and 13:39:32; `oracle_assessment: FeedError` 13:38:32; `watchlist_dhan_batch: FeedError` 13:39:31 and 13:40:33; `scanner: FeedError` 13:39:51; `dhan_batch: FeedError` 13:40:33 | **ERROR RECORDED**, generic FeedError does not prove HTTP code or specific cause | Get only redacted server per-route stage/cooldown logs; don't guess 403/404/429 |
| Watchlist equities | RELIANCE cached `1341.00`, HDFCBANK cached `815.90`; display says `LTP cached • not live • refresh failed`; 5m HIST votes present | **PARTIAL** historical/cached only, current live equity refresh FAILED | Oracle /v2/snapshot + bounded recovery and age/available count; no destructive cache reset |
| Filters/factors | News `N 20 news • WAIT` or `N WAIT`, Futures `F WAIT`, Options `O WAIT`; `Oracle 4 factors / 5 filters • WAIT • not requested` for several symbols; one row says `informational only • live orders OFF` | **NOT FUNCTIONAL / NOT VERIFIED**; avoid fabricated scores | Compare production /v2/assessment and option expiry/chain endpoints to app contract; source-only placeholders are not real factors |
| Scanner candles | NIFTY `5m WAIT`, latest completed candle `16 Nov 13:35`; historical/unverified; 2 bullish / 4 bearish votes; EMA, MACD, VWAP etc. shown | Historical candle computations **PARTIAL PASS**, verified live signal **NOT PASS** | Check Dhan historical response completeness/age and reason WAIT; do not promote historical to live |
| Super Five | `Dhan historical scan paused: HTTP 429 / cooldown; 38 symbols not attempted`, 1 history unavailable; AXISBANK historical 100/0, `5 engines • 0/5 verified • overall WAIT` | **FAIL/PARTIAL**, explicit HTTP 429 plus incomplete scan | Preserve provider cooldown, resume from cursor without duplicate 51-history fanout; never accelerate beyond Dhan limit |
| Navigation/UI | Six tabs visible and Watchlist label truncated; oversized cards with many `WAIT` labels | UX/design discrepancy from desired 3-tab Dashboard/Watchlist/Settings; lower priority than data integrity | Audit `src/main.py` UI after server fix, no APK yet |

**Evidence discipline:** Phone verifies app startup, historical chart display and retained old values. It does **not** prove that backend routes are absent, whether Oracle collector is enabled, whether cached prices are exchange-live, or which particular status produced `FeedError`. One explicit HTTP429 is shown for historical scan; it must not automatically be assigned to every failed endpoint. No real orders were placed; UI indicates live orders OFF.

**Next joint batch, before any APK:** Stage 1 run read-only deployed Oracle route and collector scripts, capture HTTP status and sanitized state/age. Stage 2 reconcile only missing/invalid server routes or collector, backup before edit. Stage 3 examine 429 historical scan pacing and independent index batch. Stage 4 rerun actual end-to-end data tests and CI. Document subsequent fixes and retests in a new ledger row, never overwrite this observed failure.

## 2026-11-16 13:45 IST — v2.3.130 follow-up device observation (3 more screenshots)

**New phone evidence, not a GitHub or Oracle server retest.** Owner provided three Settings/Scanner screenshots around **13:45 IST** following the earlier 13:39–13:40 screenshots. These do not erase earlier documented failures.

| Time / app area | New directly visible result | Interpretation and remaining work |
|---|---|---|
| 13:45 Settings System Health | Green `No active errors reported`, `54-symbol filters • 54 analyzed • 0 errors • 0 insufficient • 0 pending`, `51 equities + 3 indices` | **Local health/analysis recovery observed** from earlier `52 analyzed • 2 errors`. This is NOT independent proof that fresh quote collection, index 3/3 or Oracle routes recovered. Reinspect on real next update |
| 13:45 Settings Error History | History still includes `dhan_index_ltp_batch` RECOVERED at 13:38:27 and previously RECORDED `dhan_options`, `oracle_assessment`, `watchlist_dhan_batch`, `scanner`, `dhan_batch` | History entries retained appropriately. A **green active-health summary** and **past error records** are not contradictory; do not delete or call each prior failure currently active |
| 13:45 Scanner detail | VWAP `BEARISH • Session VWAP 25257.41`; SMC Structure, Order Block, FVG, Liquidity Sweep marked NEUTRAL; Pivot Points BULLISH at 25243.97 | Historical technical indicator computations visible, not a LIVE signal; exact symbol/date is outside screenshot crop, so do not assert it from this image alone |
| 13:45 Scanner OI | `OI Support UNAVAILABLE` though highest PE OI in ATM window 25,200 shown; `OI Resistance UNAVAILABLE` with highest CE OI 25,300; OI Profile `UNAVAILABLE` with Dhan ATM ±3 strikes; Max Pain `UNAVAILABLE` showing 25,250; each explicitly `unverified`, display-only | **Partial Options data display** observed, but signal eligibility/verified OI filter remains **FAIL/UNAVAILABLE**. Do not infer Dhan real-time/live verification from displayed strike values; audit expiry/chain response mapping and missing validation before any UI status promotion |

**Updated assessment:** Stage-4 local 54-symbol analysis completeness improved to **54/54** and active error count to **0** at 13:45, whereas Stage-2/3 production Oracle quote age and independent index availability are still **UNVERIFIED**. Some option figures are present in read-only display while OI/Max Pain filters remain unavailable. The earlier explicit Super Five `HTTP 429` and 38 unattempted symbols are not shown recovered here. No fresh APK requested or made.

**Next journal event required:** inspect actual Oracle deployed-route/source/collector state, age/count and errors via already-prepared read-only scripts, not the UI active-health badge alone. Fix only proven server/contract faults with backup and evidence; keep 429 cooldown and paper-only mode.

## 2026-11-16 — Option PCR (index vs equity) and five Oracle assessment filters joint audit

**Owner observations:** PCR appears for NIFTY/BANKNIFTY/SENSEX, but may be missing for other selected equities; equity coverage has **not been exhaustively checked on phone**. All five desired filters are reported nonfunctional. Both reports are **open**; do not promote source contract tests to live Oracle entitlement/availability.

| Scope | Concrete source evidence | What is NOT proven / actual blocker | Next proof and correction |
|---|---|---|---|
| Index PCR | `src/server_feed.py::option_expiries` and `option_chain_metrics` support the mapped three indices. `src/main.py::refresh_selected_options` loads a **selected underlying only**, then listed expiry, 3.25s pacing and Dhan option-chain metrics | Display for every index/current expiry not independently observed in this audit; user's report remains a hypothesis | Record per-index expiry and option-chain stage/status, without new request storms |
| Equity PCR | Same client permits mapped equities like RELIANCE and HDFCBANK; backend `/dhan/option-expiries` and `/dhan/option-chain` explicitly accept `NSE_EQ` **when DYNAMIC_INSTRUMENTS maps the underlying**; absent broker-listed expiry returns 422, unavailable/incomplete Dhan entitlement 502, pacing 429 | Mapping to NSE_EQ LTP **does not prove the symbol has options or an active chain**. No live Oracle request/expiry test for 51 equities; client **does not auto-query all 51 option chains** (correct quota protection) | Build eligible-underlying diagnostic matrix from instrument master and safe Oracle read-only route results; classify unmapped / no expiry / rate-limited / incomplete / available; no fabricated PCR |
| Five Oracle filters | `backend/server.py::GET /v2/assessment/{symbol}` **source-only placeholder** explicitly sets `collection_status=not_configured`, all five `oi_support, oi_resistance, max_pain, pcr, candle_trend` to `status=unavailable`, 4 factors news/futures/options/candle unavailable, bullish_score/bearish_score None, `signal_eligible=False` | **Confirmed source functional gap, not merely missing UI formatting.** Actual Oracle route may be different; no real assessment producer has been proven | Verify production route and underlying per-symbol evidence. Implement a validated, read-only shared assessment producer only after accurate source+freshness/cooldown contract; DO NOT substitute historical scores, PCR-only, or unknown market data for verified filter percentages |
| Historical bullish/bearish percentages | `src/main.py` shows HIST directional candle/technical votes and independent `five_engine_summary` coverage count. `src/shared_assessment_ui.py` correctly presents Oracle filter unavailable as WAIT | Historical B100/S0 is **not** a 5-filter 100% probability nor verified LIVE signal; green System Health 54 analyzed says nothing about validated five Oracle factors | Keep HIST label; separately show five-filter verified coverage and missing reasons, avoid implying success probability |

**Source test commits (no provider calls):** `695e5d9c` adds equity/index read-only PCR source-contract tests; `a0faec39` adds five-filter no-fabrication tests. **CI outcomes PENDING** when committed. No Oracle Production deployment/change and no new APK.

**Release gate:** block the next APK until the data-provider availability matrix and real five-filter producer are either verified for supported underlyings or explicitly labeled out-of-scope with user-approved scope. No live orders.

## 2026-11-16 — PCR symbol eligibility and source-audit follow-on result

| Stage / file | Work done | Exact proof | Oracle / actual mobile proof | Result / next |
|---|---|---|---|---|
| Stage 1/4 · PCR + 5 filters | Previous source audit tests for equity/index PCR and unavailable Oracle 5 filters `695e5d9c`/`a0faec39` | #1567 [43830743529](https://github.com/vaishnavi596/volume-king/actions/runs/43830743529) job `133175214724` **928/928 PASS** | **NO** actual Oracle or newly available PCR / five filters | Source contract confirmed, real five-filter producer still missing |
| Stage 2 · option underlying mapping-only utility | `backend/option_underlying_status.py` `38926b79`: return mapped/unknown, NEVER treat NSE_EQ instrument security ID as proof of listed F&O, option expiry, chain or PCR; no provider requests | CI #1568 pending on first check | Not deployed on Oracle, no live market evidence | Partial safe diagnostic / no source data aggregation |
| Stage 4 · regression | `tests/test_option_underlying_status.py` `ee08f363`: index/equity/unmapped/cash-only, 70-limit, no broker calls | CI #1569 pending on first check | Not a live Dhan test | Test source created, await full CI |
| Release gate | **No more APK** until real Oracle 9-route/collector check, per-supported equity expiry status and five-filter validated producer | Signed #645 v2.3.130 remains earlier diagnostic candidate | Phone has historical WAIT/PCR uncertainty, server unverified | **BLOCKED**, preserve source→Oracle→phone proof separation |

**Interpretation:** PCR cannot be promised for every one of 51 equities; option underlying eligibility must be verified from Dhan-listed expiries / option chain and entitlements, with 422/no-expiry, 429/pacing and 502/unavailable separated. The new helper performs ZERO broker requests and is not a real PCR implementation. Five filter statuses remain unavailable in GitHub source.

## 2026-11-16 — PCR equity mapping-only route: release gate update

| Stage | GitHub source/CI proof | Oracle/phone result | Remaining |
|---|---|---|---|
| 1/4 — Option PCR source | #1569 [43831492105](https://github.com/vaishnavi596/volume-king/actions/runs/43831492105) job `133177640327`: **931/931 PASS**; #1568 `928/928 PASS` | No real equity option entitlement verified | Bounded selected-equity expiry/chain runtime audit |
| 2 — Server diagnostic | `backend/server.py` added authenticated GET `/v2/option-underlying-status/{symbol}` at `3fa20d64`, with pure mapping status only. Tests `4b28e245` guard 403/422/no Dhan request; #1570/#1571 CI PENDING at first check | **Source-only, NOT DEPLOYED** on customized Oracle | Compare production source, backup+deploy only after operator read-only audits |
| 3/4 — Five filters | Known source `/v2/assessment/{symbol}` remains hard-coded `not_configured` and five WAIT; no proven 0–100 directional producer | User device five filters WAIT | Validate separate actual factor inputs/expiry/time; don't mix with historical technical scores |
| 5/6 — APK release | v2.3.130 Build #645 signed PASS but phone observed live data failures | **NOT ACCEPTED** | No new APK before complete audit, fixes, CI, Oracle+device verification |

**No fabricated PCR:** mapping-only means the Dhan cash/index security ID is known, *not* that this equity is F&O-listed or that a fresh option chain exists. New endpoint performs zero Dhan requests. The 15–30 second data collection target and genuine Oracle filter producer remain unimplemented/unverified.

## 2026-11-16 — Oracle five-filter read-only source classification

| Stage | Work completed | Code / CI proof | Oracle Production | Residual Error / next action |
|---|---|---|---|---|
| 1 / 4 | Earlier PCR mapping route source tests completed | #1571 [43832625673](https://github.com/vaishnavi596/volume-king/actions/runs/43832625673) **932/932 PASS**, job `133181353353` | **NOT RUN** | Source vs live deployment still unknown |
| 1 / 2 | Added Python AST audit of deployed `server.py` for actual five filter names, four factor names and known `not_configured` placeholder: `scripts/audit_oracle_five_filters_readonly.py` | `2bba9280` commit; new source tests `e6677c7f`, CI **PENDING** at initial inspection | **NOT RUN**; no SSH tool | Operator run grouped 9-route source+collector GET+five-filter AST audits on Oracle. Source that differs from known placeholder still does **not** prove calculations work |
| 2 / 3 | No change to real Oracle producer: five filters still unavailable in GitHub source; no new Dhan/option/assessment requests | Static helper only, no network | No production deployment | Implement verified per-underlying factors only after source/contract/expiry/freshness audit; unavailable is safer than invented percentages |
| 5 / 6 | New signed APK withheld as user instructed | #645 v2.3.130 diagnostic signed previously | Phone PCR/five filters not accepted | Complete all gates and journal evidence before next build |


## 2026-11-16 — PCR-02 continuation: ORACLE-FILTER-AUDIT-02

| Stage | Work / evidence | Verified status | Not verified / next gate |
|---|---|---|---|
| 1, 4 · PCR-02 source | CI #1570 931/931 and #1571 932/932 PASS from Actions, mapping-only diagnostic; GitHub source has known five-filter placeholder | **SOURCE CI PASS; FILTER PRODUCER FAIL/PLACEHOLDER** | Equity F&O expiry, chain, PCR and all five live filter percentages **UNVERIFIED** |
| 1, 2 · Oracle audit | Read-only scripts for 9 source routes, collector health GET and five-filter source AST inspected; [execution matrix](ORACLE_FILTER_AUDIT_02_OPERATOR_GATE_20261116.md) committed `5455ada6` | **AUDIT PLAN READY ONLY** | No SSH executor / no Oracle commands executed; await sanitized production output |
| 3 · CI follow-up | #1572 (run 43833438579) head `e6677c7f` at inspection | **IN PROGRESS, NOT PASS** | Re-check result and tests before next code gate |
| 5, 6 · Deployment and APK | Explicit server-first/no-order release gate retained | **NOT DEPLOYED; NO NEW APK** | Backup-first specific source fix, CI, Oracle verification, then independent phone validation |


- **CI #1572 FINAL VERIFIED (2026-11-16):** [run 43833438579](https://github.com/vaishnavi596/volume-king/actions/runs/43833438579), commit `e6677c7f`, job `133184087265`, **936/936 PASS** (`Ran 936 tests in 351.753s; OK`). This supersedes the earlier in-progress snapshot above. It establishes offline audit regression success only; Oracle execution, five-filter producer, device PCR and deployment remain **UNVERIFIED**. No APK created.


## 2026-11-16 — Joint batch ORACLE-FILTER-AUDIT-03 (evidence classification)

| Stage | Exact work | Code/tests/observed result | Outstanding gate |
|---|---|---|---|
| 1/2 · source and collector | Reviewed three read-only Oracle scripts; identified absence of joined triage classification | New non-network classifier `ee9b0243` distinguishes source gaps, 403, 404, 429, disabled/stale status, known placeholder vs unknown producer. **Source added**, not run against production | Actual Oracle sanitized reports required; SSH unavailable here |
| 3/4 · PCR / five filters | Fail-closed audit decision tests cover 6 cases `ef2ca0d0`; runbook updated `98b05dc6` | New suite **CI PENDING** at tracker update; prior #1572 **936/936 PASS** applies only to earlier audit test commit | Five-filter producer and equity PCR availability **UNVERIFIED**; do not fake percentages |
| 5/6 · end-to-end / release | Journal written `aebbd77e`, no deployment/orders/APK | **NOT DEPLOYED, NOT RELEASED** | Source CI, Oracle backup-first corrective patch, device proof before APK |


- **Audit-03 CI run identified:** [#1573 / 43835167845](https://github.com/vaishnavi596/volume-king/actions/runs/43835167845) at `ef2ca0d0` (six new classifier tests) was **in_progress** during inspection. This is **not a PASS yet** and is separate from #1572's verified 936/936 success; no Oracle or device proof. No APK.


## 2026-11-16 — ORACLE-FILTER-AUDIT-03 CI #1573 verified completion

- **Final CI result:** [BOT KING Offline Regression #1573, run 43835167845](https://github.com/vaishnavi596/volume-king/actions/runs/43835167845), job `133189866871`, tested source commit `ef2ca0d097145f448bceef75225a39044ff3a8bc`: **942/942 PASS** (`Ran 942 tests in 98.528s`; GitHub job and workflow completed success). This supersedes earlier **IN PROGRESS** notes, which are historical snapshots.
- Six new classifier test cases passed as part of full suite. This does **not** verify live Oracle server routes, configured collector, live PCR entitlement or running five-filter producer. Actual Oracle audit remains blocked on operator SSH execution; no live deployment, no new APK, no order calls.
- Next: execute three read-only audits on Oracle with sanitized JSON, classify, isolate concrete failure, backup production, and only then repair validated defects. Keep source/CI/server/mobile evidence distinct.


## 2026-11-16 — AUDIT-04 source protection batch
| Stage | Problem found | Corrective commit + test | Result / next |
|---|---|---|---|
| 1/2 · Oracle collector audit | HTTP 200 malformed JSON list could crash summarizer instead of preserving unknown status | `a81c2470` + `b0da29d4` | **SOURCE PATCHED / CI PENDING**; live Oracle not tested |
| 1/3 · Joined audit | Missing required route could still set `source_audit_complete=true` | `b9f6da33` + `dbd27e40` | **SOURCE PATCHED / CI PENDING**; now exact 9/9 and single assessment required |
| 4/5/6 · PCR / five filters / release | Live assessment producer and equity option entitlement not proven | No real producer or APK change | **ORACLE UNVERIFIED; APK BLOCKED** |

- **Exact new CI runs identified:** #1574 [43835829523](https://github.com/vaishnavi596/volume-king/actions/runs/43835829523) head `b0da29d4` and #1575 [43835881689](https://github.com/vaishnavi596/volume-king/actions/runs/43835881689) head `dbd27e40` were both **IN PROGRESS** at observation. Neither was called PASS prematurely. Previous #1573 (942/942) belongs to older source and does not validate these two fixes.


## 2026-11-16 — AUDIT-04 CI closeout / AUDIT-05 source-route guard
| Stage | Specific proof | Verified result | Remaining |
|---|---|---|---|
| 1/2 · collector classifier | #1574 943/943 PASS; #1575 945/945 PASS, exact earlier source heads | **OFFLINE CI PASS** | Oracle collector runtime not executed |
| 2/3 · assessment route identification | Non-`app.get` decorator could masquerade as declared Oracle route; patched `a42089d5`, tested `0f4397af` | **CODE COMMITTED; NEW CI PENDING** | Live route and verified producer NOT established |
| 4/5/6 · PCR/release | No entitlement proof or live Oracle checks | **BLOCKED** | No APK; operator audit then backup-first fixes |

| 1/2 · source audit consistency | Joined AST reports could refer to different server.py revisions | `e582b84f` source + `aa75e0cd` SHA mismatch regression; **CI PENDING**, no live audit |

- **Exact Audit-05 CI submissions:** #1576 [43837330114](https://github.com/vaishnavi596/volume-king/actions/runs/43837330114), tested head `0f4397af` (decorator guard), and #1577 [43837462720](https://github.com/vaishnavi596/volume-king/actions/runs/43837462720), tested head `aa75e0cd` (cross-report SHA guard). Both were **in_progress** when last checked; neither is yet counted PASS. Previous #1575 **945/945 PASS** is independent prior head.

| 1/2 · collector freshness | A self-reported recent status could contradict measured snapshot or last-success age | `c1c01b1b` + `0128ca1a`: two audit warnings, with 2 interval guard, new CI **PENDING**. Does not verify actual exchange freshness or live Oracle. |

- **CI #1576 FINAL:** [run 43837330114](https://github.com/vaishnavi596/volume-king/actions/runs/43837330114), head `0f4397af`, job `133197110014`, **946/946 PASS** (`Ran 946 tests in 101.635s`; GitHub completed success). This validates decorator-guard offline regression only; Oracle runtime remains unknown. #1577 (43837462720) and new #1578 (43837640203, head `0128ca1a`) were **IN PROGRESS** at latest inspection; no premature PASS.


## 2026-11-16 — AUDIT-05 CI closure (exact completed runs)
- #1577 [43837462720](https://github.com/vaishnavi596/volume-king/actions/runs/43837462720), head `aa75e0cd2a2933218117e77e024f0405cf8cf128`, job `133197544414`: **947/947 PASS** (GitHub Actions completed success, `Ran 947 tests in 117.531s`). Tests cover joined source-SHA mismatch guard.
- #1578 [43837640203](https://github.com/vaishnavi596/volume-king/actions/runs/43837640203), head `0128ca1ab0987d1c051052689beebd99a4fa3419`, job `133198147934`: **949/949 PASS** (GitHub Actions completed success, `Ran 949 tests in 228.965s`). Tests cover collector status-vs-age contradictions. Previous #1576 **946/946 PASS** on `0f4397af` is also recorded.
- **Classification:** GitHub **SOURCE/CI PASS** only. **NO ORACLE SSH execution** or sanitized reports received, **NO production deployment**, **NO real equity F&O PCR proof** or running five-filter producer, **NO new APK/orders**. Do not misinterpret CI completion as an end-to-end market-data fix.
- **Gate:** operator-run scripts listed in `docs/ORACLE_FILTER_AUDIT_02_OPERATOR_GATE_20261116.md` on Oracle, then run offline joined classifier. Source SHA in both AST reports must match; classify live GET errors and collector timestamps before backup-first remedial changes.


## 2026-11-16 — AUDIT-06 evidence validation
| Stage | Confirmed source-level issue | Fix/test | Evidence status |
|---|---|---|---|
| 1/2 · source SHA parity | Identical arbitrary strings could pass SHA agreement without real fingerprint | `0115b72e` + `685a35cc` | Code/test committed; CI pending; Oracle unverified |
| 2 · collector age audit | Nonfinite/negative values lacked strict bounded validation | `0115b72e` + `685a35cc` | Code/test committed; no real runtime readings |
| 3/4/5/6 · PCR, assessment and APK | No Oracle source/runtime proof yet | No production patch or APK | Unverified/block unchanged |

- **Exact CI run opened:** #1579 [43838615921](https://github.com/vaishnavi596/volume-king/actions/runs/43838615921), head `685a35cc`, was **IN PROGRESS** at inspection. The 949/949 PASS #1578 applies to the previous test head only; no claim yet for Audit-06.


## 2026-11-16 — AUDIT-07 quote coverage warning
| Stage | Issue | Code / tests | Runtime status |
|---|---|---|---|
| 1/2 · collector snapshot | Recent status with zero or unknown quote count lacked an explicit diagnostic | `374f3f16` source + `6220e02e` tests, CI PENDING | No real Oracle audit; no quote freshness proof |
| 3/4/5/6 | PCR/Five Filter producers and release | No broker/production changes | Still UNVERIFIED; APK blocked |

- **Exact new CI runs:** #1579 [43838615921](https://github.com/vaishnavi596/volume-king/actions/runs/43838615921), head `685a35cc`, and #1580 [43838847662](https://github.com/vaishnavi596/volume-king/actions/runs/43838847662), head `6220e02e`, both **IN PROGRESS** when inspected. Neither has Oracle runtime proof or release status. Keep both pending until GitHub completed result and job count verified.


## 2026-11-16 — AUDIT-06/07 CI final results (confirmed)
- #1579 [run 43838615921](https://github.com/vaishnavi596/volume-king/actions/runs/43838615921), head `685a35cc`, job `133201392828`: **951/951 PASS**, GitHub job/workflow success (`Ran 951 tests in 162.235s`). Tests for valid SHA256 and finite audit evidence.
- #1580 [run 43838847662](https://github.com/vaishnavi596/volume-king/actions/runs/43838847662), head `6220e02e`, job `133202162167`: **953/953 PASS**, GitHub job/workflow success (`Ran 953 tests in 200.350s`). Tests include recent label with zero/unknown equity cache quote count.
- Historical in-progress entries for these runs are superseded. These results are strictly **offline CI**, not evidence of Oracle collector execution, five-filter live signals, or equity PCR entitlement. No deployment, no orders, no APK.


## 2026-11-16 — AUDIT-08 protected read-only loopback request
| Stage | Confirmed source exposure | Fix and validation | Actual environment |
|---|---|---|---|
| 1/2 · operator GET health/readiness/snapshot | Opener disabled proxy but allowed HTTP redirects, risking propagation of protected header beyond loopback | `92c3597f` no-redirect handler, `55cffa26` regression. **CI PENDING** | No live Oracle run or reported incident |
| 3/4/5/6 · PCR, five filters, APK | No new producer or live entitlement proof | No APK/orders/deployment | UNVERIFIED |

- **Exact Audit-08 CI started:** #1581 [run 43839664916](https://github.com/vaishnavi596/volume-king/actions/runs/43839664916), head `55cffa26`, was **IN PROGRESS** when checked. This source/test security fix is not yet CI PASS; previous #1580 953/953 applies to prior commit.


## 2026-11-16 — AUDIT-08 closure / AUDIT-09
| Stage | Work completed | Verified evidence | Remaining |
|---|---|---|---|
| 1/2 · protected Oracle GET | No redirect follow source + regression in CI #1581 | **954/954 PASS** at `55cffa26` | Real Oracle routing not probed |
| 1/2 · runtime error triage | HTTP 3xx now emits `UNEXPECTED_REDIRECT`, patch `76990163`, regression `1b4a0113` | **SOURCE COMMITTED; CI PENDING** | No production 3xx observed, not claim actual incident |
| 3/4/5/6 · five filters/PCR/release | No live producer or entitlement proof | No Oracle patch, orders, APK | Blocked on read-only Oracle outputs |

- **AUDIT-09 exact CI run:** #1582 [43840281883](https://github.com/vaishnavi596/volume-king/actions/runs/43840281883), head `1b4a0113`, was **IN PROGRESS** when inspected. Do not claim PASS until completed; this is not Oracle runtime verification.


## 2026-11-16 — FIVE-FILTER-UI-01
| Stage | Observation | Corrective work | Verified / pending |
|---|---|---|---|
| 1/4 · Oracle assessment compact views | Watchlist/Super Five render only `oracle_assessment_notes()[0]`, masking explicit `not_configured` cause behind generic WAIT | `a326be97` adds concise reason, `8992cc0a` adds two regressions | Source committed; new CI pending; Oracle deployed response unverified |
| 2/3 · five-filter producer and equity PCR | GitHub source still placeholder; selected equity F&O expiry/entitlement unknown | No invented 0–100 scores, no extra API fan-out | UNRESOLVED; await Oracle evidence |
| 5/6 · APK | No new build | CI #1582 955/955 PASS from preceding source | APK blocked, phone outcome pending future release |

- **Exact new UI regression CI runs:** #1583 [43840874487](https://github.com/vaishnavi596/volume-king/actions/runs/43840874487), head `a326be97`, and #1584 [43840916114](https://github.com/vaishnavi596/volume-king/actions/runs/43840916114), head `8992cc0a`, both **IN PROGRESS** at inspection. Do not claim PASS yet. Source CI results do not prove device UI changed without APK deployment.


## 2026-11-16 — UNIFIED-54 coverage baseline and UI-02
| Stage | Invariant / work | Evidence status | Remaining |
|---|---|---|---|
| 1,3,4 · shared Dhan roster | Exactly **51 NSE equities + 3 indices = 54 symbols**; same shared filter/assessment contract across all | `29912ce8` new source regression; CI PENDING | Current Oracle assessment poll only selected symbols, no 54/54 real producer coverage; rate-safe design still required |
| 4 · known-placeholder UI | Full five-filter/four-factor response validated before marking `not_configured` | `5d4b7f8e` + `118bbfe3` committed, CI pending | Mobile APK not built |
| 2/4 · option PCR | All 54 mapping coverage does **not** mean all equities have listed derivatives | Mapping-only helper remains fail-closed | Per-symbol Dhan expiry/chain eligibility unverified |
| 5/6 · release | No deployment, APK or orders | SOURCE ONLY | Oracle runtime and mobile signoff pending |

- **Exact CI follow-up:** #1585 [43842689096](https://github.com/vaishnavi596/volume-king/actions/runs/43842689096) head `5d4b7f8e`, #1586 [43842735722](https://github.com/vaishnavi596/volume-king/actions/runs/43842735722) head `118bbfe3`, and new 54-roster #1587 [43842915421](https://github.com/vaishnavi596/volume-king/actions/runs/43842915421) head `29912ce8` were all **IN PROGRESS** at initial inspection. No PASS presumed before logs. All are offline-source CI, not an APK or real Oracle proof.

## 2026-11-16 — All historical fixes / 54-symbol release acceptance gate
| Stage | Coverage requirement | Verified / remaining |
|---|---|---|
| 1/2 | 51 equity + 3 index source universe, independent LTP/candle/rate limiting | Source roster test `29912ce8` CI pending; **54/54 Oracle/mobile not verified** |
| 3/4 | Scanner, Super Five, five filters, News/Futures/Options/Candle and PCR eligible per underlying | **Real validated producer absent in GitHub backend**, client polls only selected symbols; **not 54/54 PASS** |
| 5/6 | Before any APK, regression-check **all prior fixes** listed in [54-symbol release gate](BOT_KING_54_SYMBOL_ALL_FIXES_RELEASE_GATE_20261116.md) | `768ba669` checklist committed; APK BLOCKED; no Oracle/phone proof |
| CI | #1586 `118bbfe3` | **958/958 PASS**; other follow-up runs pending |

- **CI #1587 FINAL:** [run 43842915421](https://github.com/vaishnavi596/volume-king/actions/runs/43842915421), test head `29912ce8`, job `133215785431`, **961/961 PASS** (`Ran 961 tests in 116.066s`; completed success). This validates the 51 equities + 3 indices roster contract and safeguards against falsely equating cash mapping with options entitlement. It is **not** live 54/54 feature coverage. #1585 remained in progress at last check. No APK/deployment/Oracle execution.


## 2026-11-16 — CI #1585 failure root cause and superseding fix
- **Historical red CI explicitly retained:** [#1585 run 43842689096](https://github.com/vaishnavi596/volume-king/actions/runs/43842689096), head `5d4b7f8e`, job `133215020310`, **FAILED 1 of 957 tests** (`Ran 957 tests in 344.719s`, `FAILED (failures=1)`). Exact failed test: `test_not_configured_explains_wait_on_compact_cards`; assertion expected `server producer not configured` but new code correctly returned `Oracle 4 factors / 5 filters • WAIT • malformed response` for incomplete fixture. This is a **test-fixture/contract mismatch**, not evidence of live Oracle failure.
- **Superseding correction:** [test commit `118bbfe3`](https://github.com/vaishnavi596/volume-king/commit/118bbfe3d510fa611f7c5c734f896c9c52cbdca5) added complete factor/filter placeholder fixture plus incomplete-payload rejection test. [CI #1586 run 43842735722](https://github.com/vaishnavi596/volume-king/actions/runs/43842735722), head `118bbfe3`, job `133215174383`: **958/958 PASS**. #1587 961/961 PASS at `29912ce8` confirmed 54-roster source test. Do not delete history of #1585 or mislabel it production failure. Oracle/runtime/mobile not verified; no APK.


## 2026-11-16 — Shared 54-symbol assessment cache timestamp safety
| Stage | Source finding | Patch and proof | Oracle/device |
|---|---|---|---|
| 3/4 · all 54 shared assessment views | NaN/bool fetched timestamps could evade age expiry checks | `5d72c7c4` + `b9fd95b4` regression for equity and index selections. **CI pending** | No live 54/54 producer or device proof |
| 5/6 · release gate | Previous-fix and new-fix coverage still required | `docs/BOT_KING_54_SYMBOL_ALL_FIXES_RELEASE_GATE_20261116.md` | APK blocked |


| 3/4 · shared 54-symbol filter rendering | Malformed unhashable five-filter ID could raise `TypeError` and break screen | `3f0b0356` source + `51f67706` tests; CI PENDING; now fail-closed `WAIT • incomplete filters` for selected symbol; no 54/54 runtime proof |

- **Exact staged CI runs:** #1588 [43843886780](https://github.com/vaishnavi596/volume-king/actions/runs/43843886780) head `5d72c7c4`, #1589 [43843930827](https://github.com/vaishnavi596/volume-king/actions/runs/43843930827) head `b9fd95b4`, #1590 [43844067017](https://github.com/vaishnavi596/volume-king/actions/runs/43844067017) head `3f0b0356`, and #1591 [43844108880](https://github.com/vaishnavi596/volume-king/actions/runs/43844108880) head `51f67706` were **IN PROGRESS** at first check. Do not call any of these PASS yet; previous #1587 961/961 is older head. These are source/CI-only and not Oracle or mobile proofs.


## 2026-11-16 — UNIFIED-54 cache/filter safety CI closure
- [CI #1588](https://github.com/vaishnavi596/volume-king/actions/runs/43843886780), head `5d72c7c4`, job `133219084105`: **961/961 PASS** (`Ran 961 tests in 109.035s`).
- [CI #1589](https://github.com/vaishnavi596/volume-king/actions/runs/43843930827), head `b9fd95b4`, job `133219231687`: **962/962 PASS** (`Ran 962 tests in 224.708s`). Confirms regression on nonfinite cache timestamps.
- [CI #1590](https://github.com/vaishnavi596/volume-king/actions/runs/43844067017), head `3f0b0356`, job `133219690419`: **962/962 PASS** (`Ran 962 tests in 93.440s`).
- [CI #1591](https://github.com/vaishnavi596/volume-king/actions/runs/43844108880), head `51f67706`, job `133219823105`: **963/963 PASS** (`Ran 963 tests in 264.624s`). Confirms malformed/unhashable filter ID fail-closed regression. Previous pending entries superseded. **Only source CI is proven**, no evidence of real 54/54 oracle five-factor data, option entitlement or device acceptance. No production changes, orders or APK.


## 2026-11-16 — UNIFIED-54 shared assessment client boundary guard
- **Verified source issue:** `src/server_feed.py::ServerDhanReadOnly.assessment` did `f.get("id") not in expected` using a set. A malformed Oracle JSON filter with an array/dict ID raises Python `TypeError: unhashable type` before the intended `FeedError` contract. This was separate from the previously corrected `src/shared_assessment_ui.py` display crash and could affect any of the 54 symbols.
- **Source fix** [e8eaf916](https://github.com/vaishnavi596/volume-king/commit/e8eaf91672095b07a63a33447e22f7f3154eb5cc) checks that every filter ID is a string before membership. This makes malformed IDs return existing `FeedError("Invalid or unsafe Dhan assessment response")` and preserves provider quota and read-only calls.
- **New regression** [35797290](https://github.com/vaishnavi596/volume-king/commit/35797290b3b9490a29f3bbc8e17e7f85a5835e50) tests the same complete safe placeholder structure and list/dict corrupt IDs across **every member of `DHAN_VERIFIED_SYMBOLS` (54 symbols)**. No network requests; `_call` mocked. **CI PENDING** at commit, not yet claimed pass.
- **Scope limitation:** this validates uniform *client acceptance/rejection*, not actual real-time 54/54 producer data; server GitHub assessment endpoint still `not_configured`, Orion runtime unverified, listed options eligibility unverified. No APK or order submission.

- **Exact follow-up CI:** #1592 [43845226696](https://github.com/vaishnavi596/volume-king/actions/runs/43845226696) source head `e8eaf916`, and #1593 [43845301953](https://github.com/vaishnavi596/volume-king/actions/runs/43845301953) test head `35797290`, both **IN PROGRESS** when recorded. Previous #1591 963/963 PASS verifies preceding UI code, NOT the newer 54-symbol feed transport fix.


## 2026-11-16 — 54-symbol client transport non-object contract
| Stage | Defect / patch | CI evidence | Live state |
|---|---|---|---|
| 3/4 · all 54 assessment symbols | Non-object JSON response could throw `AttributeError`; `5ea157c0` fails closed with `FeedError`, `986553fb` tests 54/54 symbols | New CI pending; preceding #1593 **965/965 PASS** | Oracle runtime and F&O eligibility **UNVERIFIED**, not green |
| 5/6 · release | All historical-fix/54-symbol gates still mandatory | No APK built | BLOCKED |

- **Exact current regression runs:** #1594 [43846169503](https://github.com/vaishnavi596/volume-king/actions/runs/43846169503), head `5ea157c0`, and #1595 [43846192736](https://github.com/vaishnavi596/volume-king/actions/runs/43846192736), head `986553fb`, both **IN PROGRESS** at check. Do not claim 54-symbol transport fix PASS until exact GitHub outcome and test count are available.


## 2026-11-16 — CI #1594/#1595 verified closure
- [#1594 run 43846169503](https://github.com/vaishnavi596/volume-king/actions/runs/43846169503), head `5ea157c0660a08d97a09428ad35a9d897240d052`, job `133226767740`: **965/965 PASS** (`Ran 965 tests in 122.296s`).
- [#1595 run 43846192736](https://github.com/vaishnavi596/volume-king/actions/runs/43846192736), head `986553fb738c438d8f0a9913c267ca7854fca500`, job `133226843998`: **966/966 PASS** (`Ran 966 tests in 138.269s`). These supersede the prior pending CI notes and validate fail-closed non-object assessment transport across the fixed symbol roster in offline source tests. **Oracle deployment, five live factors, 54/54 market data/PCR and Android acceptance remain unverified; no APK or orders.**


## 2026-11-16 — all-54 four-factor schema parity
| Stage | Confirmed source issue | Fix/tests | Real runtime |
|---|---|---|---|
| 3/4 · four factors across 54 configured symbols | Name-only validation accepted malformed nested factor rows | Client `bf9b0c18`, 54-symbol tests `ca9f3164`; UI `8dd1e24c`, UI test `b9a1b647` | **CODE COMMITTED; new CI PENDING; Oracle producer still unverified** |
| 5/6 · APK | Historical and current 54-symbol gate still applies | No build or deployment | BLOCKED |

- **Exact new CI submissions:** #1596 [43846822794](https://github.com/vaishnavi596/volume-king/actions/runs/43846822794), head `bf9b0c18`; #1597 [43846845799](https://github.com/vaishnavi596/volume-king/actions/runs/43846845799), head `ca9f3164`; #1598 [43846871051](https://github.com/vaishnavi596/volume-king/actions/runs/43846871051), head `8dd1e24c`; #1599 [43846903826](https://github.com/vaishnavi596/volume-king/actions/runs/43846903826), head `b9a1b647`. All were **IN PROGRESS** at initial check. Do not claim PASS until exact GitHub results/logs. No Oracle host or Android build changed.


## 2026-11-16 — UNIFIED-54 FOUR-FACTOR CI #1596–1599 completed
- [#1596](https://github.com/vaishnavi596/volume-king/actions/runs/43846822794), head `bf9b0c18`, job `133228966849`: **966/966 PASS**, 101.699 s.
- [#1597](https://github.com/vaishnavi596/volume-king/actions/runs/43846845799), head `ca9f3164`, job `133229046797`: **967/967 PASS**, 100.000 s.
- [#1598](https://github.com/vaishnavi596/volume-king/actions/runs/43846871051), head `8dd1e24c`, job `133229131491`: **967/967 PASS**, 88.654 s.
- [#1599](https://github.com/vaishnavi596/volume-king/actions/runs/43846903826), head `b9a1b647`, job `133229240962`: **968/968 PASS**, 163.784 s. Exact heads succeeded in GitHub Offline Regression Tests; previous pending entries superseded. This proves factor row schema guards in source CI, NOT live Oracle 54/54 market-data, real PCR, or APK testing. No production changes/orders.


## 2026-11-16 — 54-symbol assessment contradictory status guard
| Stage | Problem / fix | CI/source evidence | Production evidence |
|---|---|---|---|
| 3/4 · four factor + five filter contract | `not_configured` could co-exist with `available` rows. Client `e49d45b7`, UI `faa14c64` and `131b82f0` fail closed; tests `f3020d28` and `96034db7` include all 54 client symbols | Source committed; NEW CI PENDING. Prior #1599 **968/968 PASS** on older head | No Oracle data/producer/entitlement confirmed |
| 5/6 · release | 54/54 old+new regression gate remains | No Android APK | BLOCKED |

- **Exact new CI runs:** #1600 [43847594630](https://github.com/vaishnavi596/volume-king/actions/runs/43847594630) head `e49d45b7`; #1601 [43847620521](https://github.com/vaishnavi596/volume-king/actions/runs/43847620521) head `faa14c64`; #1602 [43847655090](https://github.com/vaishnavi596/volume-king/actions/runs/43847655090) head `f3020d28`; #1603 [43847688861](https://github.com/vaishnavi596/volume-king/actions/runs/43847688861) head `96034db7`; #1604 [43847718684](https://github.com/vaishnavi596/volume-king/actions/runs/43847718684) head `131b82f0`. All **IN PROGRESS** at GitHub inspection. No claim of PASS for these heads, only #1599 968/968 for preceding code. No Oracle or device proof.


## 2026-11-16 — CI #1600–1604 exact final status
- #1600 [43847594630](https://github.com/vaishnavi596/volume-king/actions/runs/43847594630) head `e49d45b7`, job `133231562512`: **968/968 PASS**, workflow success.
- #1601 [43847620521](https://github.com/vaishnavi596/volume-king/actions/runs/43847620521) head `faa14c64`, job `133231651175`: **968/968 PASS**, workflow success.
- #1602 [43847655090](https://github.com/vaishnavi596/volume-king/actions/runs/43847655090) head `f3020d28`, job `133231769996`: **969/969 PASS**, workflow success.
- #1603 [43847688861](https://github.com/vaishnavi596/volume-king/actions/runs/43847688861) head `96034db7`, job `133231890955`: **970/970 PASS**, workflow success.
- **#1604 [43847718684](https://github.com/vaishnavi596/volume-king/actions/runs/43847718684) head `131b82f0`: GitHub workflow conclusion CANCELLED**, not PASS, despite job log mentioning `Ran 970 tests in 1199.348s` and no listed assertions. Do not count this cancelled head as successful CI. Subsequent run on a new source head is required for complete CI assurance. No Oracle/phone evidence, no production orders or APK.


## 2026-11-16 — five-filter status parity over all 54
| Stage | Verified source defect | Fix / tests | Remaining |
|---|---|---|---|
| 3/4 · shared five-filter UI | Filter IDs checked, status enum unchecked; malformed statuses could bypass full-schema rejection | `cd83be9d` + all 54 regression `74c965be`; CI PENDING | Actual Oracle 54/54 producer and equity PCR unverified |
| 5/6 · pre-APK | #1604 was **CANCELLED**, #1603 970/970 PASS for earlier source | New head CI required | No APK created |

- **Exact CI:** #1605 [43858265540](https://github.com/vaishnavi596/volume-king/actions/runs/43858265540), source head `cd83be9d`, and #1606 [43858299127](https://github.com/vaishnavi596/volume-king/actions/runs/43858299127), regression head `74c965be`, both **IN PROGRESS** when inspected. Do not describe as PASS until complete. #1604 remains cancelled even though its log contained a test-count line.


## 2026-11-16 — WATCHLIST-70-UNIQUE-01
| Requirement | GitHub source status | Repair and evidence | Remaining |
|---|---|---|---|
| Five lists, 70 TOTAL distinct NSE cash equities | **Implemented** by `MAX_WATCHLIST_EQUITIES=70`; default 51 equities, 3 independent index symbols | Source audit, not mobile proof | Confirm actual add / remove / restart on phone |
| HDFCBANK cannot be in both List 1 and List 2 | Add-time guards already present; **legacy saved-list gap fixed** | `fb6e18a2` shared normalization + `db1b7387` startup integration + `0725074a` six tests, CI PENDING | Validate old settings migration on phone |
| 70 user-selected Dhan symbols | Dhan Registry identity check and selected batch quotes for nonfixed symbols are in source | Quotes availability unverified on real Oracle | Dhan registry entitlement & 70/70 selected quote coverage OPEN |
| Scanner & 5 filters for all user-selected symbols | **NOT 70/70 yet**: Dhan scanner still restricts `DHAN_VERIFIED_SYMBOLS` fixed 54; real assessment producer `not_configured` | Do not claim done | Oracle dynamic historical input + eligibility design/audit required |
| APK release | 54 fixed roster regression and extended 70-slot ownership rules both required | Source CI upcoming | No APK until Oracle and on-device acceptance |

- **Watchlist-70 CI progress:** #1607 [43859347559](https://github.com/vaishnavi596/volume-king/actions/runs/43859347559) source head `fb6e18a2`: **971/971 PASS** (`Ran 971 tests in 108.421s`); #1608 [43859392970](https://github.com/vaishnavi596/volume-king/actions/runs/43859392970) app wiring head `db1b7387`: **971/971 PASS** (`Ran 971 tests in 102.960s`); #1609 [43859454137](https://github.com/vaishnavi596/volume-king/actions/runs/43859454137) test head `0725074a`: **IN PROGRESS** when checked. This is offline source evidence; no device test of add/watchlist persistence yet.

- **Watchlist-70 CI #1609 FINAL:** [run 43859454137](https://github.com/vaishnavi596/volume-king/actions/runs/43859454137), test head `0725074a`, **977/977 PASS** (`Ran 977 tests in 104.897s`; GitHub Actions completed success). Six added tests validate exactly 70 unique across five lists, 71st refused, no duplicate HDFCBANK across lists, malformed legacy prefs normalization, idempotence, and app integration. Earlier #1607/#1608 both 971/971 PASS. **No Android UI or Oracle Registry validation performed**; new source code requires future APK deployment. Extra symbols beyond fixed 54 still not proven supported for history/Scanner and are a release gate, not treated as PASS.


## 2026-11-16 — Selected dynamic 70-quote response boundary
| Stage | Verified source issue | Fix/test | Live coverage |
|---|---|---|---|
| 1/2 · up to 70 saved equity quote requests | Invalid unhashable input or malformed server JSON could raise uncontrolled exceptions | `effccb14` safety patch + `eb63d488` three tests; CI pending | Oracle dynamic registry/selected quotes not yet production verified |
| 3/4 · scanner and historical filters for extra equities | Current Dhan historical/scanner allowlist still fixed 54 | Not changed; separate backend mapping proof required | OPEN |
| 5/6 · release | All saved-list and dynamic equity paths must pass | No new APK | BLOCKED |


- **WATCHLIST-70 REGISTRY-03 source finding:** `ServerDhanReadOnly.verified_equity_symbol` called `.get` on an unvalidated Oracle registry JSON response; a scalar/list/null response could escape as AttributeError rather than controlled `FeedError`, interrupting 70-slot dynamic add flow. **Patch** [61f282db](https://github.com/vaishnavi596/volume-king/commit/61f282db867fe42c5fec13c13a9dea898aaa3ddb) rejects non-dictionary registry response; **test** [5101b562](https://github.com/vaishnavi596/volume-king/commit/5101b562872441bb6e0f5a192ab8f42c6d71dbce) verifies null/array/string/integer fail closed and an exact matching symbol succeeds once via mocked call. New CI pending. No production Oracle or mobile test, orders, Dhan API requests or APK build.

- **Exact follow-up CI submissions:** #1610 [43860483970](https://github.com/vaishnavi596/volume-king/actions/runs/43860483970) head `effccb14`, #1611 [43860534856](https://github.com/vaishnavi596/volume-king/actions/runs/43860534856) head `eb63d488`, #1612 [43860658781](https://github.com/vaishnavi596/volume-king/actions/runs/43860658781) head `61f282db`, #1613 [43860690538](https://github.com/vaishnavi596/volume-king/actions/runs/43860690538) head `5101b562` all **IN PROGRESS** at inspection. No PASS claimed. Previous #1609 **977/977 PASS** applies to earlier saved-list normalization only.


## 2026-11-16 — TWO-MOBILE SERVER REQUEST COALESCING
| Path | Two mobile upstream Dhan behavior | GitHub repair/status | Oracle / phones |
|---|---|---|---|
| `/v2/snapshot` 51 verified equities | Server ingester cache read, no Dhan call for fresh reads | Existing source; still verify collector freshness & first-boot recovery | NOT TESTED |
| `/dhan/index-ltp-batch` 3 indices | Previously two identical Dhan requests | `46cc4e2d` and `1672629f` single shared 60s lane; test `7055db1b`, CI PENDING | NOT DEPLOYED |
| `/dhan/selected-ltp-batch` up to 70 selected equities | Previously two same-set Dhan requests | Shared keyed 60s lane, 30s shared 429 cooldown, token isolation; CI PENDING | NOT DEPLOYED |
| `/dhan/intraday` historical candles | 180s validated response cache but concurrent miss risk | OPEN: add single-flight server fetch / do not fabricate timestamps | NOT TESTED |
| `/dhan/ltp-batch` bootstrap | Existing snapshot cache, direct bootstrap still callable from each phone when stale | OPEN: shared server recovery coordination | NOT TESTED |
| All | Respect Dhan 429, 70 max, Dhan-only, no live orders | No extra 54/70 provider fanout | APK BLOCKED |


## 2026-11-16 — Follow-up CI exact status for dynamic 70 and dual-mobile lane
- Previously pending [#1610](https://github.com/vaishnavi596/volume-king/actions/runs/43860483970) head `effccb14`, job `133275695507`: **977/977 PASS** (`Ran 977 tests in 97.771s`). [#1611](https://github.com/vaishnavi596/volume-king/actions/runs/43860534856) head `eb63d488`, job `133275861390`: **980/980 PASS** (`Ran 980 tests in 273.337s`). [#1612](https://github.com/vaishnavi596/volume-king/actions/runs/43860658781) head `61f282db`, job `133276289172`: **980/980 PASS** (`Ran 980 tests in 290.518s`). #1613 was **IN PROGRESS** at inspection, not counted as success.
- New dual-mobile shared quote tests were submitted: [#1614](https://github.com/vaishnavi596/volume-king/actions/runs/43862190170) head `46cc4e2d`; [#1615](https://github.com/vaishnavi596/volume-king/actions/runs/43862263412) head `1672629f`; [#1616](https://github.com/vaishnavi596/volume-king/actions/runs/43862328810) head `7055db1b`. All were **IN PROGRESS** at first check; do not say PASS yet. Their success, if any, would be offline CI, not Oracle deployment or real two-device proof.


## 2026-11-16 — Four-pipeline cadence for 2 phones, 51→70 equities
| Lane | Mobile request floor | Server cadence/cache | 70-equity readiness |
|---|---|---|---|
| 3 index LTP | 60s / 10s poll check | New 60s shared source response cache; not deployed | Independent of cash cap |
| 51 fixed equity quotes | 60s / 10s poll check | Optional ingestion default 90s (OFF by default); snapshot age limit 120s; new 60s bootstrap single-flight `75229c9a` | Future selected up to 19 extra equity quotes |
| Selected dynamic equities | Bundled with equity watchlist fetch | New 60s shared keyed batch, 30s shared 429 cooldown, source CI #1616 988/988 PASS | Registry/70-quote support source-only; Oracle not tested |
| Candles / assessment | Index historical 180s; assessment 180s; Options selected 60s | Historical cache 180s, single-flight on miss OPEN; real filter producer not configured | 70 dynamic historical/options not proven |
| Manual / UI | 30s manual retry; Watchlist paint ~2s | UI paint not equivalent to provider request | 70 watchlist ownership Source CI #1609 977/977 PASS |

- **Exact CI verification for two-device pipeline:** #1614 [43862190170](https://github.com/vaishnavi596/volume-king/actions/runs/43862190170), job `133281548897`: **981/981 PASS**; #1616 [43862328810](https://github.com/vaishnavi596/volume-king/actions/runs/43862328810), job `133282035342`: **988/988 PASS**; #1618 [43863041839](https://github.com/vaishnavi596/volume-king/actions/runs/43863041839), head `b4ed0be0`, job `133284462041`: **990/990 PASS** (`Ran 990 tests in 87.448s`) for 51-equity bootstrap single-flight integration source. #1615 and #1617 were IN PROGRESS at this follow-up and are not counted PASS. This remains GitHub offline CI, not deployed Oracle or phone evidence.


## 2026-11-16 — MASTER-24 POINT-WISE SIX-BATCH CHECKLIST

This is the persistent, numbered owner-facing checklist for the work still being completed. **All six batches remain release-open**; SOURCE DONE is not Oracle/phone PASS. Review last 5–10 relevant branch commits and CI before code changes. Single mobile only, dual mobile deferred, Dhan market-data read-only, no live orders, **one APK last**.

| No. | Batch | Checkpoint | Status at recorded inspection | Remaining acceptance |
|---|---|---|---|---|
| 01 | B1 Oracle/Indices | Read-only server audit scripts | SOURCE DONE; prior mocked CI PASS | Actual Oracle deployed route/collector audit |
| 02 | B1 Oracle/Indices | Index cached-vote fallback | SOURCE DONE 050cc5ad; test 1ea0d0cc | Exact CI and phone red/green acceptance |
| 03 | B1 Oracle/Indices | Newest CI failure closeout | OPEN; no verified new-run result | Inspect exact branch run/job and repair failures |
| 04 | B1 Oracle/Indices | Dhan three-index price and candle parity | OPEN | Actual Oracle data, history and cooldown |
| 05 | B2 Timeframes | Timeframe source audit | AUDIT DONE | Separate 1m/3m/selected/5m data paths |
| 06 | B2 Timeframes | Completed 3m OHLC source helper | SOURCE DONE ae60db3d; test source 92082b45 | Exact CI and Dhan 1m input integration |
| 07 | B2 Timeframes | Watchlist 3m red/green | OPEN | True 3m votes/cache, preserve history on error |
| 08 | B2 Timeframes | Dashboard 1m, Scanner selection, Super Five 5m | PARTIAL | Independent timeframe source and QA |
| 09 | B3 Smart Controller | Four-lane budget policy | DESIGN DONE | Validate Dhan endpoint quotas |
| 10 | B3 Smart Controller | Active-symbol planner | SOURCE DONE 211cee48; test 62c09227 | Exact CI and integration |
| 11 | B3 Smart Controller | Dynamic symbol subscriptions | OPEN | Unused symbols stop consuming avoidable workload |
| 12 | B3 Smart Controller | Latency/429/bandwidth measurements | OPEN | Compare 54 vs 34, rate limits and cache freshness |
| 13 | B4 Five Filters | Five-filter schema and WAIT safety | SOURCE DONE; historic offline CI reports PASS | Real Oracle producer evidence |
| 14 | B4 Five Filters | OI support/resistance and Max Pain | OPEN | Mapped strike/expiry/OI calculations and entitlement |
| 15 | B4 Five Filters | PCR and per-symbol option chain | OPEN | Actual NSE/BSE equity and index eligibility/values |
| 16 | B4 Five Filters | Four independent News/Futures/Options/Candle scores | OPEN | Independent data sources; avoid fake percentages |
| 17 | B5 Resilience | Five watchlists and 70 unique save policy | SOURCE DONE; CI #1609 977/977 PASS | Phone add/restart and dynamic symbol tests |
| 18 | B5 Resilience | Scanner/Super Five shared candles | PARTIAL | White chart, flicker, signal consistency mobile tests |
| 19 | B5 Resilience | Session and last-good display | PARTIAL | Holiday calendar, first refresh, background/resume |
| 20 | B5 Resilience | Health/Error Doctor recovery | PARTIAL | Active vs recovered issues; HTTP 429 and freshness |
| 21 | B6 Release | Full regression on release HEAD | OPEN | Resolve exact branch failures and full CI |
| 22 | B6 Release | Guarded Oracle parity and backup-first deployment | OPEN | Proof of deployed source, health and rollback |
| 23 | B6 Release | VersionName+versionCode+signed APK | OPEN; previous v2.3.130 diagnostic signed | One final release after earlier gates |
| 24 | B6 Release | Single mobile end-to-end acceptance | OPEN | Dashboard/Watchlist/Scanner/Super Five/Options pass |

**Totals:** 24 checkpoints in six grouped batches. 7 checkpoints have a documented completed source/design/audit component (items 01, 02, 05, 06, 09, 10, 13, 17 actually eight), plus further PARTIAL components. This is NOT an official percentage of product completion; no count represents Android runtime proof. Existing source CI run numbers should be preserved separately from upcoming exact-HEAD CI.

**Current next gate:** confirm real current branch CI fail/success without guessing from empty legacy-status responses, then integrate Watchlist true 3m data path and Dashboard true 1m, while preserving Scanner's chosen timeframe and Super Five 5m. Journal after each commit/test. No production edit or APK created by this checklist.


## 2026-11-16 — Numbered checkpoint 06 follow-up: duplicate-minute safeguard
- **Checkpoint 06 B2** completed 3m candle derivation helper has additional source safety [2fc66d70](https://github.com/vaishnavi596/volume-king/commit/2fc66d70d1adab2eda14c21049721a16476af785): reject 3m bucket when any valid 1m source timestamp is duplicated, preventing ambiguous OHLC/volume and votes. Regression [04ec7acd](https://github.com/vaishnavi596/volume-king/commit/04ec7acdb8222ff44a9adc5a7bad4213d9a4baa6) added; exact Actions CI **UNVERIFIED**. Source-level correction only; Android 3m live UI/integration **OPEN**. No Oracle edit, Dhan query or APK. Corresponding journal checkpoint: B2 duplicate-minute data-quality fix.


## 2026-11-16 — B2 checkpoint 08: Dhan-selected Scanner 3m source integration
- Existing Dhan history code accepted 1m/5m/15m/1h, while `3m` was unsupported in the Scanner dropdown. [ecd8cfe6](https://github.com/vaishnavi596/volume-king/commit/ecd8cfe657aab67b3b4fbe37942dda93af043ad1) safely enables 3m Scanner calls by fetching actual Dhan 1m history and using the previously committed completed-3m helper. [879bcfb4](https://github.com/vaishnavi596/volume-king/commit/879bcfb475ee638f38658a6faee0d002b9a52ff8) adds two code-path regression tests. **SOURCE IMPLEMENTED / exact-head CI UNVERIFIED / Oracle+phone NOT TESTED**.
- **Scope boundary:** this does NOT yet mean Watchlist's auto Bullish/Bearish shows true 3m; its source remains existing 5m `watch_signal_cache`. Dashboard index cards still use 5m and require real 1m feed. Super Five 5m preserved. Continue B2 without declaring checkpoints 07 or 08 release-PASS.


## 2026-11-16 — Checkpoints 05/07/08: strict 1m/3m/5m cache separation
- **Code** [390f7d62](https://github.com/vaishnavi596/volume-king/commit/390f7d62ea8cc717b6015bd9cc1436c97c5e1488): canonical `shared_history(sym,tf="5m")` accepts exact timeframe, source and Scanner generation; unlabeled 5m quote bars never enter 1m/3m. Default 5m callers preserved.
- **Test source** [97f76fc3](https://github.com/vaishnavi596/volume-king/commit/97f76fc359937a604056f9c8145ce0842f89e36e): 5 isolated execution cases, no network; **CI not verified**, Oracle and mobile not run.
- **Remaining:** Dashboard 1m and Watchlist 3m now have a safer shared selection primitive, but real Dhan 1m history collection, pacing, per-timeframe vote cache and rendering remain OPEN. No extra Dhan fanout, no APK, no live orders.


## 2026-11-16 — Numbered B2 checkpoint 07: Watchlist 3m display (cached-only milestone)
- **Source commit** [21ec40a1](https://github.com/vaishnavi596/volume-king/commit/21ec40a107753f4c6fa02438446b89fe06ebf2fd) adds a true completed-3m Dhan candle vote selector for Watchlist rows, filter membership, and mounted 2s observation. Previous 5m `watch_signal_cache` remains solely Super Five/common ranking; it must NOT be relabeled Watchlist 3m. Missing 3m input produces **3m WAIT**. No new upstream Dhan request from rendering.
- **Test source** [3f552681](https://github.com/vaishnavi596/volume-king/commit/3f55268197c8f04a6e2a9bbf0ab1f1e8d4f640d5) adds five AST contract tests, exact CI result **UNKNOWN** (not PASS). **Oracle/phone NOT TESTED**.
- **Checkpoint 07 status: PARTIAL** — UI now reads real cached 3m source *when present*, but the 51-equity automatic 1m→3m collection is **NOT IMPLEMENTED**, and currently most rows can remain WAIT. Do not declare the full Watchlist 3m feature done; next priority quota-safe server shared collection and Dashboard 1m ingestion after actual CI/Oracle audit.


## 2026-11-16 — B2 checkpoints 05/08 Dashboard 1m index/analysis: source corrected, acceptance OPEN
- **Code** [2e4acdcf](https://github.com/vaishnavi596/volume-king/commit/2e4acdcf8d208df9c7ccc7c97e29200da11ef7bd): three Dashboard index cards and three selectable slots now use exact Dhan **1m** historical votes rather than 5m source or fallback. Indexed poller changed its *existing 180s three-index history requests* to 1m: not an added 3-call fanout, but higher 1m payload remains unmeasured. Historical only; missing input WAIT. Super Five independently 5m, Scanner chosen interval, Watchlist strict 3m display remain scoped.
- **Regression source** [5470e34a](https://github.com/vaishnavi596/volume-king/commit/5470e34a0794b45ba498790a41f68b82eaa0842b) revised obsolete Dashboard 5m fallback guards to six updated 1m contracts. **Exact-head CI UNKNOWN**, Oracle market data/429 NOT RUN, phone NOT RUN. No complete B2 or release PASS.
- **B2 remaining:** quota-safe real shared 1m history for three selectable equity slots and active 3m Watchlist equities, actual Dhan source time/bytes/429 validation, CI and Android QA; no APK until last gate.


## 2026-11-16 — B2 checkpoint 05/08: index failure reporting fix
- **Source fix** [b1bff4b8](https://github.com/vaishnavi596/volume-king/commit/b1bff4b88c9c563e4fb76300bf965c041568f503): independent Dashboard Dhan 1m history poll errors now carry the correct **1m** timeframe, not legacy 5m; **test added** [50e0ae6d](https://github.com/vaishnavi596/volume-king/commit/50e0ae6d38f8661b36d93af72d2a5fe7cc2abdb4). GitHub Actions CI **UNVERIFIED**; Oracle and mobile **NOT RUN**.
- Proposed bounded reuse of already-cached 1m candles for Watchlist 3m was interrupted before a commit: **NOT DONE**. Remain B2 PARTIAL. No APK.


## 2026-11-16 — Four coordinated lanes; B2 checkpoint 07 active cached history reuse

| Work lane | Original numbered batches | Completed source component | Remaining proof/repair |
|---|---|---|---|
| **A** | **B1 + B2** | 1m/3m/5m cache selectors, Dashboard 1m index historical votes, Scanner-selected 3m, cached-only Watchlist 3m; cached Dhan 1m→3m local reuse [46d6491c](https://github.com/vaishnavi596/volume-king/commit/46d6491cf736f68b250fea2e223c7368384a7716), regression source [60100644](https://github.com/vaishnavi596/volume-king/commit/60100644982ba7e8a18948164c33ec88ab04d57b) | CI actual PASS; quota-safe upstream active-equity 1m acquisition, real Oracle 1m/3m provenance, 429/bytes/mobile |
| **B** | **B3** | `active_symbol_budget.py` pure planner + offline test code | Actual subscribed worklist, Dhan call-count reduction, 70 dynamic symbols, quota limits |
| **C** | **B4** | Five filter labels/source-agnostic WAIT validation and separate 4-factor UI contracts | Real Dhan OI/expiry/PCR/max pain and independent factor input/score definition; actual Oracle/phone evidence |
| **D** | **B5 + B6** | Earlier UI/candle/cache fixes, error/release policy, previous signed diagnostic APK | Exact-head CI/phone regressions, Oracle backed-up parity/release gate; one new signed version only at end |

- **Checkpoint 07 stays PARTIAL**: from already-cached authentic Dhan 1m candles, Watchlist can now derive completed 3m locally without new calls; automatically fetching all active 51-equity 1m histories is **not yet in place**. Do not interpret Group A SOURCE patch as 3m full mobile PASS.
- **New regressions 3 written, NOT VERIFIED passing**. The search connector for old PR runs cannot establish new push CI; browser fetching GitHub Actions failed. Oracle NOT DEPLOYED, mobile NOT TESTED, new APK NOT BUILT.
- **Conflict rule:** Groups can progress independently only for non-overlapping files. Changes to `src/main.py` and common data budget are staged sequentially behind pre-edit last-ten review and exact-head test gate. Source evidence vs deployed/live proof remain separate.


## 2026-11-16 — Master-24 checkpoint 11/12 Group B controller pacing
- **Source module** [819136c5](https://github.com/vaishnavi596/volume-king/commit/819136c511d27c337630034c471f4eb3e1ff0064) adds pure cooldown-aware history worklist selection, hard cap **3 symbols per planned cycle**, default 180s minimum repeat interval. **Tests source** [e4cc7d93](https://github.com/vaishnavi596/volume-king/commit/e4cc7d938b31fe330bff2fcd7765defe80fee38a) adds four offline cases; **CI result UNKNOWN**. **NOT CONNECTED** to actual Dhan/Oracle polling and does not establish 51→3 network reduction or improved freshness. B3 still **PARTIAL**. Parallel group A's cached 1m→3m reuse remained unchanged; B4 real filter producer and B5/B6 final gates remain OPEN.


## 2026-11-16 — Numbered checklist source increments (B2 #07, B3 #11/#12)
| Checkpoint | New evidence | Status and remaining |
|---|---|---|
| **07 (Group A/B2 Watchlist true 3m)** | Last-row 1m OHLCV correction now invalidates cached derived 3m: [1571c691](https://github.com/vaishnavi596/volume-king/commit/1571c6915db9543d5dd4ebc83b37101fc85d2448); regression [25b5b3de](https://github.com/vaishnavi596/volume-king/commit/25b5b3de61fb2d57918c3e4af0b4bf0a2f681070) | **SOURCE PARTIAL / CI UNVERIFIED / ORACLE NOT TESTED / PHONE NOT TESTED**. Most 51 equity 1m histories still need rate-safe collection. |
| **11/12 (Group B/B3 workload + quota)** | Optional verified Dhan mapped-symbol allowlist added to existing bounded pure planner: [3cea96ac](https://github.com/vaishnavi596/volume-king/commit/3cea96acc32469c4158c7bf67928c431f3a04147); 2 regression tests [a2275c3c](https://github.com/vaishnavi596/volume-king/commit/a2275c3c8a913bcf8ab4763f0aeebb10b111e6d9) | **SOURCE PARTIAL / CI UNVERIFIED**. Planner not connected to actual Dhan history scheduler; 429/bytes not measured. |
- **Overall six batches still release-OPEN**. Existing four coordinated groups A/B/C/D unchanged; B4 genuine five filters remain blocking. No APK or Oracle production deployment.


## 2026-11-16 — CHECKPOINTS 21 & 07/08: CI FAIL triage after owner provided #1619–#1640
- **Confirmed actual Actions job logs:** #1619 990 tests/2 FAIL (old 5m structural guard); #1641 1028 tests/16 FAIL+2 ERROR (old 5m Dashboard/Watchlist contracts + two missing test-fixture dependencies); #1654 Python syntax compilation failure caused by test update's nested quotation, suite not run. This is **NOT ALL PASS** and does not validate Oracle/phone.
- **Corrective test commits:** `b6b13456`, `f9cf5548`, `70c4b633`, `b2c17f35`, `4662540b`, `0bbdb52a`, `d0326982`, `89eb8716`, `c8574e6c`, `d6439bbd`, `69586b92`, `439d69c2`, `f2448f97`, `1e86b7cb`, with test quote fix `5a364abc` + `f25270bf`. Journal commit `44e427fd`.
- **Current gate:** exact-HEAD run #1660 was in progress on inspection; verify new run and any fresh failures, do not close B5/B6. B2 source 1m/3m semantics remain and no fallback to fake 5m percentages should be restored to make old tests pass. No production deployment, signed APK, or phone acceptance.


## 2026-11-16 — Checkpoint 21: exact tested source commit CI PASS (NOT release PASS)
- **Verified GitHub Actions** [#1660](https://github.com/vaishnavi596/volume-king/actions/runs/43881867611), commit `f25270bf47d9c550491374c0d0cbbcd43dc8af0d`, offline-tests job 133349553938: **SUCCESS**; Python syntax PASS; **1031 tests run, OK (317.339s)**. Former #1619–#1659 failures are superseded **for this particular tested commit**.
- **Not verified:** future code changes, Dhan rate/bytes and freshness, Oracle production, 1m/3m equity completeness, phone, or new signed APK. Do not set overall B1–B6 to PASS. Continue the agreed slower edit/test/commit sequence and record each subsequent exact commit's CI independently.


## 2026-11-16 — B3 checkpoint 11/12 global request gap (small controlled patch)
- **Last verified CI baseline:** [#1660](https://github.com/vaishnavi596/volume-king/actions/runs/43881867611), commit `f25270bf`, 1031 offline tests **PASS**; not a proof of subsequent edits.
- **Group B source** [95e17af0](https://github.com/vaishnavi596/volume-king/commit/95e17af040a3eddd42cb39f1449d1ed009d30f06): pure planner now accepts previous *global* broker attempt and enforces at least 1-second spacing, 1.5-second default between separate due batches, in addition to per-symbol 180s and max-batch 3. **Test source** [73580eae](https://github.com/vaishnavi596/volume-king/commit/73580eae1b37666a394738a218f2dd738dacb6e8): 2 cases added. CI #1661/#1662 initially in progress; exact source CI **NOT YET VERIFIED**.
- **B3 still PARTIAL:** planner isn't connected to live Dhan/Oracle coordinator; no measured 429/request/byte savings. B1/B2, B4, B5/B6 device and release gates remain OPEN. No APK or production change.


## 2026-11-16 — B3 #11/#12 exact source CI confirmed
- **CI:** [#1662](https://github.com/vaishnavi596/volume-king/actions/runs/43883383158), exact test commit `73580eae`, job 133354923053: **1033 tests, 0 FAIL, 0 ERROR, SUCCESS**; source implementation `95e17af0` also confirmed by #1661.
- **B3 status: SOURCE + OFFLINE TEST PASS; SERVER/PROVIDER/DEVICE NOT TESTED.** The capped cooldown-aware planner is still not connected to the real Dhan history queue, so its global 1.5s guard cannot be claimed to govern actual traffic. B1/B2 data quality and B4 genuine filter evidence remain open. Do not create APK or call all six batches PASS.
