# BOT KING — Canonical Master Improvement Checklist (2026-11-16)

**Read this FIRST after `BOT_KING_HANDOFF.md` in a new chat.** This is the authoritative **work inventory**, not a claim that every item is implemented or that GitHub CI means device PASS. Evidence and historical checks: `docs/BOT_KING_WORK_LOG.md`, `docs/BOT_KING_ORACLE_APP_CONTRACT_20261115.md`, `docs/BOT_KING_PREVIOUS_TWO_CHATS_STEP_BY_STEP_20261114_15.md`, `docs/BOT_KING_BATCH_4_FOUR_ENGINE_DESIGN.md` and `docs/B2_DHAN_OPTIONS_AUTO_REFRESH_MULTI_UNDERLYING_20261115.md`.

## 0. Status vocabulary and current baseline

- **REQUESTED** = user-approved goal. **CODE** = present in GitHub source. **CI** = GitHub offline test success for the specified commit. **ORACLE DEPLOYED** = actual production change backed by terminal evidence. **BROKER PROBED** = authenticated read-only request returned at that time, NOT exchange-live verification. **APK BUILT** = signed artifact checked. **DEVICE PASS/FAIL** = observed installed Android behavior. **PENDING** = missing evidence/implementation.
- Integration branch: `fix/botking-joint-audit-70-15-20261115`. Historical pre-journal release commit `fe2faa97c0158709593462b9293fca6f34257c1d`; always fetch **latest branch HEAD** before changing code.
- Source release `2.3.126`: **APK BUILT** — GitHub Actions `43753960172`, 809/809 offline tests, `versionName=2.3.126`, `versionCode=74101`, package `com.botking.bot_king`, signing verification and artifact `14177263980` PASS. Documentation-only commits after release are not new APK releases.
- Installed **DEVICE** reported `2.3.125`, with saved RELIANCE ₹1,339.70 and login auto-refresh not visibly occurring; **DEVICE FAIL / unresolved on installed version**. No v2.3.126 device PASS.
- Oracle S15 server route patch **ORACLE DEPLOYED**; S18 global-70/cross-list WatchlistStore patch **NOT PROVEN DEPLOYED**. User's authenticated S19 snapshot 51/51 and index batch 3/3 **BROKER PROBED**, freshness explicitly **unverified**.
- All real broker order submission **OFF** (`live_orders_enabled=false`); Paper Bot is simulation. Do not rotate Dhan tokens or overwrite Oracle-specific deployed `server.py` with repository `backend/server.py`.

## 1. Twelve grouped improvement areas

This canonical list consolidates the historical six-batch register, Batch 4 five-engine design, B1/B2/B3 work and Paper Bot; the 12 groups are **not 12 completed batches**. Each check is an explicit requested outcome, with the *strongest evidence level* available.

### G01 — Dhan-only identity, login, Oracle transport
- [x] G01.01 OAuth, Dhan API market-data token status, authenticated read-only server health — **BROKER PROBED** at earlier Oracle audit, not current phone session.
- [x] G01.02 HTTPS/Nginx/FastAPI service, protected endpoints reject unauthorized requests — **ORACLE audit**, S17 13/13 unauthenticated checks.
- [ ] G01.03 Verify current installed phone pairing/session and connection; existing pairing-key/manual setup is not a finished Keystore/PIN/biometric enrollment system — **PENDING**.
- [ ] G01.04 Dhan-only runtime must clamp restored Yahoo/Angel preferences, isolate legacy runtime modules and forbid silent fallbacks — **CODE partially gated, full isolation UNVERIFIED**.

### G02 — Watchlists, registry, equities and indices
- [x] G02.01 2,785 NSE equity registry records audited; authenticated instruments search exists; S15 selected-LTP batch + dynamic equity option guards — **ORACLE DEPLOYED route, functionality partially PROBED**.
- [x] G02.02 51 fixed-equity snapshot and NIFTY/BANKNIFTY/SENSEX index batch — **BROKER PROBED 51/51 and 3/3**, quote freshness unverified.
- [x] G02.03 Android five watchlists with 70 **unique equities total**, one symbol in one list — **CODE/CI**; historical original fixed scan 51 equities + 3 indexes remains separate.
- [ ] G02.04 Oracle WatchlistStore enforcing **global** 70 and cross-list uniqueness, preserving old JSON/rollback — **GitHub staged S18; ORACLE DEPLOY PENDING** (old deployed limit was 70 **per list**).
- [ ] G02.05 Real authenticated selected-equity 1–70 symbol batch/search, dynamic stock availability, end-to-end client display — **PENDING**.

