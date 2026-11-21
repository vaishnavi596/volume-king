# BOT KING Clone — Day 2 Speed & Capacity Journal
Date: 2026-11-21 IST
Scope: active Clone/B2/B3 branch `pilot/v1-pure-original-clone-phone-20261120` only. V1 and superseded V2 remain untouched.
Status: JOURNAL/BASELINE REVIEW COMPLETE; END-TO-END CAPACITY ACCEPTANCE OPEN.

## Owner directive — first priority before further feature work
Audit the **building/structure** before promising faster refresh: Dhan acquisition time, Oracle single protected two-way request/response gateway, response/caching/queueing, mobile bandwidth/latency, candle + five actual filters, scanner/watchlist/dashboard UI responsiveness and limits. The app must be able to receive, process and render faster data reliably, not merely fetch it. Target: explore **2-second Watchlist visible updates** and possible **1-second data reaction**, only when validated fresh source data and real device/server measurements permit. Never treat a UI tick, data refresh, completed candle timeframe or provider request interval as the same thing.

## Prior implementation evidence (do not duplicate)
- Primary historical journal: `docs/BOT_KING_WORK_LOG.md`; gateway journal: `docs/CLONE_B2_SSK_GATEWAY_IMPLEMENTATION_20261120.md`. Reviewed on active branch 2026-11-21.
- Existing Watchlist visible tick is 2 seconds with signature-based, mounted-cell repaint; 3m signal reuse and shared cache previously implemented. This does **not** prove Dhan delivers new exchange-verified quotes or full 70-equity candles every 2 seconds.
- Dashboard/Scanner mounted-section data refresh replaces section content without full page remount. Final recorded exact-head offline regression GitHub Actions #44858767855: **1424 tests PASS**. Individual section contents can still be reconstructed; exact per-control delta diff and Android performance are pending.
- Existing Clone backend uses Dhan REST quotes, cached/controlled pacing and historical candle routes; prior source audit did **not** find a deployed Dhan WebSocket stream. A logical two-way pipe is a protected request+response gateway, not proof of one continuous physical stream or permission to trade.
- Oracle read-only observed both V1 and Clone services active; Clone Dhan sync timer had one-minute triggers and last checked oneshot exit code 0. Timer/process success is not proof of Dhan token validity or live quote timestamps.
- Historical evidence: NIFTY IDX_I/13, BANKNIFTY IDX_I/25, SENSEX BSE_I/51; SENSEX phone feed and index candles previously incomplete, scanner auto/manual/filter validations still need phone/live evidence. Do not change mappings based on guesswork.
- Dhan is the sole market-data source. Oracle is a secured transport/token/technical cache and provider pacing layer; Smart Controls, timeframes, filter evaluations and UI state remain app-owned. No Angel/Yahoo or extra source. Global 70 distinct equities, no duplicates, active-symbol adaptive workload, up to four phones. Five active filters (OI support/resistance, max pain, PCR, candle trend), sixth blank. Preserve last-good with HIST/STALE/WAIT markings, no fabricated LIVE.
- Prior work log documents a reasonable 60–90s full watchlist candle/evidence rotation under REST limits and no 70-wide history burst. This is compatible with a **2s visible cached-value repaint**, not a blanket guarantee of 2s fresh broker data for all symbols.
- Keep screen-specific timeframe settings; candle timeframe (1m/3m/5m etc.) must not be conflated with network polling/render frequency.

## Day-2 first task: read-only capacity audit / measurement contract
1. Map actual source paths: Dhan API → Oracle authenticated request/response routes and quota/retry → app shared cache/adapters → data computation → mounted view repaint. Identify whether requests are per symbol, batch, per screen, or per device; confirm single-flight, TTL, queues and failure isolation from CURRENT source (not guessed).
2. Add *measurement plan* for p50/p95/p99 and timeout/error counts per stage: provider response; Oracle wait/cache hit/miss; network RTT and payload bytes; app decode + 1m/3m/5m candle validation; filter evaluation; UI update duration, frame drops, CPU/memory, navigation/scroll latency. No credentials/token payload logged.
3. Stress with synthetic/local cache first, for **5, 20, 40, 70 unique equities and 1–4 phones**; classify 10/30/50 **Mbps** network profiles plus latency/loss. Do not infer Mbps solely from 'MB', and do not equate transport bandwidth with delivered live quote freshness.
4. Distinguish (A) visible cache-to-UI 2s cadence, (B) fresh quote arrival age, (C) completed candle availability, and (D) option/OI/PCR/max-pain evidence eligibility. Never label historical/stale broker data LIVE.
5. Proposed *budget to test, not factual measurements*: for 2000ms end-to-end, acquisition/gateway 650ms, mobile transfer 350ms, candle/filter compute 600ms, UI 400ms. Track actual distribution and bottleneck; use adaptive refresh/backpressure rather than uncontrolled concurrent provider requests.
6. Admission/acceptance: no provider 429 amplification, no per-repaint or per-phone Dhan requests, no scanning when Auto OFF or exchange closed outside explicit permitted manual cache path, no scroll/navigation hangs, no cross-timeframe cache contamination, no out-of-order result overwrite. Prove success/failure separately for quote/candle/options and 3 indices, then one consolidated device acceptance.

## Gate and work status
- COMPLETED: reviewed both existing repo journals and retrieved prior-chat implementation/constraints; reconciled 2s UI repaint vs genuine market-data age; created this scoped Day-2 task specification.
- NOT EXECUTED: live Dhan RTT throughput benchmarks, Android 1–4 device profiling, provider WebSocket deployment, production source modifications, Oracle deployment, APK build, market orders.
- NEXT: inspect only relevant latest current gateway/app source and existing performance tests, collect safe per-stage telemetry; then a single combined offline synthetic performance test; review findings before any throughput code change.
- Keep already passed 1424 offline tests as historical evidence only, not proof of current live mobile speed. Record every further test/result/fix under this Day-2 entry and link source commits/runs.
