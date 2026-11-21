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