### G03 — First login, refresh, cache and lifecycle
- [x] G03.01 Preserve last valid Dhan quotes on partial/error; independent index and equity batches, shared cooldown and serialized provider access — **CODE** with past CI; **DEVICE PENDING**.
- [x] G03.02 v2.3.126 login snapshot status and closed-market guarded first-load recovery, avoiding stale saved price as success — commits `5da68b3a`, `9d94169a`, `bd5c2212`, **CI 809/809 PASS**; **DEVICE PENDING**.
- [ ] G03.03 Every successful login open/closed loads one bounded verified-origin last-known equity/index snapshot + cached candles; user must see success/partial/error and collection age — **installed 2.3.125 DEVICE FAIL**, v2.3.126 **NOT DEVICE TESTED**.
- [ ] G03.04 During actual market session independently refresh equities/indexes at existing 60s throttles; background/resume, manual floor, 429 cooldown; closed session pauses repeated polling after first-load/recovery — **DEVICE acceptance PENDING**, do not casually change intervals.
- [ ] G03.05 Official NSE/BSE holidays/special sessions beyond weekdays and 09:15–15:30 IST — **PENDING**.

### G04 — Historical candles and chart integrity
- [x] G04.01 54-symbol historical 5m (51 equities + 3 indices), 10 default filter rows per symbol (540 evaluations), user-provided read-only Oracle run — **HISTORICAL TEST PASS only**, no exchange-live timestamps.
- [x] G04.02 Source/timeframe/candle timestamp validation, chart fallback, symbol isolation, newest-history handoff and paced history scheduling — **GitHub CODE/tests**.
- [ ] G04.03 Android 1m/5m/15m, 54 historical sources, blank WebView avoidance, candle freshness and cross-screen consistency — **DEVICE PENDING**.
- [ ] G04.04 Server-prepared persistent historical snapshots fully replace per-stock direct Dhan history fetching on Android — **migration PENDING**.

### G05 — Central Scanner filters and editing
- [x] G05.01 Actual current integration-branch cap: **15 saved movable active slots = 10 default + 5 extras**; remove to Available, add without exceeding cap, persist selection — **CODE/CI**. Historical intermediate B3 branch temporarily had a **10-slot** cap; do not promote that old status.
- [x] G05.02 Default technical filters, OI Support, OI Resistance, OI Profile, PCR, Max Pain visibility and fail-closed WAIT when source unavailable — **CODE/CI**, actual display needs phone check.
- [ ] G05.03 User-visible per-filter bullish/bearish result, Scanner page opens reliably, same narrow candle display and Add/Remove/Save works on Android — **DEVICE PENDING**.

### G06 — Super Five ranking and BSDS/Bullish–Bearish
- [x] G06.01 Historical technical candle votes, top-five candidate ranking, cached fallback with WAIT/stale labels, 51-equity watch universe — **CODE/CI**, not five validated live engines.
- [x] G06.02 Shared `vote_display` presentation and historical B/S evidence; last-known data cannot be promoted to live signal — **CODE/CI**.
- [ ] G06.03 Login/saved-candle bootstrap, reliable Top Five result on device, B/S parity with Watchlist/Scanner for same symbol/timeframe/bars, independent fast cached calculations — **DEVICE FAIL reported on v2.3.125 / PENDING**.
- [ ] G06.04 Three or more **independent source-verified** engines agree, with freshness/coverage/conflict rules before an actionable signal; never duplicate Technical+Candle vote — **PENDING for all-engine completion**.

### G07 — Dhan Options Chain / CE-PE / OI / PCR / Max Pain
- [x] G07.01 Mapped broker-listed expiry and read-only option chain, NIFTY ATM ±3 **listed strike levels** = seven levels, OI/PCR/Max Pain calculation and 422/429 guards — **CODE/partial older BROKER PROBE**, not all underlyings certified.
- [x] G07.02 Automatic load on selected symbol/expiry, sequential/queued requests, per-contract 422 retry suppression, symbol/expiry data isolation — **GitHub CODE/CI**.
- [ ] G07.03 NIFTY/BANKNIFTY/SENSEX and genuinely option-enabled equities (e.g. supported RELIANCE/HDFCBANK/ICICIBANK): expiry, cash security mapping, exchange segment, entitlement, lot size, CE/PE premium, volume and OI/ΔOI verification — **authenticated multi-underlying Oracle and phone PENDING**.
- [ ] G07.04 CE/PE strike rows and near-ATM premiums, premium change, OI support/resistance, OI profile, PCR, Max Pain, turnover estimate displayed in Scanner/Super Five with matching (symbol,expiry) cache — **partial CODE, comprehensive data provenance/display PENDING**.
- [ ] G07.05 Real directional Options money-flow score independently validated; OI ≠ actual cash flow; currently `signal_eligible=false` and freshness unverified — **PENDING / WAIT**.

