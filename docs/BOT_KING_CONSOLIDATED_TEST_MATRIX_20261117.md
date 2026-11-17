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


## T06/T07 result closure and T09 read-only five-engine review — 2026-11-17
- Verified GitHub full offline regression logs: #1725 at `65ce21ac7` **1103/1103 PASS** (job 133847251106); #1726 at `63b9ddbd0` **1109/1109 PASS** (133847538428); #1727 at `1fb114842` **1109/1109 PASS** (133848711295). Source + added tests for 3m historical vote-retention (T06) PASS only to `63b9ddbd0`; Scanner simulation-only no-extra-request and same-timeframe chart retention source PASS only to `1fb114842`.
- New T07 1m default + first auto-scan exchange-hours guard source `aab055dec`; structural regression additions `c6c297be` and escaped-newline test correction `dcf6a2bce`. At checkpoint #1728–#1731 were IN_PROGRESS; some had syntax PASS, none has yet been promoted to full-suite PASS. Existing saved scanner timeframe is not overwritten by default. Closed-session explicit user selection is a separate action from automatic scan.
- T09 read-only source inspection: five evidence engines are canonical `technical,candle,news,futures,options`, independent of the Watchlist 3m *technical-filter agreement*. `five_engine_chips()` and `five_engine_summary()` correctly present historical technical/candle context as HIST / NOT live without counting absent News/Futures/Options as verified votes. Unverified PCR and Max Pain are context only, not directional option signal. A full 5/5 Bullish/Bearish result cannot be declared functional without verified per-engine data; missing feed is a legitimate WAIT and T09 remains INTEGRATION PENDING, not automatically a code failure.
- T01–T03 bootstrap/index live source freshness, T10 index candle on device, T11 equity option-chain route support, T12 Oracle/Dhan provider count, T13 manual after-hours cadence, T14 assessment production parity, T15 read-only server safety and T16 signed APK remain open as stated above. Freeze and final joint tests only after relevant in-progress tests settle. No Oracle or mobile proof claimed.


## T05/T07/T13 follow-up repair and CI correlation — 2026-11-17
- CI #1728 at `80404dd8f` **1112/1112 PASS** (full offline). #1729/#1730/#1731 red: the source default moved to requested Scanner 1m, but the 5m shared-analysis and Yahoo-news fixtures did not explicitly set 5m; old `saved_scanner_tf="5m"` static assertion was obsolete. #1730 additionally had the now-fixed escaped-newline assertion. Failures are real regression test incompatibilities, not permission to abandon 1m default.
- Two test-only fixture repairs: `b7247ba28` pins TCS 300-second historical scan tests to 5m; `4b1297ee7` corrects 1m fallback source assertion and Yahoo 5m-news failure test setup. #1732/#1733 retest results pending.
- New source-proven T13/T05 risk: Android resume allowed selected scanner 1m/3m candles to replace unlabeled quote bars that a legacy shared 5m filter consumer would read as 5m, and its Chart-tab resume could overwrite a valid history with a short/empty response. `99d33430f` protects Dhan history through same-timeframe snapshot identity, guarded 5m quote update and last-good chart retention. `4d8ac7800` updates six resume regressions (including real retention helper on partial 1m bars). #1734/#1735 CI pending.
- T04 source acquisition is bounded as previously recorded. T09 verified five engines remain independently gated. T13 after-hours user-manual refresh, T01 bootstrap and T11 option equity support are still separate acceptance gates. T16 APK remains BLOCKED pending CI and Oracle/phone integration; no new APK/production deployment.


