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

