# BOT KING — Dhan + Oracle + Yahoo final pre-build audit (2026-11-06)

## Decision and build gate
**DO NOT BUILD APK until owner explicitly authorizes.** Do not run or restart the Oracle production service during code preparation. Keep existing Android package `com.botking.bot_king` and permanent release signing workflow/key unchanged. Keep Angel One available as an optional legacy broker, not a dependency for the primary workflow.

## Primary architecture
- Yahoo Finance: indicative underlying quotes and candles; label source, exchange timestamp, retrieval timestamp, stale/unavailable status. Never treat as guaranteed exchange-grade or as verified option premium/OI.
- Dhan: primary authenticated broker/market-data provider when owner later creates credentials. Access and market-data entitlement must be independently checked. Paid data cancellation may remove endpoints.
- Oracle: owner-operated HTTPS gateway with provider-specific adapters, bounded sessions, rate limiting, health, safe errors, and credential isolation. Do not blend incompatible timestamps, instruments or contracts into one price.
- Angel One: preserve existing read-only adapter and UI for optional future use; no forced login for scanner/dashboard.

## Verified gaps in current main branch
1. `src/main.py` currently offers Yahoo Finance / Broker API as a single source toggle; Broker API data flow is Angel One-specific. Dhan appears in the broker dropdown but the Connect handler explicitly reports that Dhan integration is not connected.
2. `backend/server.py` constructs `AngelFeed` by default, and existing `/v1/login`, history and option routes target that adapter. `src/server_feed.py` is Angel-specific.
3. Credential fields are intentionally cleared/not persisted. A saved client ID alone is not an authenticated broker session. Do not store Dhan tokens in ordinary preference JSON or backups.
4. Current server bearer session is capped at 8 hours total and 2 hours idle; this is not a Dhan token refresh mechanism. Never claim Dhan can remain authenticated beyond the provider token validity.
5. Chart indicators/overlays, chart-touch drawing, and verified levels are explicitly marked incomplete in `src/main.py`. UI handler presence alone does not prove phone functionality.
6. Scanner `src/scanner_engine.py` analyzes candles; verified CE/PE premiums, expiry, OI, Greeks and contract mapping require entitled broker data. Never invent premiums or confidence percentages.

## Implementation sequence before next build
1. Introduce a Dhan adapter behind a broker-neutral read-only interface; validate provider API specifications, allowed endpoints, subscription entitlement, expiry and rate limits. No credential or trading endpoint in tests.
2. Add versioned provider-specific Oracle routes and tests without changing existing Angel One route semantics. Require authentication, redact credentials, implement explicit status: NOT_CONFIGURED / CONNECTING / CONNECTED / EXPIRED / UNAVAILABLE / RATE_LIMITED.
3. Use server-side encrypted credential storage only if approved and implemented with OS-protected key management; otherwise request new token at expiry. On Android, use platform-backed secure storage, not Flet preference JSON; do not pretend persistence exists before verified.
4. Add Dhan setup, validate, disconnect and session-status UI. No secrets in backup, screenshots, diagnostics, logs or GitHub. No token required to render any page.
5. Implement provenance-aware Yahoo+Dhan selection and quality gates. Scanner may give underlying bullish/bearish *analysis* from valid candles; options recommendations only with verified current contract data and risk parameters. If absent show WAIT/UNAVAILABLE.
6. Preserve 5 watchlists, navigation, chart, scanner, paper trading and Angel One; audit all buttons and regression tests, including offline/expired-token/restart cases. Real orders remain disabled until separately approved and tested.
7. Validate backend in staging, backup Oracle config, provide rollback and migration steps; do not deploy or restart live server without owner approval.
8. Run syntax, offline unit/integration/UI tests and static audit. After explicit owner approval only, build APK using pinned permanent signing, verify package/version/cert SHA256 and perform phone installation tests.

## Acceptance tests
- App opens without Dhan credentials and Yahoo mode works with honest source/age labels.
- After Dhan token is added, connection status is verified against provider, not inferred from text fields.
- Closing/reopening app preserves non-secret preferences; session resume succeeds only while valid and securely stored. Expiry triggers explicit reconnect, never fake live status.
- Oracle restart or Dhan outage does not crash dashboard/scanner; Angel One remains optional.
- Underlying scan and option premium/strike/expiry/OI each carry source and timestamps; mismatches are rejected.
- All visible controls either function or are clearly disabled/explained; no silent placeholder buttons.
- All offline tests pass; Android device UI and update behavior are separately confirmed.