## T11 / T13 read-only source evidence checkpoint — 2026-11-17
- T11 GitHub *source* parity: `backend/server.py` POST `/dhan/option-expiries` and `/dhan/option-chain` accept mapped `IDX_I`, `BSE_I` and `NSE_EQ`, and enforce auth, expiry/date, quota and incomplete-feed errors. `backend/dhan_feed.py` supports those underlying segments in the broker adapter. `src/server_feed.py` validates returned underlying, expiry, unverified PCR/Max Pain and `signal_eligible=False`. Thus current GitHub source has a contract for NIFTY/BANKNIFTY/SENSEX and mapped NSE-equity underlyings, **but deployed Oracle and broker equity option entitlement remain UNVERIFIED**; T11 stays PENDING, no claims that RELIANCE/HDFCBANK options actually load.
- T13 manual refresh path `refresh_all_dhan_quotes()` currently honors 30s manual cooldown and refreshes read-only equity and index **LTP** even after market hours. However Watchlist 3m source warmup requires `refresh_hours()`; tapping Watchlist Refresh does not explicitly schedule 1m candle warmup, so **after-hours manual 3m candle refresh is not implemented/proven**. Keep T13 as PARTIAL, separate planned behavior; do not silently increase broker calls or change after-hours snapshot semantics without controlled tests.
- #1734 SOURCE `99d33430f` had 1114 tests, 2 old assertions for raw `quotes[sym]=data`. #1735 TEST `4d8ac7800` had 1117 tests, one remaining obsolete mobile source assertion. `03eb8ce8` replaces that with a fail-closed historical/non-live expectation. #1736 exact-SHA full suite is PENDING; do not call APK ready or mark resume mobile PASS.


## Joint release gate readied; #1733/#1736 fully PASS — 2026-11-17
- #1733 run 44028485468 / `4b1297ee7`, job 133854443711, **1114/1114 PASS**: Scanner 1m default, intentional 5m legacy test fixture parity, runtime selected-history behavior, no Broker calls. #1736 run 44029150443 / `03eb8ce8`, job 133856601867, **1117/1117 PASS**: Android resume selected 1m/3m isolation from 5m and strict last-good history/quote guard, plus prior T04–T07 changes. Both complete Python compile and full offline suite; old failures retained historically but *resolved at the later source/test SHA*.
- Five-scope joint gate workflow `.github/workflows/botking-joint-regression-gate.yml` reviewed: complete-offline-suite, login-watchlist-index, candles-scanner-superfive, option-chain-five-filters, android-release-contract. Pending one controlled workflow-path push to trigger them on a fresh documentation-only head; no APK.
- Remaining non-CI gates: T01/T02/T03 actual post-login + 51 equities + 3 index performance/age; T06 device historical votes; T09 **five independent engines** external feeds (WAIT where absent); T11 deployed equity chain route and broker entitlement; T12 shared Dhan request budget/cooldown and Oracle snapshot collector age; T13 explicit after-hours candle refresh still missing; T14 Oracle assessment parity; T15 production read-only/auth/orders-off proof; T16 APK version/sign/build/device. Status still **BLOCKED** despite offline regression PASS.


