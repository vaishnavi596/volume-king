# BOT KING V3 — Building Capacity Phone Test Journal
Date: 2026-11-21 IST
Branch: `pilot/v1-pure-original-clone-phone-20261120`

## User-approved sequence
1. Measure original V3 Building first on actual Android using complete pre-supplied fake data (no Dhan calls).
2. Review Help Doctor/error timings and queue integrity.
3. Fix B1 building/cache/display bottlenecks before B2 timeframe and B3 UI delta work.

## Grounded baseline
GitHub offline benchmark #44870140640 SUCCESS: 73 instruments (70 equities + 3 indices) Python fixture validate/technical/queue/mock process 175.801ms; 512 of 730 abstract queue keys accepted, 218 rejected. This is NOT a Flutter/mobile render benchmark. Existing prototype SmartApplyQueue is not wired into production V3.

## Changes
- Commit `9cd5fd6`: new standalone `diagnostics/v3_building_phone_capacity.py`. Separate offline Flet app: 10/35/54/73 instruments, 180 synthetic 1m candles per instrument, derived 3m/5m sample bars, five filter slots WAIT (not real option scores), current SmartApplyQueue max_pending 512 to expose rejection. Android device measures synthetic generation, stock validation, compute, queue, Flet control construction, update submission and manual on-screen visibility acknowledgment. Raw report selectable in-app. NO network, Dhan or Oracle access. No modifications to production src/main.py.
- Commit `f5eefce`: separate workflow `.github/workflows/v3-building-phone-capacity-apk.yml` substitutes diagnostic as src/main.py ONLY in isolated ephemeral GitHub build workspace, different package `com.botking.v3capacity.bot_king_v3_capacity_lab`, ephemeral signing, uploads test APK. Current branch actual runtime app files remain unchanged.
- Workflow started automatically by creation: GitHub Actions #44870760545; initial status in_progress; final success or APK download must be verified separately.

## Limits and acceptance
This is an isolated Building/queue/UI capacity diagnostic, not full production V3 tree or genuine exchange filters. On-device measured call to page.update() submits updates but is not equivalent to Flutter raster completion. Manual acknowledgment includes user response latency. No time claim until phone report. First reproduce baseline bottleneck; then propose one combined B1 fix and repeat comparable phone test. Keep timeframes unchanged until B1 acceptance.


## 2026-11-21 IST — Real Android phone screenshots: both 54 and 73 instrument tests
Owner supplied four phone screenshots from installed separate Capacity Lab APK. Values below are directly transcribed; no extra Android profiler was run.

| Observed metric | 54 instruments (51 equity+3 indices) | 73 instruments (70 equity+3 indices) |
|---|---:|---:|
| generate_ms | 120.269 | 70.397 |
| validate_stock_ms | 4.651 | 5.236 |
| synthetic_compute_ms | 0.062 | 0.106 |
| queue_ms | 3.351 | 5.002 |
| total_python_ms | 128.334 | 80.740 |
| thread_wall_ms | 129.151 | 84.303 |
| flet_controls_construct_ms | 7.800 | 12.741 |
| queued/applied | 512/512 | 512/512 |
| capacity_rejected | 28/540 | 218/730 |
| failed | 0 | 0 |
| flet_submit_until_ack_ms | 875.278 | 1299.306 |
| test_start_until_ack_ms | 1020.428 | 1409.014 |

### Assessment
Both screenshot reports display an ACK. Their 1.020428s and 1.409014s intervals end at a **manual tap**, so the times include human interaction/reaction and must NOT be labeled exact Flutter raster/paint. The very small synthetic_compute_ms is dummy price-direction calculation, NOT real five-filter/technical scanner computation. The isolated apply queue rejected 28 and 218 updates because its current max_pending=512, even though Flet rows are independently created for all 54 or 73 stock records. Thus this is a **test queue failure, not proven production missing UI rows**. No live feed or server involved. Different generation_ms with larger sample is expected from one-shot timing variability; no p95 inferred.

### Next action
B1 first: preserve full authoritative per-symbol/per-timeframe candle stock independent of UI hint queue; stage backlog/backpressure or drain batches without losing completed candles; test exact 540/730 key acceptance/application, revisions, completion, error retry, and 1–4 device offline runs before production integration. B2 timeframe implementation deferred. Do not claim V3 Building capacity is 1.409s as a full production UI benchmark.