### G08 — Futures, listed contracts, OI and volume
- [ ] G08.01 Broker-listed Futures instrument master/expiry/entitlement; authenticated read-only futures quote/OI/volume transport — **PENDING** (original design deferred to Batch 7).
- [ ] G08.02 OI change, price change, volume and explicit-unit turnover estimate — **PENDING**.
- [ ] G08.03 Long buildup, short buildup, short covering, long unwinding as *inferences*, not guaranteed money flow; separate Freshness/Confidence — **PENDING**.
- [ ] G08.04 Futures independent Bullish/Bearish evidence score accepted by Super Five only when verified — **PENDING / WAIT**.

### G09 — Five Engine / Four Factor shared assessment
- [x] G09.01 Contract separates **five UI evidence engines** (Technical, Candle, News, Futures, Options) from Oracle **four assessment factors** (News, Futures, Options, Candle) and **five assessment filters** (OI Support, OI Resistance, Max Pain, PCR, Candle Trend) — **schema CODE**, not 5/5 live signals.
- [x] G09.02 Oracle S09 27/27 static safety/schema checks, read-only Assessment, News fail-closed, order execution blocked — **STATIC/CONTRACT PASS only**.
- [ ] G09.03 Independent completed-bar Candle/Price Action engine (not duplicate technical votes); sourced News with publisher/time/issuer matching, negation and dedup; genuine per-factor numeric evidence scores — **PENDING**.
- [ ] G09.04 One symbol/timeframe/source/expiry timestamp-keyed normalized assessment reused by Dashboard, Scanner, Watchlist, Super Five and Trading Page; confidence and reasons displayed consistently — **CODE partially shared, full phone and feed PENDING**.
- [ ] G09.05 0–100 bullish/bearish *evidence strength*, never win probability; missing data = WAIT/N/A, not fake 0%; no implied real order — **source guard exists; complete inputs PENDING**.

### G10 — Paper Bot and future trading page
- [x] G10.01 Unified Options/Trading Center, 5 simulated Bot profiles, paper BUY/SELL/EXIT, manual mark, SL, target, trailing, partial 25/50/75, break-even, charges/net P&L and local paper timing — **GitHub CODE/CI, signed APK**, physical Android QA pending.
- [ ] G10.02 Profile switching, state persistence, crash/restart, portfolio totals, duplicate prevention, gaps/slippage, fees, simulated partial/exits and paper action timing on Android — **PENDING**.
- [ ] G10.03 Single durable transactional ledger across old Quick Paper/Chart Paper/new Bot, automatic **paper-only** serialized market ticks and safe multi-symbol bots — **PENDING**; existing Bot runs from manual marks, not unattended Dhan price feed.
- [ ] G10.04 Live Buy/Sell controls may be displayed together but separate risk/ledger/gateway, server-side auth and broker ACK/reconciliation, order idempotency and kill switch required before any future authorization — **LIVE ORDERS OFF**.

### G11 — Dashboard, settings, diagnostic clarity and usability
- [x] G11.01 Compact shared candle/vote components, fixed Dashboard index data paths, Health/Error Doctor, app version in UI, watchlist countdown, cached quote retention — **SOURCE WORK**, specific placement and device QA may differ.
- [ ] G11.02 Final navigation is **unresolved design revision**: some old Batch 4 plan says five bottom tabs; product discussion also preferred Dashboard/Watchlist/Settings only with Trading under Options. **Current source has six pages** (`Home, Options, Settings, Scanner, Watchlist, Chart`). Never claim any proposed navigation already shipped. Decide based on user-approved latest layout and regression tests.
- [ ] G11.03 Recovered vs active errors, 422/429 reason and expiry/symbol, stale-age, server stage, scan completion and watchlist first-login status legible on device — **PENDING**.
- [ ] G11.04 Lightweight cache, responsive foreground mode, avoid repeated 51-history/provider fanout, instrument result appearing promptly rather than blocking behind whole scan — **CODE partial; latency/bandwidth on phone UNVERIFIED**.

