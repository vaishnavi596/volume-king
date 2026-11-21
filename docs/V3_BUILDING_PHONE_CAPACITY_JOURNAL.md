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