## 2026-11-21 IST — B1 bounded-burst source repair (isolated prototype, not production integration)
After owner Android screenshots (54: 28 rejected; 73: 218 rejected), inspected exact latest files `src/clone_day2_apply_queue.py`, `diagnostics/v3_building_phone_capacity.py`, and this journal, without rechecking 10 earlier commits. Confirmed `SmartApplyQueue` is an isolated helper not imported by production `src/main.py`.

**B1 patch:** `src/clone_day2_apply_queue.py` gained `ingest_burst(updates, apply, batch_size=128)` that drains before hitting 512 slots and refuses to proceed if callbacks cannot make progress, instead of silently losing newly received keys. This is a bounded in-memory batch-passing policy for a finite list; NOT a persistent stock/cache and NOT yet a frame-budget UI scheduler. The original `receive` cap and exception/health behavior remain unchanged. Diagnostic source now sends its 10 updates per instrument through the new method. Exact target is 540/540 and 730/730, 0 capacity rejected; no assertion of PASS until CI completes.

**GitHub changes:** `65a545df` queue prototype; `c4531c8b` diagnostic B1 queue plumbing; `cfa5561e` test for 10/35/54/73 instruments, 1m/3m/5m key separation, callback failure backpressure and invalid candle timeframe; `d2bfe81e` standalone .github/workflows/v3-b1-bounded-queue-gate.yml CI. Workflow status and outcome to verify from GitHub run. No Android APK built in this step; phone has baseline APK which still shows the old queue behavior. Production app, Oracle, broker and B2 timeframe unchanged.


## 2026-11-21 IST — B1 second Android capacity APK: owner-phone PASS, isolated synthetic scope

Owner uploaded four new screenshots from Android B1 bounded-queue Capacity Lab after build2 workflow `#44872027777` (do not infer exact Flutter raster/paint).

| Metric | 54 instruments (51 equities+3 indices) | 73 instruments (70 equities+3 indices) |
|---|---:|---:|
| generate_ms | 47.227 | 52.248 |
| validate_stock_ms | 3.694 | 5.646 |
| synthetic_compute_ms | 0.068 | 0.108 |
| queue_ms | 3.763 | 4.821 |
| total_python_ms | 54.753 | 62.824 |
| thread_wall_ms | 56.608 | 64.132 |
| flet_controls_construct_ms | 7.934 | 11.164 |
| received/queued/applied | 540/540/540 | 730/730/730 |
| capacity_rejected | 0 | 0 |
| failed | 0 | 0 |
| flet_submit_until_ack_ms | 2054.926 | 911.652 |
| test_start_until_ack_ms | 2128.349 | 998.177 |

**Comparison:** Prior phone baseline had 28/540 and 218/730 capacity rejects respectively; after bounded-burst drain both cases show zero rejected and zero apply failures. PASS limited to finite synthetic burst processing in isolated queue prototype and simplistic Flet rows. These screenshots do not certify complete V3 production data/cache integration, five live filter computation, Android raster timing, actual last-row visibility, real options evidence, or production latency. ACK includes human reaction and varies across trials; single-run 2.128s vs 0.998s does NOT establish relative device performance. The displayed filter slots remain WAIT (sixth absent).

**Next B1 checks:** Keep Dhan/Oracle and timeframe work untouched. Verify authoritative stock/last-good retention, candle completion/revision behavior, actual scanner/five-filter calculations, connection to production Flet screens, and real Android frame-stage timings; use controlled combined offline tests before any production app edit/next APK. No new test APK or server change initiated by this journal entry.


## 2026-11-21 IST — Owner B1 first-fill and adaptive hardware/network policy (mandatory before implementation)
Owner clarified that first-login cached data readiness MUST be distinguished from arrival time and device processing. Network can deliver the same required data in about 1 second or a minute or longer. Initial required dataset must be fully verified and stocked before claiming FULL_CACHE_READY; progress must continue without rigid 1/3/5-second assumptions. Do not block the interface entirely: show truthful stage-by-stage progress and keep prior valid cached observations visibly HIST/unverified where applicable; fail closed when required evidence is missing, rather than claiming live/complete. After initial cache, allow continuous incoming changes, but mutate only affected values/visible widgets/chart series rather than rebuilding or resetting full pages. Retain scroll and screen state.

