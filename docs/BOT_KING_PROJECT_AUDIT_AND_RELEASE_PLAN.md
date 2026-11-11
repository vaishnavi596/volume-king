# BOT KING — Project Audit, Release Gates and Recovery Plan
Date: 2026-11-11
Repository: vaishnavi596/volume-king (main)
Last audited release source: 2.3.76, commit 2d3c696bb069fa890c5be4bd6358de0feb5f8229

## Goal
A stable Android market-data, chart, watchlist, 51-symbol scanner and paper-trading app, followed by controlled Dhan order integration. Live orders MUST remain disabled until explicitly verified and approved.

## Evidence (not claims of production readiness)
- Offline Regression Tests passed on 2d3c696 (GitHub Actions run 43050481317).
- APK Build run 43050481339 was in progress at audit time; APK installation and Android acceptance are unverified.
- Dhan Historical Candle Regression and Backend checks passed on dcfab37 (runs 43049240450 and 43049240430).
- Screenshot of installed v2.3.75: NIFTY quote unavailable / 3-day-old historical bullish label; BANKNIFTY and SENSEX instrument mapping not verified.
- Source includes a 51-symbol NSE equity watchlist and 3 configurable dashboard analysis slots (main branch), but these have not passed device acceptance.
- Source backend /dhan/intraday validates OHLC and returns no_candles_available for six empty arrays, without treating upstream failures as holidays.
- Current OAuth token status uses oauth_consent and renewal_supported=false. Legacy dhan_web RenewToken timer must not be enabled for OAuth tokens.
- src/secure_credentials.py is a secure-storage contract, not proof that Android Keystore integration is installed.
- src/main.py is approximately 3900 lines; high UI coupling raises regression risk.
- Paper engine exists; no verified end-to-end live order adapter. Never infer live trading readiness from paper UI.

## Release gates (in order)
G0: Source consistency. Keep pyproject.toml and src/main.py display version aligned; increment build/version code for every release; preserve package/signing identity for upgrade installs. Record exact commit, build run, artifact and signing fingerprint.
G1: Automated tests. Offline suite, backend tests, Dhan historical tests, navigation, persistence, quote freshness, 3-slot selection and no-order safety must pass. No known failures.
G2: APK/device smoke. Fresh install AND upgrade from prior signed version. Six tabs; every major button; save/restart; no crash; clear auth error; version visible.
G3: Dhan market data. Verify token provenance, entitlement, 51 equity batch, index mappings, timestamps, holiday/no-candles, rate limiting, 401/403 and 502. No fabricated quote freshness or fallback provider attribution.
G4: Chart/watchlist/scanner. Chart auto-load and timeframe isolation, 30-second quote poll when foreground, historical scan cadence, 51/51 scan accounting, 3 configurable slots, retry and source labels. Verify across two open-market sessions.
G5: Paper trading. Entry/exit/stop/target/P&L and persistence, reconnect and kill-switch tested with network failures; no real orders.
G6: Controlled Dhan trading. Separate order gateway, broker permissions, risk caps, duplicate-order idempotency, order-state reconciliation, manual confirmation, emergency stop, audit trail and explicit owner approval. Live orders default OFF.

## Priority defects / risks
P0: Live quote freshness and chart refresh are unverified on device.
P0: BANKNIFTY/SENSEX Dhan instrument IDs are unverified; do not guess.
P0: OAuth consent expiry requires reauthentication unless officially supported noninteractive flow exists.
P0: Keystore-backed app pairing-key persistence unverified.
P1: Main UI monolith and shared state cause regression risk.
P1: Offline tests alone do not prove Android controls function.
P1: Options OI/premium and news signals lack validated complete feed; avoid predictive accuracy claims.
P2: Additional AI/automation enhancements should wait for stable market data and measured paper results.

## Required test matrix
Each of Dashboard, Options, Settings, Scanner, Watchlist, Chart: navigation, data, loading, error, retry, refresh, persistence, restart, offline, reconnect.
Each market data component: symbol, provider, exchange, timestamp, latency, stale status, market-open/holiday state.
Each release: test result, APK run, versionCode, signing, update install, rollback artifact, acceptance evidence.

## Rollback / backup
- Tag the last successfully installed and tested commit and preserve its signed APK artifact securely.
- Before Oracle deployment, back up the current service unit, code and configuration without printing secrets. Never commit tokens, PINs or keys.
- Record the Oracle deployed commit separately from GitHub main; never assume they match.
- If a new build fails a gate, revert the change or isolate it on a feature branch, not by deleting working source.
- Keep a release ledger with PASS/FAIL/BLOCKED per gate and evidence URLs.

## Current immediate next actions
1. Check APK Build 43050481339 and inspect any failed job logs.
2. Add automated regression coverage for three dashboard slots, selection persistence and quote status.
3. Verify APK upgrade and all six pages on an Android device.
4. Validate Dhan index mappings via official instrument master, no guessed IDs.
5. Fix data timestamps/chart refresh and verify scanner before any live trading work.

This is an engineering audit based on repository, GitHub Actions and previously observed Oracle/mobile evidence, not a full live device/Oracle penetration or functional test.


