# BOT KING B3 — GitHub-only full error audit
Date: 2026-11-15
Branch: `fix/botking-2399-candle-retry-20261114`
Audited release: `2.3.121`, Build APK run `43701787694`, commit `c9fc31e0`.
Scope: GitHub source, workflow configuration and user-provided Android screenshots. **No Oracle SSH access, production deployment, new APK, or live Dhan account requests were performed.**

## CI / release findings
- Latest branch Build APK `43701787694`: SUCCESS, `751` unittest tests, pinned signing certificate verified, `versionName=2.3.121`, `versionCode=73601`.
- Recent offline run `43701626457`: SUCCESS. Older intermediate B2 failures do not constitute a failure of the final release commit.
- `.github/workflows/test-only.yml` covers this feature branch and runs compilation and unittest discovery on Python 3.12.
- `.github/workflows/backend-tests.yml` triggers automatically only for main and feature/dhan-market-data-audit, **not** this working branch. It can be dispatched manually. This creates a branch-specific backend CI coverage gap, despite the shared unittest suite passing in the APK workflow.
- GitHub green checks do **not** prove the currently running Oracle `/opt/bot-king-server/server.py` matches repository `backend/server.py` or that a Dhan account is entitled to each listed contract.

## Findings by priority

### P0 — Dhan Options HTTP 422 and repeated error events (device-confirmed, cause unverified)
- v2.3.121 screenshot: NIFTY 2026-11-17 shows a read-only ATM seven-strike window with CE premium, CE OI and volume. This is positive evidence of one populated Dhan option snapshot, with freshness still UNVERIFIED.
- ICICIBANK screenshot shows `expiry not set`, `Dhan request rejected (HTTP 422)`. That may mean no listed expiry/entitlement, incorrect mapping, or a deployed server with a different contract. The screenshot does not identify which endpoint produced 422.
- `src/server_feed.py` maps both `/dhan/option-expiries` and `/dhan/option-chain` HTTP 422 to the same generic string, losing endpoint and the server's specific safe reason.
- Unlike HTTP 429, HTTP 422 does not set a cooldown. `src/main.py:option_poll` periodically re-requests during market hours and the selection callback can schedule additional work. User screenshots recorded multiple `dhan_options: FeedError` entries close together. Need per-symbol/expiry negative caching, backoff, cancellation/de-duplication, and stable operator-readable status for 422.
- Limit repeated retries for the same rejected contract without suppressing a different selection or a manual reconnect after server repair.

### P0 — Oracle source/deployment parity NOT verified
- `backend/server.py` now includes authenticated POST `/dhan/option-expiries` and `/dhan/option-chain` supporting mapped `IDX_I/BSE_I/NSE_EQ` underlyings. `backend/dhan_feed.py` calls the Dhan read-only expiry-list and chain endpoints, paced >=3 seconds within a process.
- The working Oracle service has historically used a separate `/opt/bot-king-server/server.py`, not necessarily the same file. Confirm actual route list, code revisions, market token validity, segment/security ID mappings and response status **before any new production deployment**. Back up both server code and config before authorized changes; do not rotate existing pairing key.
- Dhan listing by cash `NSE_EQ` ID is not itself proof that a corresponding derivative exists or that the account is entitled. Do not synthesize expiry dates or premiums.

### P1 — Option-data scope and Scanner filter wiring
- `src/main.py` stores one mutable `dhan_option_metrics` dictionary and one Options selection (`chain_symbol.value`, `expiry.value`). Scanner's OI Support/Resistance/Profile/Max Pain detail is available only if the Scanner symbol matches the current Options selection and identical expiry. All 51 symbols cannot independently receive their own option context from this single slot.
- Introduce bounded, keyed `(symbol, expiry)` read-only cache and pass matching snapshots to Scanner, Dashboard and Super Five. Never propagate NIFTY OI to ICICIBANK or any unmapped symbol. Missing/old evidence => WAIT.
- Option Chain returned ATM rows and global PCR/Max Pain are informational; verified directional option-flow measurements are still absent, and `signal_eligible=false` is expected.