Device-aware bounded UI application: measure CPU/RAM pressure and observed queue/render frame budget where Android APIs permit; adapt batch size and scheduling instead of trying to infer device class from brand or network throughput. Test slower, current and faster devices where available; 4-phone concurrency remains a planned separate acceptance. Break down timings as T0 network/buffer arrival, T1 complete+validated stock, T2 calculations (technical indicators, genuine five filter prerequisites, bullish/bearish candles), T3 staged UI submission, T4 displayed/interactable confirmation. T4 currently has only manual ACK, not exact raster. Track cold/warm starts, sustained subsequent delta updates, missing or partial candle, slow/mobile network, zero cross-timeframe/expiry leakage and zero lost completed candles. Required readiness may be defined per-symbol/timeframe and aggregate for the selected watchlist; do NOT promise whole 70-share live feed in a specific wall-clock time.

Read-only source audit of exact current branch files:
- `src/main.py::refresh_mounted_data_sections` at ~6181 still reconstructs all six dashboard and three scanner section hosts on each refresh via factory()+host.update(); a full delta/widget signature strategy is not yet established for those screens.
- `watch_visible_tick` at ~2272 uses fixed 2-second polling while mounted and computes signal signatures across visible symbols; some child controls already retain identity and avoid rebuilding on quote-only changes.
- `shared_history` at ~4946 maintains timeframe isolated/generation selected histories, with local completed 3m derivation from valid 1m data.
- `get_market_data` at ~575 has a 90-second Dhan recent-cache TTL; this is not itself a full first-login cache-ready barrier or device adaptive scheduler.
- `snapshot_store.py` persists validated market snapshots with a 24 MB cap and fallback on corrupted stored data; `candle_retention.py` retains prior valid candles when refresh is partial and ensures retained history isn't misclassified as live.
- `scanner_engine.py::analyze` has technical indicators plus option filters WAIT without verified Dhan evidence; the isolated Capacity Lab measures only synthetic directional comparison and five WAIT slots, not actual complete scanner/chart/filter compute.
- `src/clone_day2_apply_queue.py` remains isolated and NOT imported by production `src/main.py`, so its successful 730/730 stress test does not establish full production readiness.

**Decisions / next guarded repair order:** (1) design explicit COMPLETE/PARTIAL/STALE/WAIT per-key initial stock readiness and in-app stage timings, (2) protect completed-bar durable stock and backpressure/retry, (3) profile actual scanner/chart/technical-filter computation and select screen updates, (4) replace coarse dashboard/scanner refresh with dirty-target delta updates while retaining state, (5) measure real Android on more than one hardware tier and varied delayed-arrival profiles. Keep Oracle, Dhan connectivity, current timeframe defaults and production V3 runtime untouched until targeted B1 tests warrant changes. No hard 1/3/5-second user deadline. This entry records requirements and read-only source findings only; none of the above repairs is yet implemented.


## 2026-11-21 IST — Owner final decision: full V3 source app with embedded real-cache 54 / 70-share test

Owner prefers existing genuine BOT KING V3 UI (not separate synthetic capacity lab). Preserve installed old APK untouched; build a new distinct-package test APK from the full real V3 source. After normal existing Clone SSK login, Settings at top offers **TEST 54 (51+3)** and **TEST 70 SHARES (+3 indices)**. Test is manual and reads already-arrived Dhan cache only; it must not initiate separate Dhan/Oracle requests, replace app with a mock, or manufacture live broker data.

