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
