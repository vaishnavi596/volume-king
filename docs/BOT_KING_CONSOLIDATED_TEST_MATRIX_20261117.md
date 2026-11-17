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

## CI checkpoint closed; next root-cause audit — 2026-11-17
- Run [44021906603](https://github.com/vaishnavi596/volume-king/actions/runs/44021906603) completed **SUCCESS** at code SHA `7e1274049`; job `133833107931`, including Python syntax and full offline regression step, SUCCESS. This closes the diagnostic regression checkpoint, **not** Oracle/mobile release gates or newer documentation SHAs.
- Source audit for T04/T06: `src/main.py` `shared_history(sym,"3m")` accepts matching cached 3m and derives 3m from cached Dhan 1m; `watch_three_minute_signal` is explicitly read-only. Main 51-equity scan `load_one` requests `get_market_data(sym,"5m","2d")`, so it cannot by itself populate matching 3m candles. This is a **source-proven input-coverage gap**, not a new CI failure. Prior cache identity fix and WAIT text do not close it.
- Risk-controlled repair candidate: plan a bounded, selected/visible-symbol 1m warmup that reuses shared cache, honors singleflight and Dhan cooldown, does not contend with existing 5m scan, and retains last good history. Do not send 51 simultaneous requests or re-label 5m bars as 3m. Need tests for pacing, cache preservation and symbol change before source patch.


## T04/T05 repair intake checkpoint — 2026-11-17
- Branch HEAD at intake: `4e33c2f24ec5592a8b67add36be37a89fb632a2b` (journal). Last ten commits and twelve workflow runs inspected; chart-retention CI #1719 at `53b1262` and #1720 at `bedadb8` completed SUCCESS. Do not transfer this success to subsequent warmup SHAs.
- T04 source fixes: `724b67a` tags Chart's real 1m/3m Dhan timeframe in shared snapshots, then runs one-at-a-time foreground selected-Watchlist 1m warmup, locally producing actual completed 3m from three consecutive minute bars. `cf432a0` enforces 3 uncached upstream requests / rolling 180s and >=30s gap. The warmed 3m signal is still historical/unverified. No blanket 51-symbol burst, 5m substitution or live order code.
- Test additions: `7ea53e5` adds structural regressions for 3m source path, chart tag, warmup restrictions and index-lane guard; `843615d` checks rolling-window policy. Both *CI and real-phone outcomes remain PENDING* until exact SHA completion. Note that these are source-structure tests, not a provider replay or real-world refresh timing proof.
- Related gates: T03 index 1m scheduling conflict must pass regression; T05 retain-last-good must continue to pass; T06 UI stable candle/percentages remain phone-validation pending; T12 mobile-data/provider cadence is bounded in source but actual Oracle/Dhan request counts remain unverified.
- Release T16: BLOCKED. Do not sign APK from a SHA newer than a verified joint test and integration result. After-hours manual 3m historical refresh remains separate pending acceptance check; normal market-hours-only warmup does not implement it.

 
## T06 3m historical-vote retention checkpoint — 2026-11-17
- Final completed baseline: #1724 / run 44024474140, exact code SHA `843615d07`: 1103/1103 offline PASS; source and test include T04 bounded 1m input acquisition. #1723 / 44024460797 failed *only* the now-superseded test expectation for fixed-window counting (1/1103 failure); #1724's rolling-window guard resolves that mismatch.
- New independent failure mode in `watch_three_minute_signal()`: a temporary missing/partial series, unusable quality, empty fresh votes or exception discarded prior valid 3m historical directional votes, making colored Watchlist historical percentages disappear. Source repair `65ce21ac7` uses the existing fail-closed `retain_last_filter_votes()` only for same-generation/same-filter 3m cache, keeps `WAIT`, `score=0`, `historical=True`, `live_verified=False`; valid later 3m replaces it. It does not populate the five independently verified evidence engines.
- Functional replay-style offline tests (actual extracted function, mocked input, no Dhan) at `63b9ddbd0` cover missing source, retention, config/provider mismatches, invalid OHLC quality and valid replacement. CI #1725 (source) and #1726 (functional test) were IN_PROGRESS at latest checkpoint. T06 mobile UI behavior is PENDING, and five-engine T09 remains separately BLOCKED by source verification where not configured.
- Do not label this new behavior CI PASS until #1726 finishes; no Oracle deployment or signed APK, T16 release remains BLOCKED.

 
## T07 Scanner source-side batch — 2026-11-17
- T07 read-only audit identified extra Dhan fetch on simulation-only controls in `trigger_scan()`; `1fb114842` prevents budget/min/max/expiry/trend edits from scheduling candle history, while preserving explicit symbol/interval selection refresh. Simulation settings are saved for next selected scan.
- Same patch retains prior good **same-timeframe** Dhan scanner-chart history before replacing it with shorter/partial non-empty candles, reusing tested `retain_candle_history`; no extra network or live-order calls.
- Functional mock-UI/source + real retention helper tests added at `80404dd8f`. CI #1727 / #1728 are IN_PROGRESS at intake. T07 live phone first-chart-on-symbol-change is not established by tests; T05 last-good scanner chart device recovery is also pending.
- Newest completed baseline #1724 (1103/1103 PASS on `843615d`) does not prove T06/T07 SHAs. T16 release remains BLOCKED.
