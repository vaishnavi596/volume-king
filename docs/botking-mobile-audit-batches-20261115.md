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