Source changes in latest branch:
- `src/v3_building_doctor.py`: read-only partial/observed-cache progress and safe, monotonic login milestones (gateway authorization, Dhan quote response, stock application), Python page/update timings, adaptive UI refresh gap; no claim of Flutter pixels.
- `src/v3_live_capacity_probe.py` commit `3274e73f`: bounded read-only 51/70 selected equity plus 3 index probe from real cached quote and three timeframe histories; runs cached chart indicator + scanner technical computations; tracks per-frame missing data, elapsed Python stages, 70-slot selection shortfall. No network, no options LIVE signal assertion, no fake synthetic bars.
- `src/main.py` commits `7dc2b826` and `3a52888d`: integrates manually triggered 54 and 70 probe at **top of Settings** with on-screen selectable JSON report and typed errors, no separate provider call. UI control remains the full original app. Normal login captures gateway and stock milestones; prior B1/B2 tests retained. Test does not force 70 real symbols into watchlist if fewer are selected.
- `tests/test_v3_live_capacity_probe.py` commit `e1429544`: tests missing 70-share stock stays WAIT, exact 51+3 accounting, stored OHLC scanner/chart analysis, generation and timeframe isolation.
- `.github/workflows/v3-live-building-doctor-apk.yml` commit `9947be5c`: entire original full Android app (not miniature capacity lab), separate temporary-signing APK package `com.botking.v3live.bot_king_v3_doctor`, B141 with combined existing offline gate and new tests. GitHub Actions run `#44873572371` triggered; initial status pending. A subsequent Settings placement commit triggers newer workflow run; final APK and signing outcome must be verified rather than assumed.

**Limitations / release gate:** 54/70 tests reflect **selected symbols with market data already in local cache**. They report missing/WAIT honestly. Actual Dhan/Oracle network arrival times measured from login via local elapsed milestones, not full 70 symbol chart download. Five real options filters and Flutter raster/frame not measured. Do not claim complete real-time app on-device performance before the owner installs test APK, logs in, runs both buttons and submits results. Oracle and old installed APK unchanged. Keep live orders disabled. Final release only after B1/B2 runtime issues measured.


## 2026-11-21 IST — Owner per-stock incomplete-cache fallback and independent progress rule

Mandatory B1 behavior: a partial, invalid, stale or missing data component for a symbol must not stall the other symbols in the 70-equity+3-index workload. Mark only the affected symbol/component as WAIT for unavailable evidence, and show explicit sanitized code in System Health/Error Doctor for malformed data, mismatched timeframe/generation/expiry, callback/transport error, calculation error or retry exhaustion. Do not turn WAIT into fabricated bullish/bearish, a live option signal, or a sixth filter vote.

The processor advances immediately to the next ready symbol, while retaining a **bounded separate retry/wait registry** for incomplete ones. Retry should be triggered when fresh matching data arrives and by existing provider-controlled, rate-limit-aware normal refreshes, NEVER a tight polling loop or new independent broker request lane. On same-source, same-symbol/timeframe/expiry/generation completed evidence, validate the whole snapshot, calculate chart/analysis and publish one atomic per-symbol replacement. Until that success, show the previous last-good complete snapshot labeled historical/unverified where available; otherwise show WAIT placeholders. Do not reset the whole page or block ready peers.

User expects Dhan first responses to be generally complete, but this is an expectation, not a verified guarantee of 70 simultaneous complete live candles and option filters. Distinguish Dhan delivery, gateway, phone cache, computation and screen commit timings; guard partial/empty/off-hours/entitlement failures. Once per-symbol first-fill is complete, subsequent updates should update only changed values and keep already-mounted screens stable.

This entry is policy/requirements only. Implement and test the readiness state machine/atomic publication before claiming live runtime behavior. Preserve original installed APK and Oracle service unchanged.

## 2026-11-21 IST — Owner refinement: visible ERROR in place of generic WAIT on incomplete stock
Owner explicitly requests that missing/incomplete cache/Candle/filter/bullish-bearish readiness be visually identifiable as an **ERROR** rather than only WAIT so the Health/Error Doctor can identify the cause. Apply **diagnosable, sanitized typed error codes** at the affected symbol/component, preserve stage and timestamp; never leak credentials or payload bodies. Suggested classifications: `DATA_INCOMPLETE` (expected evidence not yet present), `CANDLE_INVALID`, `TIMEFRAME_MISMATCH`, `FILTER_EVIDENCE_MISSING`, `CALCULATION_ERROR`, `REQUEST_FAILED`. Do not imply every transient missing item is an irreversible program failure: visible ERROR is an operational diagnostic state; keep the affected analysis **non-directional / not eligible for trade** until actual evidence arrives. Internally retain WAIT/PENDING semantics for retry flow, but display an actionable error reason and Doctor issue for missing prerequisites. Continue other ready symbols, retry only via existing broker pacing or arrival notifications, and replace the per-symbol snapshot atomically on verified recovery. On recovery Health Doctor should mark the prior active issue RESOLVED and present accurate updated evidence; preserve historical events for audit. Do not fabricate sixth filter or live market evidence. **Requirements recorded only; actual stock-level error presenter and recovery classifier not yet implemented.**


