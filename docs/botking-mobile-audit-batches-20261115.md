# BOT KING — Combined Mobile Audit (2026-11-15)

Reference: Android BOT KING v2.3.113 screenshots captured around 10:35–10:36 IST. This file is the batch-wise baseline. Do not mark a batch PASS based only on successful CI if mobile/Oracle validation is pending.

## Batch B1 — Dhan authentication and pairing header
- Observed: `dhan_status: UnicodeEncodeError`, `dhan_oauth_start: UnicodeEncodeError`.
- Implementation: reject non-ASCII/whitespace in the server pairing header **before** urllib; preserve the original key (do not rewrite/rotate it), display a safe actionable message.
- Regression: `test_dhan_pairing_ascii.py`.
- State: CODE COMMITTED; mobile verification pending. Never log keys or token values.

## Batch B2 — Equity Watchlist refresh
- Observed: countdown shows `Next 14s`, while `dhan_batch_after_connect`, `watchlist_dhan_batch`, `dhan_batch` report `FeedError`. Last valid values are retained; unverified/stale must not be presented as live.
- Implementation: shared 60-second equity snapshot clock (login/page entry/poller/resume), no repeated calls from UI redraw; explicit sanitized Oracle snapshot errors.
- Regression: `test_watch_countdown_incremental.py`, `test_snapshot_error_diagnostics.py`.
- State: CODE COMMITTED; **Oracle /v2/snapshot collection and phone live-data verification pending**. Do not claim server snapshots are valid based only on LTP endpoint success.

## Batch B3 — Scanner/WebView chart
- Observed: HDFCBANK 5m chart sometimes shows 216 saved historical candles (last 13 Nov 15:10 IST) and sometimes a blank white area on the same page.
- Implementation: avoid losing pending JS candle updates after dispatch failure; preserve symbol/timeframe isolation, and retry via local chart delivery rather than making an upstream request.
- Regression: `test_scanner_chart_delivery_retry.py`.
- State: CODE COMMITTED; actual Android blank-viewport recovery still needs testing.

## Batch B4 — Indices and signal validity
- Observed: NIFTY LTP shown; BANKNIFTY and SENSEX unavailable, despite historical Bullish/Bearish votes. Historical `HIST • NOT live` labels are correct; 54/54 analysis is not proof of 54 live quotes.
- Code guard: missing or malformed batch/fallback index quotes preserve the last valid Dhan price but downgrade `freshness` to `unverified` and set `provider_status=provider_data_unavailable` (commit `b2d3e3c`; regression `30a95e8`).
- State: CODE COMMITTED; Oracle `/dhan/index-ltp-batch` and missing-symbol fallback **live checks still pending**. Do not synthesize quotes from candles.

## Batch B5 — Compact UI and priority refresh
- Existing targets: scanner selected-symbol local check ~2s, Super Five changed-candle cache check ~10s, equity snapshot ~60s, chart/history on their own schedule.
- Keep UI updates independent from provider calls. Reduce redundant captions only when the diagnostics remain accessible.
- State: PARTIAL; Android responsiveness/scroll behavior requires device test.

## Batch B6 — Release gate
- Run complete offline tests on the *final combined head*; inspect exact failure logs, fix regressions, and rerun until success.
- Verify app versionName and Android versionCode both advance; permanent signing certificate and APK artifact must pass.
- Smoke-test Watchlist timer, actual Oracle snapshot availability, Dhan read-only status, Scanner cached 5m chart after navigation/resume, NIFTY/BANKNIFTY/SENSEX, and last-valid-price retention.
- **Keep live broker order placement disabled.** No silent Yahoo/Angel fallback.

## Source of truth and limitation
- Android screenshots are observational evidence, not proof of current Oracle status.
- Sundays/closed-market historical snapshots cannot demonstrate exchange-live updates.
- No production server modifications or credential rotations are authorized by this audit alone.


