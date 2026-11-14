# BOT KING — Batch 4 audit / tomorrow handoff (2026-11-14)

**Status: OPEN / NOT PASS. Do not start Batch 5.** Last installed/tested APK: **2.3.108**. Preserve existing working features; no new APK until fixes and regression audit.

## Ground truth — user's mobile report (31 checks)
- PASS 17: app opens, header version and safe area, Dhan/Oracle connection, three index prices, five watchlists, 51/51 LTP, automatic watchlist refresh, page navigation, last-valid-price retention, scanner opens, symbol selection, scanner refresh, five-engine display, option page opens, horizontal table scroll, no screen overflow.
- FAIL 8: 5m candle/history freshness, stale/live signal presentation, CE/PE premium, CE/PE OI, CE/PE volume, PCR, Max Pain, paper BUY/SELL separation/safety behavior.
- NOT TESTED 6: expiry list, selected refresh, seven listed strikes, unverified signal WAIT, new navigation KeyError, new watchlist AssertionError.

## Evidence from nine screenshots (2026-11-14 23:28–23:34 IST)
1. Scanner: `DATA UNAVAILABLE — Scanner: Data request failed (KeyError)` repeatedly. Diagnostics `scanner: KeyError` at 23:28:07, 23:29:21, :22, :25, :36, :41. Scanner **navigation itself works**; failure is during data processing. Find actual missing key with safe diagnostics (no secrets/URLs).
2. Scanner 5m/7d shows 299 bars, last candle **2026-11-13 15:25 IST**, completed candles stale. A separate combined analysis displays **2026-11-08 14:55**, six days old. Historical 7 bullish / 0 bearish filter votes appear green; **combined result WAIT**, 0/5 verified engines; do not mislabel historical votes as live BUY/SELL.
3. Option page selected NIFTY, Nearest, calendar-preview 2026-11-17. Option strike card: `Dhan option strikes unavailable`, `Option chain not connected`, `Dhan option metrics not loaded`, `ATM window: Not yet verified`. Scanner OI context: `no matching Dhan expiry snapshot`. Need verify expiry refresh -> Dhan chain -> seven-strike UI -> CE/PE premiums/OI/volume -> PCR/Max Pain and accurate data provenance. Paper buttons visible, but no proof of executed orders; live orders must remain OFF.
4. Diagnostics at 23:23:53 and :58 `watchlist_dhan_batch: FeedError`, 23:24:18 `dhan_index_ltp_batch: FeedError`; app also shows `No active errors reported`. Investigate transient gateway/feed failures separately from scanner KeyError; do not break last-valid-price retention.
5. Header v2.3.108, status-bar spacing and bottom navigation appear correct. No visible overflow. News snippets are old (Nov 8); news/futures five-engine work is explicitly deferred, not Batch 5 now.

## Technical audit starting points
- `src/main.py`: `scan_market()` (KeyError; `timeframe_spec(interval)["annual_bars"]`, `analyze_current`, `advanced["reason"]`, `advanced["bias"]`, `advanced["votes"]` etc.); `log_error()` currently records exception class only. Add narrow, sanitized missing-key diagnostics and regression test for the precise crash.
- `refresh_selected_options()`, `option_chain_preview()`, `option_metrics()`, `scanner_option_context()`: compare selected expiry to actual broker-listed expiry, no simulated CE/PE feed presented as live.
- `analyze_current()`, `scan_shared`, fusion/combined card: historical candle votes must be labeled historical, and stale/unverified data must never issue a live trade signal.
- Dhan Oracle option API had previously returned 18 expiries, NIFTY PCR ~0.83049, Max Pain 25100, seven strikes [25000,25050,25100,25150,25200,25250,25300], but freshness unverified/signal_eligible false. This is **prior server evidence, not proof of current app availability**.
- Prior 2.3.108 release CI 666/666 PASS, versionCode 72301, signing verified. These tests did not reproduce the phone's scanner KeyError or option display failure.

## Next work order
1. Reproduce scanner KeyError from actual runtime path and add targeted regression; guard missing fields without hiding faults.
2. Trace 5m candle source/cache freshness, ensure clear historical labeling and fail-closed signal safety.
3. Trace Dhan option expiry/chain/metrics/ATM seven-strike app integration and missing CE/PE/OI/volume, PCR, Max Pain. Keep broker throttling and live orders OFF.
4. Audit FeedError and diagnostic health consistency; preserve 51/51 last-known prices.
5. Run complete offline regression and review changes; only then bump APK version and build/sign/test. No Batch 5 until Batch 4 mobile acceptance.

**Scope freeze:** Do not start News/Futures future filter expansion or Batch 5. No Oracle production changes without backup. Do not generate images.