## 2026-11-21 IST — B1 stock ERROR classifier / recovery implementation and B142 gate
Owner confirmed implementing typed visible errors in place of generic WAIT at the per-stock cached capacity diagnostic. New `src/v3_stock_diagnostics.py`: `classify_stock` checks existing Dhan quote and 1m/3m/5m cache presence, source/timeframe correctness and finite OHLCV bar structure; emits sanitized `DATA_INCOMPLETE`, `CANDLE_INVALID`, or `TIMEFRAME_MISMATCH` while keeping `analysis_eligible` and `live_signal_eligible` false. `DiagnosticRegistry` tracks active symbol errors and bounded ERROR/RESOLVED history per provider generation; omitted symbols on a smaller next test stay active, not falsely marked recovered.

`src/v3_live_capacity_probe.py` classifies every actually selected stock individually and adds `stock_error_count`, `stock_errors`, `stock_states`, and `stock_error_classification` timing to the existing cache-only 54/70 diagnostic; when fewer than 70 equities are configured, remaining absent equity slots are shown as missing count rather than fabricated securities. `src/main.py` Settings test triggers update the persistent, safe `stock_diagnostic_registry` and show Error codes and Recovery events in on-screen Health Doctor JSON. No new provider requests, trading, or server modifications; standalone installed old APK remains unchanged.

Added `tests/test_v3_stock_diagnostics.py` for missing data, bad OHLC bars, timeframe mismatch, missing-peer nonblocking, active/resolved recovery, generation isolation, and real 70 test shortfall. Workflow `.github/workflows/v3-live-building-doctor-apk.yml` now gates these tests and produces B142 separate full live V3 phone test APK. Run #44874828492 initially queued. APK success, Android runtime acceptance, actual 70-share live data completeness, production atomic whole-stock UI publishing and live 5-filter execution remain UNVERIFIED and must not be claimed. This implementation is **diagnostic-on-manual-test**, not yet a universal production card-level error presenter or full atomic stock publishing.


## 2026-11-21 IST — Real phone results and owner-directed ONE grouped six-frame/full-feature build

**Evidence supplied by owner** from genuine V3 phone Settings Building Doctor v2.3.138, screenshots at 12:03–12:04 IST: after SSK login, gateway authorized at 0.853s, quote response at 1.386s, quotes applied to phone stock at 1.470s. Both 54 and 70 tests reported only 51 configured unique equities + 3 indexes (54 actually observed), i.e. 19 unselected equity slots in 70-share test; quote cache 38/54, raw chart snapshots 1m 53/54 (SENSEX missing), directly stored 3m 0/54, 5m 2/54, technical scanner/chart count 2, Python technical compute 21.39ms (54) / 26.651ms (requested 70, actual 54), cache snapshot copy 163.149ms / 172.533ms. Measured page submission average ~17.56/17.73ms (60 samples), mounted refresh avg 72.724ms (11 samples); no exact Flutter raster proof. Existing 54-symbol 5m filter audit on screen separately showed 53 analyzed and 1 error; this is not proof five genuine verified options filters available.

**Two owner observations:** Scanner filters only appeared after Settings Retry Data; default NIFTY option-chain did not appear until BANKNIFTY->NIFTY selection caused on_change. Treated as potential boot/refresh routing defects, not CPU speed. Existing 3m watchlist derives completed 3m from locally available 1m; initial Doctor counted only directly stored 3m and underreported possible 3m readiness. Price and candle source paths are separate, so 38/54 quotes vs 53/54 1m history must not be conflated.