## Batch B7 (Priority 1) — Market-Aware One-Time Session Refresh (PLANNED)
**Requirement decided 2026-11-15. Do not report as implemented.**
- The global header prominently displays MARKET OPEN / MARKET CLOSED / MARKET HOLIDAY (specific holiday if known), with IST and the actual market-session calendar source. Allow special sessions (e.g. Muhurat Trading); do not assume every Sunday is permanently closed.
- Normal NSE equity and derivatives refresh cadence: 09:15–15:30 IST subject to official product-specific holidays and exceptional trading schedules. Calendar unknown => label unverified, never imply verified market-open status.
- When market is closed, suspend recurring *market-data* polling for equity quotes, scanner fast signals, Super Five, option-chain/premium, futures, and historical candles. Avoid useless 2s local loops as well as upstream requests.
- On a *new authenticated login or a new app session*, permit one bounded serialized data refresh when closed: validate connection and fetch most-recent permitted snapshot(s) once, reusing shared caches; never loop retries, hit 429 repeatedly, or trigger a 51-symbol historical burst. Further page navigation/resume within the same session reuses the result. An explicit user Refresh can request a separate controlled refresh, honoring cooldown.
- Display last actual source-data date/time and timezone per instrument and data type (spot LTP, futures, premium, candles, OI). Distinguish exchange timestamp from Oracle collection time, cache write time, last market date and unknown. Never invent a source time when unavailable.
- Keep last valid same-Dhan-provider data with CLOSED / HISTORICAL / UNVERIFIED labels, not live. Do not turn an absent timestamp into a fresh quote simply because the login request succeeded.
- On reopening: a single staggered data wake-up, priority order active read-only position/selected scanner, Super Five, then Watchlist; no duplicate polls. Keep server-side token/health monitoring separate from market-data polling; never enable live orders automatically.
- Regression: weekend, declared holiday, exceptional session, 09:14/09:15/15:29/15:30 boundaries, new login once, repeated navigation, app resume, manual refresh, 429 cooldown, previous-value preservation, per-source timestamp accuracy, Dhan-only provenance, active position read-only reconciliation.

## Batch B8 (Priority 2) — Dhan Option Chain NIFTY/BANKNIFTY/RELIANCE (PLANNED)
**Requirement decided 2026-11-15. Do not report as live/available yet.**
- DhanHQ supports option-chain by underlying instrument ID and segment including IDX_I (index) and NSE_EQ (equity); however BOT KING client currently hardcodes NIFTY in option_expiries and option_chain_metrics, and backend option-chain rejects non-IDX_I instruments. Confirm deployed Oracle code, entitlement and exchange-listed contracts before expanding.
- Underlyings: NIFTY, BANKNIFTY, RELIANCE. Fetch real broker-listed expiries rather than forecasting expiry dates or inventing strikes. Confirm backend route for /dhan/option-expiries exists in the deployed service before claiming support.
- Display actual CE/PE strike list, premiums (LTP), OI, volume, bid/ask and IV/Greeks where supplied; missing fields show —, not zero. Clearly show latest reliable data time if provider supplies it; otherwise UNVERIFIED.
- Keep futures prices and futures symbol/contract mapping a **separate verified read-only feed**. Do not infer futures from cash spot or historical candles. Futures follow the same session-aware pause and one-login-refresh rules.
- On OPEN: controlled, serialized snapshot reuse and rate-limit protection (Dhan option-chain documented minimum one unique request per three seconds); selected chain gets priority. No 2-second full-chain REST polling. On CLOSED/HOLIDAY: one bounded read-only check on login; no periodic chain, premium, OI or futures polling.
- Signal calculation is WAIT until source, valid instrument mapping, expiry, data freshness and eligibility are established. Display-only broker data is not a certified live trading signal. Live broker order placement remains OFF.
- Regression: each underlying, listed expiry, invalid/expired expiry, missing strikes/quotes, equity vs index segment IDs, 429, empty/partial provider response, holiday/weekend session, and cross-provider contamination.