### P1 — Five-engine truthfulness vs historical technical ratio
- `src/five_engine.py:scanner_snapshot` populates ONLY the independent Technical engine. Candle, News, Futures and Options are deliberately WAIT if no separately verified evidence exists.
- `src/main.py:five_engine_chips` may show `T HIST B100/S0` from saved scanner votes while the adjacent historical Bullish/Bearish strip is another per-row calculation. This can produce different percentages for the same displayed symbol/timeframe. Label their bases and bar timestamps, or reuse one normalized historical calculation; never describe the ratio as trading success probability.
- A cached headline count is not directionally classified News evidence. Futures provider acquisition and exchange-freshness verification are absent; do not silently turn these slots ON.

### P1 — Index LTP missing in screenshots
- NIFTY previously showed an unverified cached LTP, while BANKNIFTY and SENSEX showed unavailable. Existing tests verify handling of a partial `/dhan/index-ltp-batch` response but cannot prove that the running Oracle has the right BSE_I/IDX_I contract and entitlement.
- Later check public/local authenticated index batch and single index LTP with known mapped IDs, preserve last valid quote without promoting it to live.

### P2 — Dhan-only provider isolation incomplete internally
- Production provider and broker dropdown options are limited to Dhan, but `src/main.py` still allows restored `prefs["source"]` equal to `Yahoo Finance` or `Broker API` and includes executable `get_yahoo`, Angel One login/history and cache paths.
- These are **not evidence of current cross-provider leakage**, but a Dhan-only release should clamp persisted/imported source to Dhan and isolate legacy code so it cannot be reached through a restored setting. Regression tests must assert legacy data cannot feed Dhan.
- Some hidden/unreachable captions and option-history functions still mention Angel One; archive behind non-production module boundary rather than blindly deleting historical recovery code.

### P2 — Chart and refresh robustness
- User previously observed an empty white Lightweight chart. Native fallback exists, but device recovery after a WebView ready callback needs an end-to-end test; CI has no graphical Android device verification.
- Dashboard mini charts reuse historical Dhan OHLC; independent candle freshness and timestamp status must remain clearly historical/unverified.

### P2 — UI and diagnostic quality
- Expiry field still labels itself `Expiry date (calendar preview)` even though broker-listed expiry is now loaded automatically.
- Generic help still says Refresh and `src/main.py` defines calendar-estimate expiry utilities for the earlier interface. Ensure no guessed exchange dates are displayed or treated as listed contracts.
- Error Doctor logs the same `dhan_options: FeedError` category without distinguishing `expirylist 422`, `optionchain 422`, `429`, transport or auth. Status should show symbol, selected expiry, endpoint family, safe error code, last attempt, next permitted retry, and whether cached rows are retained. Never log the pairing key or Dhan token.

## Next validation sequence (when the user has laptop)
1. Read-only Oracle systemd/Nginx/health/Dhan status, without printing any secrets. Compare active route implementations with the GitHub B2 contract, back up before any authorized write.
2. Authenticated Dhan option-expiries for NIFTY, BANKNIFTY, SENSEX, HDFCBANK, ICICIBANK, RELIANCE. Explicitly record `200/422/429/502` separately; use a paced request schedule. Do not assume every cash equity has listed options.
3. For symbols with broker-listed expiries, read one matching option-chain snapshot; validate PCR, Max Pain, CE/PE OI, expiry, ATM rows and read-only flags. Never invent missing fields or mark them live.
4. Verify three index LTP mappings and fallbacks. Separate cached price from exchange-verified live.
5. Only after server/API evidence, prepare a grouped GitHub B3 patch: 422 negative-cache/backoff, symbol-keyed option snapshot cache, status diagnostics, restored provider clamp and coverage tests; then signed APK release bump and device test.

## Audit verdict
**GitHub v2.3.121 builds and offline tests pass. End-to-end Dhan Options and all five engines DO NOT yet pass.** No production deployment, token change or new APK was performed in this audit.