**Combined fixes applied on current branch** (keep old APK/Oracle untouched):
- `src/v3_live_capacity_probe.py` now derives and counts completed 3m from actual matching 1m; reports absent true quote keys and login source coverage separately. 10m and 30m are derived only from complete same-generation 5m and 15m bars. Six-frame presence/status and technical calculation use current local data only.
- `src/main.py` Scanner cache-only selected timeframe now checks matching `shared_history` before saved market snapshot and does not create additional Dhan request; SSK login triggers the existing paced default NIFTY options refresh, without waiting for symbol-change event. Login-source expected/received/missing counts are captured. Manual capacity test now includes precise login-to-test milestone and feature audit of Home/Super Five, five Watchlists, Scanner, Options, Chart, News cache, Filters, History, Doctor and UI refresh; no false exchange-live claims.
- Owner specifically instructed ONE whole timeframe segment, not piecemeal APK installs: 1m, 3m, 5m, 10m, 15m, 30m. `src/dhan_multi_timeframe.py` derives completed 10m from ordered Dhan 5m bars and completed 30m from Dhan 15m bars anchored to 09:15 IST, refusing gap, duplicate, partial, out-of-session/cross-session bars. Provider fetch maps requested 10m->5m, 30m->15m, keeping existing 2m and 1h options for backward compatibility. `src/scanner_engine.py` validates 10m spacing; Chart and Scanner selectors, cached-history resolver, Doctor presence and per-stock Error classifier all support six frames. Dashboard stays 1m, Watchlist 3m, Scanner currently selectable (no forced change).
- `tests/test_v3_timeframe_full_segment.py`, `tests/test_v3_phone_startup_wiring.py`, `tests/test_v3_full_phone_feature_gate.py` added alongside existing phone, queue, stock and error tests. Updated legacy B1 and adapter assertions to match new six-frame contract; latest B1, B2 and Adapter workflows PASS on commit `656b6674`.
- A single new `.github/workflows/v3-six-frame-final-offline-gate.yml` (commit `62a01394`, run `44876924335`) covers all V3 tests, original B1 and adapter tests before *one* final APK. Deliberately paused automatic APK workflow until gate PASS, to avoid repeated build-and-install churn. No production APK declared final; no broker/Oracle changes.

**Important remaining gates:** Confirm offline combined gate success. Ensure full Android APK job's entire offline suite and signing pass. Phone-install, login, 54 + 70 cache tests and Options/Scanner first-open behavior remain unverified, even after CI success. Only 51 equity holdings currently configured; test must not claim actual 70 selected or synthetic 19 missing equity prices. User must choose 70 real unique equities to test actual 73-instrument live load. Do not equate selective test cache timing with all display/raster timing.


## 2026-11-21 IST — Final single-install B143 gate and status
Owner requested comprehensive one-pass app/feature analysis and only one final phone-test installation; do not issue separate repeated 1m, 3m or 5m APKs. Added full-feature report to actual app Settings V3 Building Doctor covering Dhan/Oracle login, quote coverage and missing tickers, all six 1m/3m/5m/10m/15m/30m candle frame counts, matched-source derivation, chart and real cached technical analysis, scanner auto/candle/filter status, current options symbol/expiry/chain, Watchlist selection, Dashboard index slots, Super Five cache, News fusion cache, UI Python timing, error/recovery and active analysis filter names/count. Diagnostic never makes new provider calls, fabricates live data or trades. Logged exact login→test click/calculation timestamps. 70-share probe correctly shows 19 unselected stocks instead of manufacturing unavailable equities.

Preflight CI `V3 six-frame full-feature offline acceptance` GitHub Actions run **#44877028116 SUCCESS**. Verified all 37 V3 tests (after fixing 2 out-of-date assertion names), all existing B1 timeframe tests, Adapter audit, compile; prior B1, B2 and Adapter runs on `656b6674` also SUCCESS. Test contract assertions updated to include whole timeframe set. In the preflight, first attempt #44876924335 FAILED two static assertion naming differences; corrected and exact current gate passed. This is an offline gate, not phone readiness.

Enabled **ONE final full Android APK workflow** `.github/workflows/v3-live-building-doctor-apk.yml`, commit `441ee953285fed16d3172d43cacd0748bef25317` at GitHub Actions run **#44877090531**, currently IN_PROGRESS at entry writing. Full original app source with separate `com.botking.v3live.bot_king_v3_doctor` package, product `BOT KING V3 LIVE DOCTOR TEST`, build number **143**, version **2.3.138**, isolated ephemeral test signing. It requires all old unit tests, targeted B1/B2 and V3 source tests, signed APK aapt/apksigner verification and artifact upload. Previous B142/B141 runs were superseded/cancelled; do not treat them as final phone apps. No Oracle server change, original installed production APK preserved. Phone login, option default first-open, scanner filter auto-readiness, full 70 selected equity load and Flutter frame performance remain pending the owner's physical test. This B143 run is NOT yet declared SUCCESS or APK ready in this entry.