## Joint #3 incremental five-scope gate — 2026-11-17
- GitHub Actions [run 44031362802](https://github.com/vaishnavi596/volume-king/actions/runs/44031362802) pinned to code+workflow SHA `676fc1e4e1fdf9731ff16a426bed06d2ddc0c757`. Activated by workflow **comment-only** commit, no functional workflow changes. Four jobs completed **PASS**: `login-watchlist-index` 133863838561, `candles-scanner-superfive` 133863838615, `option-chain-five-filters` 133863838622 and `android-release-contract` 133863838238. `complete-offline-suite` 133863838602 syntax **PASS**, final regression still **IN_PROGRESS**; do not label full joint gate PASS yet.
- Under T04/T03, the 5m `refresh_market()` initial 54-symbol history scan runs with `dhan_history_scan_active[0]` set. The newly bounded selected Watchlist 1m→3m `watch_three_minute_warmup()` and the independent 1m index candle poll both skip provider calls while the long scan remains active; **initial 3m/index history may be delayed despite restored last-good values**. This is a source-level scheduling/UX risk, not a measured mobile latency. Audit potential rate-safe interleave only after immutable Joint #3 finishes or as a separate controlled repair batch with fresh full test gate. No user-market data was queried.
- T11 source-level equity option support remains distinctly *not deployed Oracle proof*; T13 manual after-hours Watchlist 3m history still missing; T14 assessment producer production parity and T15 read-only protection remain Oracle-operator checks. T16 RELEASE **BLOCKED**.


## Gate #3 closed and T04 early 3m priority new source/test intake — 2026-11-17
- Full five-job [Joint Gate #3](https://github.com/vaishnavi596/volume-king/actions/runs/44031362802) at `676fc1e4e1` **5/5 PASS**; 1117/1117 complete offline plus scoped 131 Android, 98 login/watch/index, 94 candle/scanner/Super Five, 43 options/five-engine test executions PASS, subject to overlap. This is a GitHub code-only acceptance, not Oracle or phone PASS.
- T04 startup scheduling priority source `7c940c30b` borrows at most one selected Watchlist 1m→3m acquisition **before** the long 5m equity tail, using the same 3/180 rolling request budget and 30s 1m global spacing as periodic scheduler, in-market foreground only. 5m ranking and 1m input remain distinct; 1.5s pacing and cooldown preserved. #1737 / 44033276947 at source SHA 1117/1117 PASS. Network-free nine-case executable priority helper test `4c259645d`, guard literal fix `4586d74c0`; #1738/#1739 running, not yet closed.
- Next source risk T10: 1m NIFTY/BANKNIFTY/SENSEX index poll also waits for long 5m scan, so dashboard 1m historical bars may still delay. Assess separate early-provider work against Dhan budgets and legacy index-mapping smoke before change.
- T01 first-login and indexed quotes, T09 external five-engine evidence, T11 equity option entitlement, T12 collector rate/age, T13 manual after-hours candle history, T14 Oracle assessment parity, T15 authenticated deployed read-only safety and T16 signed APK remain separate blocked/unverified gates. No Dhan production probe performed.


## T04/T10 startup history scheduler progress — 2026-11-17
- T04 priority **SOURCE+TEST CI PASS** at `4586d74c0`, #1739 [44033512195](https://github.com/vaishnavi596/volume-king/actions/runs/44033512195) 1126/1126 PASS; first eligible visible Watchlist 1m acquisition borrowed from existing 3/180 rolling budget, 30s global spacing, before 51-equity 5m tail. Source-only #1737 1117/1117 PASS. No latency proof from phone.
- T10: `3f00d978d` source brings up to three NIFTY/BANKNIFTY/SENSEX 1m histories ahead of 51-equity 5m tail *inside the same serialized Dhan worker*. It uses same 180s `index_candle_last_attempt/index_candle_generation` as existing index 1m poll, 1.5s gap, cache reuse and 429 cooldown; no new timer, after-hours background requests, 5m context substitution or false exchange-live claims. `608227861` adds nine no-network actual-helper tests (ordered/limited fetch, cache, correct history, retention, provider mismatch, cooldown, 180s reuse). CI #1740 and #1741 PENDING and device/Oracle history routes NOT VERIFIED.
- Other remaining critical gates: T01–T03 real authenticated login/3 index + 51 equity quote freshness; T06 red/green 3m user-phone retention; T09 verified five engines unavailable when source missing; T11 deployed equity CE/PE entitlement; T12 shared upstream count/429; T13 manual after-hours 3m history; T14 real assessment route; T15 read-only/live-orders-disabled actual production; T16 APK build and one-phone test. No release promotion while any blocking evidence is absent.


## T10 index early history source/test CI CLOSED — 2026-11-17
- CI #1740 [44034186877](https://github.com/vaishnavi596/volume-king/actions/runs/44034186877), exact source SHA `3f00d978d01f9acd2999f4ade406b34e77ab3384`, job 133872984150: Python syntax and full **1126/1126 PASS**.
- CI #1741 [44034335037](https://github.com/vaishnavi596/volume-king/actions/runs/44034335037), exact source + test SHA `6082278618f1d3baad939c5c2b9a93d13d347aa5`, job 133873464517: Python syntax and full **1135/1135 PASS**, including nine new executable early-index helper tests. No known code/test regression at this latest executable SHA.
- T04 early Watchlist 3m #1739 **1126/1126 PASS** and T10 early index 1m #1741 **1135/1135 PASS** verify serialized source policy only. Source now prioritizes selected Watchlist 1m and three index 1m histories in the existing paced Dhan history lane, before the long remaining 5m equity history tail. It does not prove Dhan API entitlement, latest 1m market timestamps, provider HTTP429 frequency, three index chart display on phone or user-observed latency; these integration T01/T03/T10/T12 gates stay pending.
- Next T13 after-hours manual data refresh: Watchlist button currently checks equity/index quotes with 30s cooldown but has no explicit after-close candle history fetch. Need single-symbol, explicitly user-triggered Dhan-only history request with 1m budget/cooldown and same-timeframe retention, not auto polling; keep T13 PENDING. Oracle production and APK remain BLOCKED.
