# BOT KING Dhan integration audit (2026-11-07)

## Confirmed by owner on Oracle
- /health returned status ok, protocol 1, live_orders_enabled false.
- Dhan /v2/profile returned HTTP 200 with token read from root-owned /etc/bot-king/dhan-token.
- Dhan /v2/marketfeed/ltp returned HTTP 200 for IDX_I security ID 13 (NIFTY), last_price 25030.35 at the time of the request.
- These checks do not prove quote freshness, live market hours, historical candles, option data or Android connectivity.

## Draft branch changes
- Paired POST /dhan/ltp, read-only and limited to verified NIFTY mapping.
- Root-owned token file read on each request; no credentials committed to GitHub or packaged in APK.
- Existing Angel One /v1 login and history routes untouched.
- Offline adapter tests added under tests/ and backend/.

## Blockers before deployment or APK
1. GitHub backend/server.py imports market_feed, but backend/market_feed.py is not in main. Oracle has /opt/bot-king-server/market_feed.py. Establish canonical packaging and deployment.
2. Android src/main.py only selects Yahoo Finance or Broker API (Angel One). It requires a separate Dhan provider integration, not just an LTP endpoint.
3. Scanner and charts require verified historical candles and timestamps. LTP must not be fabricated into candles or assigned a fresh timestamp without upstream proof.
4. Map NIFTY/other instruments through Dhan instrument master; do not guess security IDs.
5. Run offline regression tests and live server checks without printing credentials. Test 401/403/429/5xx, malformed JSON, stale/closed-market behavior, and pairing-key rejection.
6. Confirm package ID, signing fingerprint and versionCode relative to installed APK before update installation.
7. The GitHub Actions APK build workflow is workflow_dispatch/manual; no build has been launched as part of this draft.

Do not merge or deploy until blockers are resolved. Keep live order execution disabled.

## Added in this iteration
- Added paired POST /dhan/intraday with a verified NIFTY security-ID mapping and a bounded 5-day request window.
- Validates OHLC array shapes, numerical values, timestamps, order, and high/low consistency before returning candles.
- Returns historical_unverified rather than claiming live data.
- The upstream /charts/intraday response has NOT yet been verified against the user's Oracle Dhan credentials; do not connect the Android scanner to this route until a real response and tests pass.
- The Oracle service process may lack permission to read root-owned /etc/bot-king/dhan-token (mode 0600). Confirm service User and use systemd credentials or a dedicated restrictive group; do not make token world-readable.

## Token renewal review (2026-11-10; source audit, not deployed)
Official reference: https://dhanhq.co/docs/v2/authentication/

- Dhan Web-generated tokens: GET https://api.dhan.co/v2/RenewToken with access-token and dhanClientId headers. Renewal invalidates the old token, works only while it remains active, and issues another 24-hour token. Implement atomic credential replacement and proactive scheduling only for this confirmed token origin.
- OAuth app-key/secret consent tokens: the official RenewToken documentation explicitly limits this endpoint to Dhan Web-generated tokens. Do NOT silently apply it to the current /dhan/callback OAuth session. Reauthentication/consent is required unless Dhan explicitly documents a supported noninteractive renewal flow for that token type.
- Current backend/server.py stores OAuth session tokens only in process memory, so restart loses them. It may fall back to /etc/bot-king/dhan-token without confirming freshness; /dhan/status reports configured state, not verified live authorization.
- Prior to code/deployment: determine token provenance, validate actual expiry/profile and timezone, ensure secret storage readable only by the service, design atomic rotation with rollback, distinguish expired/unauthorized from transport errors, and test restart/recovery without logging secrets.
- Never store PIN/TOTP seed in GitHub or APK. Do not automate interactive 2FA circumvention. No live order execution, server deployment, or APK build was performed by this audit.
