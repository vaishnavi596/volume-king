# BOT KING — Consolidated Pre-Fix Test Matrix (2026-11-17)

Status: AUDIT / TEST COLLECTION, NOT RELEASE PASS. Branch: `fix/botking-joint-audit-70-15-20261115`.

## Operating rule
Collect all remaining failures and evidence BEFORE making more source repairs. Group root causes, patch related changes together, run a complete final offline regression and integration gates, then signed APK and real-phone market test. Do not delete historical runs or assume a cancelled run failed. Do not change production Oracle without preflight, backup and postflight proof. Do not make live broker orders.

## GitHub evidence baseline
Last ten commits at intake: d95e171ba, 7ace62329, 7e1274049, 0d968c673, 755d2498b, 358c158ad, a6387c011, 4c504aece, 51dd726a9, 18a3cb2c5.
Latest 20 runs inspected: 44021906603 IN_PROGRESS and 44021896629 IN_PROGRESS at intake; 44018312569 SUCCESS; 44018292533 CANCELLED; 44015524269 SUCCESS; 44015513031 CANCELLED; 44014400347 SUCCESS; 44014385479, 44013488865, 44013473530 FAILURE; 44012249070 joint gate SUCCESS; 44011857387 joint gate FAILURE. Earlier history also contains successful and cancelled runs. Recheck outcomes before any repair.

## One-pass test intake / expected evidence

| ID | Component | Required test / acceptance evidence | Current evidence / status |
|---|---|---|---|
| T01 | Login & bootstrap | First authenticated session loads quote and index lanes without 3-minute idle; retry, token expiry, offline | Mobile end-to-end pending |
| T02 | Equity LTP | 51 base equities and selected extras; cache preservation; 09:10–15:45 IST poll; no whole-page redraw | End-to-end pending |
| T03 | Index LTP | NIFTY/BANKNIFTY/SENSEX independent of equity queue; correct source and timestamps | End-to-end pending |
| T04 | Watchlist 3m | Per-symbol matching 3m OHLCV available; completed candles; revised last row invalidates signal; no 5m substitution | Revised OHLCV identity offline PASS at CI 44018312569; acquisition missing for many equities, pending |
| T05 | Last-good retention | Rate-limit/partial/empty/malformed history never progressively clears valid candle or votes | Partial offline coverage; device pending |
| T06 | Watchlist UI | Red/green candle bar and five-filter chips remain stable on quote refresh; WAIT explains missing source | Pending; diagnostic change CI in progress |
| T07 | Scanner | Symbol/interval change promptly updates selected chart and analysis, no navigation workaround | Pending |
| T08 | Super Five | Shared filter engine, candle display parity, independent cached local refresh | Pending |
| T09 | Five engines | Distinguish five evidence engines vs 17 deferred research indicators; valid bullish/bearish percentage basis; unsupported sources WAIT | Pending |
| T10 | Index candle | 1m completed candle bars and consistent NIFTY/BANKNIFTY/SENSEX display | Pending |
| T11 | Options | CE/PE, expiry, OI, PCR, max pain; test indexes and equity support separately; no fabricated option votes | Pending |
| T12 | Provider limits | Dhan-only, no Yahoo/Angel fallback, shared pacing/cooldown/singleflight, no 51-symbol 1m burst | Pending |
| T13 | Resume / hours | Background/foreground, market-closed freeze, after-hours manual data refresh | Pending |
| T14 | Assessment | Oracle factor contract, missing/unverified feed fail-closed, no false live verified label | Prior regressions exist; final end-to-end pending |
| T15 | Read-only safety | No live order routes/calls; auth key protected; server health | Server audit/integration pending |
| T16 | Release | Complete regression PASS on final SHA, signed APK, bumped versionCode/versionName and UI version, phone installation | BLOCKED until gates |

## Root-cause hypotheses requiring proof
- Main 51-equity history scan fetches 5m, while Watchlist signals require matching 3m and can only derive 3m locally from existing 1m data. Do NOT rebrand 5m bars as 3m or launch 51 concurrent 1m calls.
- Watchlist signal cache previously keyed only on final timestamp/count; fix now keys on full final candle, offline test PASS. Live retention remains unverified.
- Five-engine WAIT may reflect genuinely unavailable news/futures/options sources rather than a computation bug. Keep evidence engines distinct from scanner technical filter list.
- Index 1m and main 5m lanes have separate snapshots; test UI selection and provider cooldown before changing fetch cadence.

## Consolidated fix gate
1. Resolve in-progress CI, collect failing job/step/log evidence.
2. Audit tests and code paths for T01–T15; label each PASS/FAIL/BLOCKED/NOT TESTED with SHA and evidence.
3. Group fixes by shared cause (history/cache/UI, filters/assessment, options/provider, bootstrap/lifecycle), apply small coherent patches with regression tests.
4. One final joint regression run on final source SHA; check older ten runs before each write.
5. Oracle/Dhan authenticated checks only with access and rate caps; user phone/live market test after signed APK. Do not mark unavailable evidence PASS.

Deferred: 17 technical/option filter five-group research (not release blocker).

## Incremental checkpoint — 2026-11-17, run 44021906603
- GitHub workflow still IN_PROGRESS at SHA 7e1274049; job 133833107931: checkout, Python setup, dependency install, syntax PASS; `Run offline regression suite (no APK build)` IN_PROGRESS. No test percentage or partial failure logs exposed.
- Inspected `tests/test_watchlist_refresh_regression.py` new diagnostic assertion against `src/main.py` function `compact_watch_signal`: exact function boundary, WAIT text and `row.get("timeframe")=="3m"` guard present. **Static source alignment only, not execution PASS.** No speculative source patch.
- Continue to collect actionable failures from finished steps; do not confuse a running job with a failed test or new SHA verification.
