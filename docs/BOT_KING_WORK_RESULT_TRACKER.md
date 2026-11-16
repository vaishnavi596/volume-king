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