## Final Master Roadmap Addendum — Approved 2026-11-11
This addendum consolidates the earlier mobile app audit/release plan with the user's approved Oracle-first centralized data architecture. Existing release gates G0–G6 above remain mandatory.

### Product architecture and source of truth
- Dhan authorized market feed (WebSocket where supported, otherwise bounded HTTP polling) -> Oracle centralized collector -> quote cache, candle store, scanner and analysis workers -> versioned snapshot/push API -> BOT KING Android.
- Mobile Dashboard, Watchlists, Charts, Scanner, Super Five, Options and paper trading consume the same timestamped Oracle snapshots; no duplicate per-screen direct Dhan polling.
- One authoritative instrument mapping per exchange/security ID. Verify NIFTY/BANKNIFTY and option instruments; never fabricate or infer unavailable mappings.
- Each quote/candle carries provider, exchange, instrument, event time, received time, source age and freshness state. Closed market, disconnected, rate limited and stale must be distinguishable.
- Oracle can maintain a last-known snapshot 24/7; it must not label closed-market or disconnected cached quotes as live.

### Data delivery and refresh targets (not promises or verified Dhan limits)
- Prefer Dhan streaming for subscribed live quotes when permitted. Aim for 1–3 second server-side update visibility where feasible; fallback HTTP 3–10 seconds only within official rate limits.
- Active mobile charts: push or 3–5 second snapshot refresh; active watchlists: 5–10 seconds; general app snapshot: 30 seconds; power saving: 60 seconds.
- Scanner calculations triggered by changed inputs/new candle; Super Five ranking target 15–30 seconds, avoiding full 51-symbol rescans on the handset.
- Candle persistence: incremental 1m, 5m, 15m, daily data with deduplication, gap checks, and no cross-timeframe contamination.
- Server-side shared request coordinator, backoff on 429, bounded concurrency, circuit breaker, deduplication, caching and instrumentation. Track feed-to-cache, cache-to-device and end-to-end latency percentiles.
- Faster quotes improve timeliness, not guaranteed trading accuracy. Backtesting and paper performance must validate signals.

### Android UX and central error handling
- Remove intrusive visible 'Scanning 1/51' progress from watchlist. Render last verified snapshot immediately; update silently when Oracle publishes new data.
- Show compact symbol row: LTP, percentage change, bullish/bearish signal where validated, freshness/last update, and per-symbol error if relevant.
- Dashboard central error monitor: Oracle connectivity, Dhan auth/entitlement, 429 cooldown, missing instruments, quote freshness, candle gaps, scanner job state and retry status.
- Charts auto-load on tap, preserve timeframe isolation, do not require tab-switch/retry to show initial data. Keep five persisted watchlists and three configurable dashboard slots.
- Keep all major buttons functional, fixed compact navigation, readable typography, consistent visual states, and accessibility. Do not clear valid prices on transient failures; mark stale with timestamps.

### Secure device login
- One-time device pairing over TLS. Store device-bound limited-scope credentials with Android Keystore; do not permanently store Oracle master pairing key, SSH key, Dhan access token or plaintext PIN in app.
- Six-digit PIN or supported biometrics unlock local secure session; device credentials are revocable, expiring and renewable with rotation. Rate-limit PIN attempts and provide secure recovery/re-pairing.
- Broker Dhan OAuth consent remains a separate requirement and may require explicit reauthorization when expired. App unlock does not bypass broker authentication.
- Upgrade/restart should retain valid device session; data clear/new device requires pairing. No live orders from unlocking the app.

### Ordered implementation plan
P0. Verify existing 2.3.79 signed APK, upgrade installation and real-device Dhan error evidence; do not assume GitHub success proves mobile operation.
P1. Audit every existing mobile/backend data fetch path, Oracle deployed commit, Dhan limits and provider fallback; produce measured baseline and rollback.
P2. Implement Oracle shared quote collector, freshness metadata, cache, bounded refresh and one snapshot API. Test 51 symbols and index mapping.
P3. Implement durable historical candles, incremental synchronization, scanner queue and Super Five server-side ranking.
P4. Migrate Android Dashboard, Watchlists, Charts, Scanner and Options to shared snapshots, remove scan progress, centralize errors, test foreground/background/reconnect.
P5. Implement device pairing, PIN/biometric unlock, session revocation and upgrade persistence.
P6. Validate option chain/OI/premium/news inputs with provider provenance; paper trading, backtesting and risk rules.
P7. Run G0–G5 release gates and two open-market acceptance sessions, preserve signed rollback APK; G6 live trading only after separate explicit approval.

### Delivery workflow and operational safety
- User approved a streamlined GitHub workflow: audit, edit, isolate unused legacy files, test, fix, build and verify without asking OK after every routine change.
- Do not claim continuous unattended execution when no active session/tool run exists. Report only evidenced PASS/FAIL/BLOCKED.
- Oracle deployment must be backed up and reversible; never print/commit keys or tokens. Provide small command groups or a reviewed idempotent deployment script, verify service and endpoints before/after.
- No order placement; live_orders_enabled remains false unless separate explicit owner approval and controlled G6 validation.
- Maintain release ledger with exact source commit, Oracle deployed revision, CI results, artifact, signing fingerprint, device install result and open-market data freshness.