### G12 — End-to-end release, performance, continuity and security
- [x] G12.01 Earlier app-only signed releases through 2.3.126 with versionCode/check/signature + GitHub offline regression — **BUILD PASS, not Android acceptance**.
- [ ] G12.02 Record server→app quote RTT, freshness age, candle fetch, scan computation, paper callback, UI response separately, p50/p95/p99, errors and request volumes — **PENDING**. Local paper calculation milliseconds are NOT 1–3s full-path proof.
- [ ] G12.03 One-time enrollment with scoped/revocable Oracle session, Android Keystore PIN/biometric unlock (not broker PIN), safe recovery and minimal repeated pairing input — **long-term roadmap PENDING**.
- [ ] G12.04 Verify old-version upgrade without uninstall/clearing, versionName+versionCode, retained watchlists and bot profiles, release signing, closed/open session mobile QA — **PENDING**.
- [ ] G12.05 Oracle changes only after exact source diff and timestamped backups (including Dhan feed, Watchlist JSON), compile/tests, controlled restart, post-health and rollback; never print tokens, never enable orders — **ongoing process requirement**.

## 2. Corrections to historical journals — explicit supersession, no deletion

1. **10 vs 15 filters**: Some older B3 entries mention a 10-slot cap, but at the verified 2026-11-16 branch head `src/main.py` explicitly sets `MAX_ACTIVE_FILTERS=15`, ten default + five extra. The correct **current code** status is **15 total**. Ten default filters remain the historical calculation baseline. Android-device Add/Remove/Save acceptance remains separate.
2. **Futures data vs configured Futures UI**: Validators, engine slots and futures/four-factor schema exist, but a broker-verified read-only Futures acquisition feed, actual OI/volume and independently scored direction are **not established**. Don't mark Futures Engine PASS.
3. **News**: Headline counts/RSS context do not prove directional 0–100 sentiment or market impact; Oracle readiness `feed_not_configured` must stay WAIT.
4. **Options**: A successful NIFTY expiry/chain or PCR/Max Pain computation is not proof that every NSE stock is optionable, nor that full ATM ±3 CE/PE rows are verified, nor that Options directional score is actionable.
5. **54 historical candles**: Past read-only 54-symbol/540-filter run confirms one historical session and calculations, not today's exchange-live session or Android rendering.
6. **S18 server WatchlistStore**: Android source enforcing five lists/global-70 does **not** mean the Oracle production S18 patch was applied. Latest documented deployment is S15 selected-LTP/option guards only.
7. **APK and dates**: 2.3.126 Build #641 SUCCESS, whereas installed phone still reports 2.3.125; earlier entries saying 2.3.126 is yet to build are **superseded**. Build success cannot override phone FAIL.
8. **Navigation conflict**: Old six-tab runtime, five-tab UI plan and newer 3-tab request are competing revisions. Record conflict as **design pending**; avoid a unilateral breaking navigation rewrite.
9. **Paper/Live**: Paper Bot position simulation, manual marks and profile saving do not prove automatic multi-bot, broker fill or paper/live shared ledger. Oracle live trading remains OFF.
10. **Old backup discrepancy**: A previous expected `dhan_feed.py` timestamped backup was missing; a separate successful `server.py` backup is not proof of both files' backups.

## 3. New chat procedure and highest priority

1. Read **`BOT_KING_HANDOFF.md` → THIS FILE → `docs/BOT_KING_WORK_LOG.md`**; then relevant Oracle contract/Batch design. Confirm current branch HEAD, `pyproject.toml`, GitHub workflow result **before** claiming latest APK.
2. Treat evidence lanes separately: user device `2.3.125` **refresh FAIL**, GitHub `2.3.126` **BUILD PASS**, Oracle S15 **DEPLOYED**, S18 **NOT DEPLOYED**, five-engine live **PENDING**.
3. First fix/verify actual Android login equity/index snapshot and Watchlist `Quote check`, then historical candle/Scanner→Super Five B/S continuity; do not mark as fixed from 809 CI alone.
4. Next audit genuine Dhan mapped Option expiries/CE-PE/volume/OI/multiple underlyings and add real Futures/News inputs only with verified entitlement, rate limits and timestamps. Never invent signal percentages.
5. Finish S18 Oracle global-70 WatchlistStore with backed-up isolated test/deploy; preserve user records.
6. After work, append dated proof to `docs/BOT_KING_WORK_LOG.md`; update Handoff baseline. Never rewrite historical evidence or use a previous assistant summary as a CI/production proof.

**No live broker orders, no token rotation, no silent non-Dhan fallback.**