## 2026-11-21 IST — Full 1476 tests PASS; one final B144 Android APK currently building

Single-install policy preserved: B143 workflow run #44877090531 stopped before signing because the full 1476 legacy/new suite detected four newly stale/isolated test contracts: three had prior 1m/2m/3m/5m/15m/1h literal selections and one isolated Scanner cache-only test harness did not provide the real `shared_history` closure. Corrected only targeted expectations and injected a read-only shared-history stub in that isolated harness; the actual production Scanner now consults matching shared cached candles before saved fallback. Offline full test gate initially encountered an incompatible second FastAPI pin; configured it to honor `backend/requirements.txt`.

Full external GitHub **#44877450308 PASS**, both all V3 tests + original B1/Adapter and **all 1476+ full repository tests**; previous partial/full test failures #44876924335 / #44877379237 logged and corrected. No old installed APK/Oracle service modified.

Launched **only final signed full V3 phone-build** B144 at `#44877667052` from commit `ab83301e24b94c0e52fbe81bc2e0bf649a9b7ccf`, separate package `com.botking.v3live.bot_king_v3_doctor`, artifact target `BOT-KING-V3-REAL-CACHE-54-70-LIVE-DOCTOR-B144-APK`. During active verification, final-build GitHub full regression step SUCCESS and new Doctor tests SUCCESS, ephemeral signing certificate creation SUCCESS; actual Flutter/Flet APK build **IN_PROGRESS**, aapt/apksigner + artifact upload NOT YET VERIFIED as of latest check, so no download claim. Owner should not install until SUCCESS. The next owner physical acceptance is actual Clone SSK login then both Settings capacity buttons 54 and 70, inspect stock error, six-timeframe counts, first-page Scanner filters, default NIFTY option-chain readiness and supported refresh without manual selection switching. 70-test remains only 51 configured equities unless user actively selects 70 unique equity symbols; report must show 19 missing inventory as missing, not fictitious actual data.


## 2026-11-21 IST — FINAL B144 PHONE TEST APK BUILD SUCCESS (not phone-runtime acceptance)
GitHub Actions run **#44877667052** `completed/success`, https://github.com/vaishnavi596/volume-king/actions/runs/44877667052. Recorded SUCCESS for B2/B3 source/SSK contract and complete offline regression; V3 doctor targeted tests; distinct Android test signer; **full Flet Android APK build**; **aapt package/version and apksigner inspection**; and artifact Upload. Artifact actually exists: ID `14696542361`, name `BOT-KING-V3-REAL-CACHE-54-70-LIVE-DOCTOR-B144-APK`, ZIP size `65,820,492` bytes, not expired when checked. Final package `com.botking.v3live.bot_king_v3_doctor`, Android `versionCode 144`, app version string 2.3.138, product name `BOT KING V3 LIVE DOCTOR TEST`. This is a separate APK, not an in-place upgrade of installed original app; Oracle server not touched. User can download from that run's Artifacts section after signing into GitHub.

**Phone acceptance to perform once:** install separate B144 package; log in via existing Clone V2 SSK, observe first NIFTY option ready without changing selection; open Scanner and check filters without Settings Retry; Settings -> V3 LIVE BUILDING DOCTOR -> TEST 54 (51+3) and TEST 70 SHARES (+3 indices); capture on-screen full report sections for quote-source missing, six timeframe Dhan-history presence and local derived 3m/10m/30m, actual technical compute and Python UI, active typed stock Error/RESOLVED. Dhan data may be historical/off-hours; not guaranteed LIVE exchange verified. Verify Watchlist is still only 51 unique equities; real 70-share load needs 70 configured equities (no fake 19). 5 genuine verified option filters and exact Flutter raster timing still NOT measured; treat phone results as a verification gate, not completed final-release certification.
