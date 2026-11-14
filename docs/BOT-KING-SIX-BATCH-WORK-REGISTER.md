# BOT KING — Six-Batch Work Register (2026-11-14)

This is the persistent handoff/checklist for BOT KING. Update the status only after verifying code, tests, Oracle deployment, and phone behavior separately. A commit is not a deployed fix.

## Batch 1 — Dhan data path, index LTP, watchlist refresh (ACTIVE)

**Scope:** 51 equity symbols + 3 indexes = **54 displayed instruments**. Preserve the equity-only 51-symbol scan, equity snapshot, and Super Five ranking. Index quotes/candles are separate from the equity snapshot. Do not count the three indexes as additional equities or claim exchange-timestamp-verified live data.

| ID | Work item | State / evidence |
|---|---|---|
| B1-01 | Index instrument mappings for NIFTY IDX_I/13, BANKNIFTY IDX_I/25, SENSEX BSE_I/51 | **Oracle mapping verified PASS** (2026-11-14): all three present in server.py; syntax PASS, service health PASS. GitHub mapping committed. |
| B1-02 | Authenticated Oracle LTP for all three indexes | **PARTIAL:** NIFTY HTTP 200, LTP 25144.3, freshness unverified; BANKNIFTY and SENSEX HTTP 429 due rate-limit/cooldown; positive quotes still unverified. |
| B1-03 | Dashboard three configurable cards and independent index refresh | **CODE UPDATED:** index refresh now one batch request per >=60s; preserves last-good prices; Android verification and latest CI still required. |
| B1-04 | Watchlist 51 equities + 3 index cards = 54 displayed instruments | **CODE UPDATED:** index cards separate from equity snapshot/scanner; Android display and refresh verification pending. |
| B1-05 | Foreground watchlist polling, reconnect/resume, last-good retention | **CODE UPDATED:** manual refresh, 30s foreground poll, resume recovery, separate index cooldown; phone verification pending. Continuous background service NOT implemented. |
| B1-06 | Full regression, Oracle integration, signed APK and device acceptance | **IN PROGRESS:** historical CI PASS at bf0903d; offline CI failed one stale assertion at bf0903d; test fix committed 5929101; CI PASS at 41bed67. Oracle batch deployment, Android test, versionName/versionCode, signing and APK pending. |
| B1-07 | **NEW:** rate-limit-safe one-request index batch | **CODE UPDATED, NOT DEPLOYED:** authenticated POST /dhan/index-ltp-batch; DhanFeed.batch_ltp used once for 3 indexes, partial results, 429 Retry-After; mobile transport and main UI refresh wired; endpoint contract tests added at 41bed67 and CI PASS; Oracle integration pending. |

**Batch 1 acceptance:** authenticated read-only Oracle LTP for each mapped index; 51 equity snapshot remains independent; 54 display without adding indexes to equity ranking; watchlist refreshes on schedule and after resume; last valid quotes retained but labelled unverified; no Yahoo/Angel fallback; regression green. Keep live order routing disabled.

## Batch 2 — Historical candles and charts (QUEUED)
- Audit prior screenshots: only two/three equities displayed candles; many symbols lacked candles.
- Verify 5-minute and other selected timeframe candle availability for all 51 equities and three indexes; distinguish missing history, rate limiting, cooldown, and chart UI errors.
- Chart search/select for NIFTY, BANKNIFTY, SENSEX; preserve candle timeframe isolation from scanner quotes.
- Validate candle timestamp/freshness; historical_unverified is not a live signal.

## Batch 3 — Scanner, Super Five, signals (QUEUED)
- Audit the two previously reported scanner screenshots/issues and their error/progress states.
- Validate 51-equity scan completion, priority scheduling, Super Five ranking, bullish/bearish votes and paper-bot behavior.
- Avoid per-equity request fanout, duplicate polling and misleading confidence; keep real orders disabled.

## Batch 4 — Dhan options and market metrics (QUEUED)
- Listed expiries, option chain, OI, PCR, Max Pain, premiums, source and freshness.
- Preserve expiry validation and 422 on invalid expiry; fail closed when signal eligibility is false.
- Read-only options integration; no implied automated real trading.

## Batch 5 — Watchlist UI, presentation and usability (QUEUED)
- Five saved lists, filters, per-row bullish/bearish percentages, chart status, diagnostics, compact navigation.
- Coordinate presentation with Batch 1 index cards; do not duplicate the data acquisition work.
- Persist Dhan connection preferences and protect secrets.

## Batch 6 — End-to-end release (QUEUED)
- Run backend, offline regression and Android build checks; investigate failed CI rather than assuming success.
- Verify versionName **and** versionCode advance, signing identity, install/upgrade path, release artifact and phone test.
- Check Dhan-only provider isolation, lifecycle recovery, 54-instrument display and 51-equity scanner; live orders OFF.

