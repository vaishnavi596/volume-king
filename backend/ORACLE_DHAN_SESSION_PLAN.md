# Oracle Dhan credential and session implementation gate

Status: audit-only; not deployed. Branch: audit/oracle-dhan-credential-readiness.

## Existing behavior (backend/server.py)
- /dhan/start requires the BOTKING pairing key and server-side DHAN_CLIENT_ID, DHAN_API_KEY and DHAN_API_SECRET.
- /dhan/callback exchanges the consent token and stores access_token and expires_at in process memory.
- dhan_market_token() checks the in-memory expiry and falls back to /etc/bot-king/dhan-token.
- /dhan/status reports configuration/authentication, but does not verify Dhan market-data entitlement or live freshness.
- The server does not currently persist a consent token across restarts.
- The existing read-only token file may be stale; its existence is not proof of validity.

## Safe implementation sequence
1. Run backend/audit-oracle-dhan-readonly.sh on Oracle as root and review only its nonsecret output. Do not paste keys, token contents, or environment-file contents into chat.
2. Verify the actual systemd service User, its access to the token directory, file permissions and whether server.env supplies the consent-flow settings.
3. Check Dhan's current official token generation/renewal contract before adding any scheduler. Do not assume indefinite refresh or bypass interactive authorization.
4. If supported by Dhan, implement server-side renewal with atomic restrictive writes, explicit expiry, per-account locking, error states, and no secrets in responses or logs. Prefer a dedicated secret manager or systemd credentials; never commit credentials.
5. If unattended renewal is unsupported, implement expiry warnings and a one-action reauthorization flow; do not claim automatic renewal.
6. Add offline tests for expiry boundaries, timezone parsing, restart persistence, concurrent renewals, 401/403/429, callback rejection, permissions, and no token leakage.
7. Validate Oracle service health and read-only Dhan quote/candle freshness independently; do not enable trading orders.
8. Obtain explicit deployment approval after reviewing tests and rollback. Preserve production Android version and signing.

## Oracle validation observed 2026-11-09
- Owner ran read-only audit: token file present and readable by service user; restricted token and environment permissions; Dhan client ID, API key and secret configured; nginx syntax valid; local gateway health successful.
- Owner ran Dhan /v2/profile: HTTP 200, tokenValidity 10/11/2026 09:43 (provider-local timezone unverified), dataPlan Active, dataValidity 2026-12-05 20:54:01.0.
- Owner ran backend/check-dhan-token-expiry.py: DHAN_TOKEN_STATUS=accepted; DHAN_AUTO_RENEWAL=not_enabled.
- Do not assume the provider-local expiry string is UTC/IST until documented; do not run renewal on an unverified token type.

## Current limitations
- GitHub repository inspection does not establish the state of the running Oracle VM.
- Oracle results above were supplied by the owner from the live server; no production deployment or renewal was performed by the assistant.
- The audit script is intentionally read-only and cannot fix an expired token.
