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

## Verified Dhan authentication contract (official docs, checked 2026-11-09)
- Source: https://dhanhq.co/docs/v2/authentication/
- Web-generated access tokens are valid for 24 hours. GET /v2/RenewToken accepts only an active **web-generated** token; the previous token becomes invalid when renewed. Never probe this endpoint against the production token to discover its origin.
- API key/secret consent flow has generate-consent, interactive browser login, then consumeApp-consent; it is not documented as eligible for RenewToken.
- Dhan also documents POST /app/generateAccessToken with Dhan client ID, PIN and TOTP, when TOTP is enabled. This requires separate sensitive credentials and explicit opt-in; do not silently collect PIN/TOTP seeds or use the flow without security review.
- Source: https://dhan.co/support/platforms/dhanhq-api/what-is-the-maximum-validity-of-an-api-access-token-in-dhan-apis/
- Dhan support describes API key/secret-based token generation as automatable, but the consent-flow docs still require browser verification. Verify which flow is authorized for this account before claiming unattended renewal.
- Current production token origin is unknown. No token replacement or renewal attempt is authorized by these read-only checks.
- Avoid printing client ID, PIN, TOTP, API secret, JWT, consent token or raw Dhan response bodies in diagnostics.

## Current limitations
- GitHub repository inspection does not establish the state of the running Oracle VM.
- Oracle results above were supplied by the owner from the live server; no production deployment or renewal was performed by the assistant.
- The audit script is intentionally read-only and cannot fix an expired token.

## Read-only monitor hardening (2026-11-09)
- The optional `DHAN_PROFILE_TIMEZONE` must only be set after verifying Dhan's clock; otherwise output remains provider-local and does not compute a misleading countdown.
- Once configured, the monitor now differentiates healthy (>6 hours), warning (0–6 hours), and expired (at or past expiry); an expired state returns exit 2. This is a **local clock assessment**, not a Dhan renewal or live-quote validation.
- Offline tests cover expiry boundaries, India versus UTC clock interpretation, invalid timezone, missing token and date parsing.
- No systemd timer, notification destination, token write, service restart, production deployment or unattended renewal is enabled by these branch changes.