## Execution discipline
Work on Batch 1 first; track fixes in small related commits (2–4 items per pass). Mark a task DONE only when relevant tests and real deployment/phone verification support it. Keep backup before Oracle production edits. Update this register whenever batch scope/status changes.


### Batch 1 grouped-audit note
- GitHub branch: `botking-b1-index-mapping-20261114`; draft PR #111. Commit is not deployment.
- Newly found/fixed: index polling was blocked by equity snapshot cooldown; concurrent or frequent index polling risk; stale dashboard warning incorrectly claimed BANKNIFTY/SENSEX mapping unverified after mappings were added.
- Never expose pairing credentials or overwrite Oracle `/opt/bot-king-server/server.py` without comparing with repository and taking a timestamped backup.
- Acceptance requires actual HTTP 200 + positive LTP for all three indexes, verified watchlist/dashboard display, and a clean new versioned signed APK.


### Batch 1 running verification ledger — 2026-11-14
- Original six items: **0/6 fully end-to-end accepted**; B1-01 Oracle mapping stage verified, but acceptance across the complete batch is not finished. New B1-07 makes **7 tracked items**; **0/7 fully accepted**. Do not conflate code commits with deployed/device-tested completion.
- Oracle: service active, /health HTTP 200; NIFTY /dhan/ltp HTTP 200 (25144.3, freshness unverified); BANKNIFTY and SENSEX HTTP 429; no repeated provider probing during cooldown.
- GitHub index-batch commits: 44ce59c backend endpoint; 3e34d76 mobile transport; 7114566 foreground UI refresh; 194c164 and bf0903d tests; 5929101 stale generation assertion correction.
- CI: 7114566 offline failed 2 old assumptions; bf0903d offline failed 1 stale assertion; historical regression passed. **Recheck CI at 5929101 and after this register commit.**
- Remaining critical path: (1) latest offline+historical CI green and endpoint-specific tests, (2) backed-up Oracle deployment of exact endpoint with local changes preserved, (3) one authenticated index batch test including partial/rate-limit behavior, (4) Android dashboard/watchlist/resume/51-equity scan verification, (5) bump both versionName and versionCode, signed APK and install test.
- New issues must be added as B1-08 onward, or as a clearly marked subtask, with evidence and unresolved status. Update this register in each related change batch and do not silently mark pending items DONE.

### CI checkpoint — 41bed670 (2026-11-14)
- Offline Regression **PASS**: https://github.com/vaishnavi596/volume-king/actions/runs/43550132583
- Historical Candle Regression **PASS**: https://github.com/vaishnavi596/volume-king/actions/runs/43550132600
- New tests/test_dhan_index_batch_endpoint.py verifies pairing-key denial, one three-index provider call, partial index response, and HTTP 429 Retry-After.
- **No Oracle deployment or Android APK verification has occurred for this new endpoint.** Next: compare deployed server.py with branch, timestamped backup, safely deploy exact change, compile/restart/health, then one authenticated index batch probe. Keep live orders disabled.


---

## Refreshed execution sheet — 2026-11-14, mobile v2.3.102

**Evidence precedence:** This section supersedes the older QUEUED and pending descriptions above where a newer verified observation exists. Keep original ledger as historical audit evidence. A code/test PASS is distinct from mobile PASS and exchange-verified live data. This is a refreshed work sheet, not a claim that all batches are finished.

**Batch 1 — FUNCTIONAL MOBILE ACCEPTANCE, conditional live follow-up.** On installed v2.3.102, user screenshots confirm Dhan-only 51/51 equity LTP, separate NIFTY/BANKNIFTY/SENSEX positive LTP, 54 instruments displayed, three independent Dashboard analysis selectors, index cards stacked vertically, and historical vote bars on Dashboard and Watchlist. The quote status explicitly says exchange timestamp unverified. BK-102 initial 10s retry, 180s regular foreground polling and manual 30s guard are implemented; 180s timing and foreground/background behavior have not yet been measured over multiple cycles on phone. Preserve last-good prices and no real orders. Signed APK Build #43575086543 PASS; offline tests #43574393006 PASS (584 tests). B1 index LTP is no longer blocked as in the older ledger, but authenticated Oracle endpoint testing and market-session freshness are not re-proven by screenshots. Do not call B1 exchange-live verified.