## Dependency and release sequencing
B7 comes first (shared session/calendar + cache gate). B8 builds on that session gate. Then B1–B8 combined regression, Oracle read-only endpoint validation, Android screenshots/smoke testing, signing/versionName/versionCode checks, and one consolidated APK. Existing v2.3.113 is not evidence that B7 or B8 has been implemented.
References consulted: NSE 2026 holiday and regular trading hours page (https://www.nseindia.com/resources/exchange-communication-holidays), DhanHQ official SDK option-chain documentation (https://dhanhq.co/docs/DhanHQ-py/_option_chain/).


## v2.3.114 Android acceptance audit (15 Nov 2026, 11:07 IST) — NEW TEST EVIDENCE

Source: three user-supplied phone screenshots (Dashboard index strip and Home cards with five-engine expansion). These observations supersede older screenshots only for the specific fields visible; they do not establish a verified live Dhan market feed.

### M1 — Index availability (carry into B4)
- NIFTY LTP 25,144.30 appears; BANKNIFTY LTP 61,034.10 now appears, improving on v2.3.113 when BANKNIFTY was blank.
- SENSEX still shows em dash and `Dhan LTP unavailable`. Investigate Oracle deployed `/dhan/index-ltp-batch` returning `unavailable`, the BSE_I mapping and index fallback only with authorized read-only diagnostics. Do not fill with candle close or cross-provider values.
- All quotes show `exchange time unverified`; a collection-age indication (~1 minute) is **not** source/exchange verification. Sunday 15 Nov is closed, so there is no proof of live-session prices.

### M2 — Historical votes versus 5-engine eligibility (new B9 integration gate)
- RELIANCE 1,339.70, HDFCBANK 804.00 and ICICIBANK 1,583.60 LTPs appear with `time unverified`; do not mark quotes as exchange-live.
- Their 5m candle panels show 8 directional votes with Bullish 100% / Bearish 0%, explicitly tagged `HIST • NOT live`. This is an agreement ratio from historical filters, not a trade win probability or a verified live direction.
- Their five-engine cards show `WAIT • 0/5 verified`. Expanded ICICIBANK reports technical/candle/news/futures unavailable due to stale/missing proof and Options `Validated Dhan option trade flow unavailable`.
- Code audit: `five_engine.scanner_snapshot()` currently maps technical and candle analyses from the same scanner vote set to **one** technical slot to avoid double-counting. `snapshot_for_display()` enforces 300s maximum age and source/timestamp checks. News/Futures/Options have no active independent verified voting feed. Hence 0/5 is safe fail-closed output on closed-market day, not by itself an app crash.
- Required: distinguish `historical analysis available` and `live five-engine evidence unavailable` clearly in one compact component. Do not represent historical 100% as five-engine 100% or force 5/5.
- For B9, implement separate independently justified candle vs technical evidence, verified futures, option and sourced news inputs before coverage can grow. Require provenance, per-input timestamps, independent-counting and coherent freshness policies.

### M3 — UI presentation (carry into B5/B9)
- Open expansion lists five near-identical long stale reasons, consuming most of phone height. Replace with short, specific per-engine labels and one shared expandable diagnostic reason; keep exact details in Error Doctor.
- Preserve consistent Bullish/Bearish bar across Home, Watchlist, Scanner and Super Five; show last actual candle date and timeframe beside `HIST` when available.
- The overall signal summary must not override the `NO LIVE SIGNAL` gate when only historical votes exist.

### M4 — Regression and rollout order
- Current installed v2.3.114 APK is user-confirmed. No user screenshot yet validates scanner WebView stability, Watchlist countdown/end-to-end refresh, full 51/51 equity quote coverage, Options premiums or Futures LTP on this version.
- **Near-term combined correctness batch**: B4 SENSEX mapping/availability diagnosis + B5 compact five-engine and historical date display + B6 regression and real Android validation. Do not claim missing live provider data fixed without a read-only Oracle test.
- **Future functional batch**: B7 market/holiday one-time closed-session snapshot; B8 broker-listed NIFTY/BANKNIFTY/RELIANCE option chain and independently mapped futures; B9 company/index/sector/global news and independent five-engine fusion with OI/PCR/max-pain filters.
- Release gates: offline regression green on final commit; confirm actual Android versionName, versionCode, permanent keystore and uploaded signed artifact; retest mobile after installing. No automatic live orders; no Yahoo/Angel fallback.



## v2.3.114 Android System Health follow-up — 15 Nov 2026, 11:10 IST

Evidence: user screenshot of System Health and Error History on installed BOT KING v2.3.114. **Do not conflate the audit coverage's three symbol failures with the card's two grouped issue categories.**

### M5 — 3 isolated candle/filter audit failures (priority for next combined correctness batch)
- System Health: `54-symbol filters • 51 analyzed • 3 errors • 0 insufficient • 0 pending`. The three named errors are **HDFCBANK, HINDUNILVR, NTPC**. Earlier screenshot reported 54/54 with 0 errors; performance is intermittent, not proven permanently fixed.
- `scanner: FeedError` recorded 15 Nov 11:07:00 IST and again 11:09:54 IST. Exact upstream HTTP code, selected timeframe, affected-symbol identity and clean candle response are **not available in this screenshot**. Do not label these three as 429/422 or blame the network without sanitized endpoint/cooldown evidence.
- Audit `refresh_market`'s Dhan 5m history fetch/cache path for these three only, `remember_candle_failure`/`clear_scan_failure`, timestamp interval consistency, and scheduled retry/cooldown. Preserve previously valid Dhan LTP and historic candles; never classify an error as a live signal.
- Distinguish 54 configured instruments vs 51 successful analyses, and ensure the failed-symbol list and status are synchronized. Record sanitized per-symbol failure stage, endpoint, HTTP status (if available), cooldown and last successful candle date without leaking credentials; avoid unbounded retries.
- Confirm the Sunday/closed-market history scan's retry conditions do not repeatedly hammer the server when the snapshot cannot change. This will be consolidated with B7 market-session gating, not silently changed in the v2.3.114 APK.

### M6 — recovered index incident is not current failure
- Error History reports `RECOVERED • dhan_index_ltp_batch: FeedError` at 11:07:13 IST. Keep this in **history only**; it must not inflate active error count.
- SENSEX price remained unavailable in the prior v2.3.114 Dashboard screenshot, even though BANKNIFTY recovered. Treat BSE_I/SENSEX independently; a recovered batch error is not confirmation that all three indices have valid LTP.

### M7 — historical warning versus actual error
- `Chart warning: historical or unavailable data; not verified live` is shown as an issue. On a closed market and with legitimate last-valid historical candles, the label `HIST • NOT live` is an expected safeguard, not itself proof of a broken chart.
- Plan one compact *informational* historical/closed-market state, separately count active feed/validation problems; keep source freshness explicit. Investigate whether `component_status("market")` is truly STALE/UNAVAILABLE versus just HISTORICAL before downgrading a component.
- System Health groups two problems: (1) three named scan failures; (2) historical/unavailable chart warning. This does not mean only two instrument errors.

### M8 — mobile test and batch grouping
- **Next correctness/failure batch B4/B5/B6**: HDFCBANK/HINDUNILVR/NTPC candle error diagnosis + SENSEX missing-index checks + concise Health/5-engine UI + regression. Require sanitized runtime failure reasons and Android retest before claiming data-feed fix.
- **Then B7–B9**: holiday-aware one-time closed-session refresh, Dhan derivatives (options/futures) and independent news/five-engine integration. Do not overwrite the existing B7/B8 plan.
- No new APK is implied by this screenshot or audit document. v2.3.114 remains the last installed/tested release.


## FINAL JOINT BATCH — Closed-Market Stable Data and Session-Aware Refresh (approved scope, 2026-11-15)

**Observed on installed v2.3.114:** NIFTY, BANKNIFTY and SENSEX LTP may temporarily disappear and later reappear. User specifically confirms BANKNIFTY and SENSEX returned. Preserve that positive observation: the missing state is **intermittent**, not a proven permanent mapping failure. The underlying exchange timestamps are still unverified. The stock market is closed on Sunday 15 Nov 2026.

**Code audit findings on current branch:** `regular_hours()` only checks weekday and 09:15–15:30 IST, not the official exchange holiday/special-session calendar. `refresh_market()` already limits repeated closed-market historical 51-symbol scans per provider generation, and `visible_chart_poll()` / part of `option_poll()` already respect `regular_hours()`. But `dhan_quote_poll()` and `dhan_index_poll()` still periodically fetch quotes while closed. `refresh_after_resume()` and Watchlist page-entry also can cause closed-session requests. `scanner_fast_signal_loop()` keeps running 2-second local checks, and `super_five_minute_refresh()` keeps running local checks. `next_watch_refresh_label()` may show a misleading Next 60s countdown during closed session.

### Final sub-batches, to implement and test as one integrated change set

**F1 — One canonical exchange-session decision:** Introduce a shared IST session policy for each supported equity/derivatives segment: OPEN, CLOSED, HOLIDAY, SPECIAL_SESSION, and CALENDAR_UNVERIFIED as needed. Back with versioned official NSE/BSE holidays and validated special-session dates/hours; do not permanently hardcode weekday logic or assume all Sundays closed. On unknown calendar state fail conservatively and allow a controlled manual read-only check; display explicit uncertainty. Share the session decision across Dashboard, Watchlist, Scanner, Super Five, Options, Futures and Charts.

**F2 — Suspend periodic market requests while closed:** Gate all automatic equity snapshot (`dhan_quote_poll`), index LTP (`dhan_index_poll`), historical scans, chart, options/premium/OI, futures, Scanner fast local calculations, Super Five local calculations and resume/page-entry refresh behind the canonical market-session gate. Keep UI responsive and show saved values. Do not stop the separate low-frequency Oracle health/Dhan-token-expiry monitor. Do not alter existing live_orders_enabled=false.

**F3 — Exactly one bounded new-login/new-session snapshot:** On a NEW authenticated app/broker session while the market is closed, allow one serialized set of read-only quote snapshots and reusable cached candle/option/futures snapshots that the server actually supports. Record a session id + request-attempt outcome (not just a successful response), preventing infinite retries and duplicate calls on navigation, app resume, Watchlist selection, or Scanner reopening. Explicit manual Refresh is permitted with cooldown and server quota handling. Do not force a full 51-symbol historical scan unless explicitly requested and supported.

**F4 — Last-good value and data provenance:** On a missing/partial/invalid/HTTP error in Dhan equity or index batch, keep every valid last Dhan quote, and preserve displayed rates in an unmodified cache while showing LAST AVAILABLE / NOT LIVE. Never replace price with a dash during transient refresh. Keep `provider_status` or error indicator distinct from value, and do not overwrite independent LTP with historical chart OHLC. Show *actual source exchange timestamp* when provided, else “Exchange time unavailable”; distinguish Oracle collection age and display cache-write date. Do not mislabel “collected 1m ago” as a market price from today.

**F5 — Prominent stable UI state:** Put MARKET CLOSED / MARKET HOLIDAY (and known holiday name), timestamp and relevant exchange calendar in the top shared heading. Watchlist timer says `Market closed • auto-refresh paused` rather than `Next 14s`. Show last available quote/candle dates in IST separately. Candle Bullish/Bearish stays HIST • NOT live; five-engine fusion remains WAIT absent verified independent live evidence. No periodic full-page rebuild or flickering blank prices.

**F6 — Joint regression + device acceptance:** Add deterministic tests for weekday session boundaries, Sunday, NSE-only/BSE-only holidays, special sessions, calendar missing, two successful login sessions, one failed closed-login attempt, repeated app foreground/Watchlist navigation, explicit manual retry, Dhan API cooldown/429 and quote retention on missing SENSEX/BANKNIFTY. Verify no automatic closed-session Dhan calls, no background battery-hungry local 2s checks, no legacy Yahoo/Angel cross-feed, no active real orders. Run full offline test suite at final head; validate Oracle read-only outputs without changing production secrets; check signed APK versionName and advancing versionCode before creating one **joint** APK and requesting phone screenshot verification.

### Dependency with other agreed batches
- Complete F1–F6 as the shared session/retention foundation and treat it as the **final consolidated B7 market-time/holiday improvement**; do not independently introduce a second competing session scheduler.
- Then B8 Dhan options/futures and B9 independent news/five-engine filters **must consume the same F1 session policy and F4 last-good cache**, not introduce additional timers. The final product release for B7–B9 requires their independent broker-data validations, rather than claiming those sources live from historical price bars.
- **Status today: AUDITED / JOINT BATCH READY; NOT CODE-IMPLEMENTED OR MOBILE-VERIFIED.** v2.3.114 remains the latest confirmed installed/tested APK. No replacement APK has been built from this final joint-batch plan.


## F7 — Scanner Symbol-Switch White/Blank Chart Recovery (ADDED 2026-11-15)
- User reproducible Android v2.3.114 issue: NIFTY chart shows correctly, changing Scanner selection to HDFCBANK/BANKNIFTY or another symbol leaves the lightweight chart viewport blank white. Visiting another page and returning mounts the chart and shows the candles; repeating the symbol switch reproduces failure.
- Root-cause candidate from source: the chart WebView is recreated on symbol/timeframe context change, yet `about:blank` Android `on_page_ended` callbacks are not guaranteed. Previously local 2-second chart loop set `tv_booted` only after attachment or callback. A current-symbol view could remain uninitialized/unready until navigation.
- Fix committed: start chart widget initialization after the selected Scanner page is actually attached by `page.update()`; clear previous symbol JS state, candle history, delivery identity and retry counter on context change. If the WebView fails to reach JS-ready within six seconds, retry the **current context's saved candles** at most twice by local HTML reload. Do not issue extra Dhan historical requests on these retries or reuse another symbol/timeframe's candles.
- Commits: `2487368` implementation; `49bcdd3` regression guard in `tests/test_scanner_chart_delivery_retry.py`.
- Verification gate: full offline regression must pass; user must switch NIFTY→HDFCBANK→BANKNIFTY→RELIANCE without leaving Scanner, verify correctly labelled chart and latest saved candle dates on each, ensure no old symbol candle flicker and no white blank canvas. Confirm same after Android app background/resume and TradingView/BOT KING chart provider selection. Treat **MOBILE PASS as pending** until observed.
- This is now part of the combined F1–F7 release gate, not an unrelated second APK. B7 market-session and B8/B9 future evidence-data gates remain separately scoped.


### F1–F7 implementation checkpoint (2026-11-15)
- Partial closed-session gating implemented in `src/main.py`: regular-hours check now suspends *automatic* equity and index LTP polling, Watchlist page-entry refresh and resume quote/history fetch while outside the existing weekday 09:15–15:30 session. Watchlist countdown says `Market closed • auto-refresh paused`.
- Super Five repeated local cache calculation pauses outside regular hours. Scanner skips costly off-hours repeated shared analysis but keeps local selected-chart render/recovery available while the Scanner page is open. This preserves F7 chart switching even on closed days.
- Commits `54c3ab3`, `321ea2c`, `b614ab1`, and legacy assertion updates `e6664a8`, `451776f`, `48505ca`. Offline regression run 43682835716 PASS.
- **Not yet implemented:** official NSE/BSE holiday and special-session calendar, global heading with correct holiday name, strict per-login single closed-session data-check guard, and broker-verified source exchange timestamps. These require separate integration and live device/Oracle validation. Do not declare F1–F7 complete or create a final combined APK based solely on this checkpoint.


## F8 — Central Assessment Filter 10-slot editor (2026-11-15; CODE COMMITTED)
- Regression from user phone test: OI Support/OI Resistance/Max Pain disappeared from the active defaults and pressing Add did nothing. Removing 3 of 10 did not move those filters into the Add/available list.
- Root cause: old load sanitization explicitly discarded every `OPTION_FILTERS` entry; Add and checkbox callbacks rejected OI filters even as WAIT-only configuration; Settings permanently rendered `DEFAULT_FILTERS` instead of the actual active selection. Because default 10 were full there was no explicit capacity behavior.
- New policy: exactly 10 maximum active slots, any of the supported filters may occupy them, unused default and option filters move to a visible Available list immediately; removal and Add update the same saved `scanner_filters` preference. "Restore default 10" restores the original core set. Filters selected without verified broker chain evidence remain WAIT, never counted as bullish/bearish or live. A full 10/10 shows an explicit slot-full reason.
- Code commits: `de624e6` selection/persistence; `3b2fcf9` dynamic UI; tests `e010116`, `f2b22d3`; legacy regression updates `667f256`, `7443525`. Latest offline regression 43683460026 SUCCESS.
- Manual acceptance required: remove 3 default filters, find all 3 under Available, select and Add OI Support/OI Resistance/Max Pain, check 10/10, reopen app and confirm persistence, verify OI evidence WAIT; Reset Defaults and verify all original ten return. No random phantom 11th filter. Check Scanner, Watchlist and Super Five share those settings.

### Integrated testing/release checkpoint
- F7 chart symbol-switch local recovery and the early F1–F2 regular-session polling guards are in this branch as well as F8. They have passed offline code regression but **NOT been verified on Android**.
- The full NSE/BSE holiday/special-session calendar, global Market Closed heading, strict new-login one-time closed-session snapshot, separate verified futures/option/news feeds (B8/B9), and actual exchange timestamps are **not complete**. Do not advertise those as included in this checkpoint APK.