| Batch | Already implemented or observed (avoid duplicate work) | Still to audit/implement and acceptance evidence | State |
|---|---|---|---|
| B2 — Candles / charts | Historical 5m candle technical votes are visible for NIFTY 100/0, BANKNIFTY 100/0, SENSEX 86/14 and RELIANCE 88/12, HDFCBANK 100/0 in v2.3.102; 51/51 equity candle scan reported in previous phone tests; timeframe-isolation and index-history cache code/tests exist | Check all 51 equities + 3 indexes for requested chart timeframes, actual OHLC bars, timestamps, gaps and 429/cooldown; ensure Chart UI candle rendering and no cross-timeframe contamination; verify index history refresh independently of end-of-scan and diagnose WAIT vs bullish votes; verify during open market; never label historical as live | **PARTIAL / NEXT ACTIVE** |
| B3 — Scanner / Super Five | 51-equity scanning, Super Five ranking, historical vote filters and paper-mode controls exist; prior 51/51 scan completion observed; historical votes labelled NOT live | Measure full scan latency and Super Five turnaround; check priority queue, retry/WAIT, empty/missing histories, 429, duplicates, and paper-only signal eligibility; 51 equity total must exclude indexes; compare actual app results and regression | **PARTIAL / PENDING ACCEPTANCE** |
| B4 — Options / market metrics | Prior authenticated expiry/chain tests: HTTP 200; 18 expiries; PCR ~0.83049; Max Pain 25100; invalid expiry HTTP 422; source Dhan, freshness unverified, signal eligible false; option adapter and tests exist | Validate chain OI, PCR, Max Pain, premium, expiry selection and UI consistency against backend; 429 handling, freshness and fail-closed behavior; paper-only, real orders OFF | **PARTIAL / PENDING MOBILE** |
| B5 — UI / lifecycle / diagnostics | Five watchlists, 54 displayed instruments, index vertical cards, configurable 3 Dashboard slots, equity and index historical green/red ratio bars, manual quote refresh, 10s initial/resume path, 180s foreground polling, last-good quote retention, Dhan-only preference guards are in code or phone screenshots | Test 5-list persistence after reboot/upgrade, navigation and scrolling, 30s manual vs 180s automatic timing, app background/resume, Dhan credential persistence, Error Doctor visibility and precise error codes; no claim of continuous background service | **MOSTLY IMPLEMENTED / ACCEPTANCE PENDING** |
| B6 — Regression / release | 584 offline regression tests PASS at #43574393006; signed v2.3.102 APK build PASS #43575086543; user installed v2.3.102 and confirmed index/equity LTP and historical vote bars; Live OFF | Verify manifest versionCode explicitly, signing identity versus installed app, full Android upgrade/reboot, backend auth/security, Dhan-only isolation, real-market end-to-end B2–B5, no regressions. Release build PASS does not mean all product functions PASS | **BUILD PASS / FINAL E2E PENDING** |

### Batch 2 action order (next grouped audit)
1. B2-01: distinguish **OHLC candle bars present** from **bullish/bearish historical vote bar present**; the latter is not a plotted candlestick chart.
2. B2-02: inspect index history ingestion and cache independently of the 51-equity scan; capture source, timeframe, bar count, timestamp and cooldown, no unverified freshness promotion.
3. B2-03: check 51 equity + 3 index 5m data availability, retry/429 and missing/partial response behavior without flooding Dhan.
4. B2-04: validate Chart UI selection, OHLC plot, timeframe isolation, and Dashboard/Watchlist shared historical vote calculation; explain WAIT vs 100% bullish.
5. B2-05: add focused regression tests, commit grouped fixes, run offline tests; only build a new APK if a code change warrants it and bump both versionName and versionCode.

**Live-market gate:** Market-session exchange timestamp and 180-second actual refresh cadence require separate phone verification; neither is established by a successful Saturday historical screenshot. Do not treat 100% bullish votes as win probability or permission to trade.


### B2-01 source audit checkpoint — 2026-11-14
- Inspected current src/main.py at v2.3.102 branch, not just prior screenshots.
- fetch_market_data_uncached accepts Dhan 1m/5m/15m/1h, calls dhan_feed.intraday, normalizes with clean_bars, rejects empty/future candles and labels history unverified. This is code evidence, not proof that all timeframes or 54 instruments return data.
- get_market_data shares a 90-second Dhan historical cache keyed by provider generation, symbol, interval and range. Timeframe cache isolation exists; actual plotted chart still needs inspection.
- Equity historical scan handles Dhan 429 by marking remaining symbols unattempted, cooling down and retrying rather than marking an incomplete scan complete.
- Specific B2 risk: index histories warm only after a successful equity scan; the index loop stops on intraday cooldown. Fresh LTP and historical vote bars can coexist with stale index candles. Phone screenshots showed approximately 22-hour-old historical votes.
- Next code audit: decouple rate-limit-safe serialized index history scheduling from equity scan completion, retain last-good candle cache on errors, and add regression guards.
- Historical vote bars are not full OHLC candlestick plots; Chart UI and all timeframe OHLC verification remain open.
