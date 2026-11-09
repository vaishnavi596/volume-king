# BOT KING Oracle Dhan consent persistence: deployment and rollback gate

**Status: NOT DEPLOYED.** This document is preparation only. Never paste tokens, API keys, PINs, TOTP seeds or environment-file contents into tickets, GitHub or chat.

## What this change does — and does not do
- The audit-branch gateway has an opt-in `DHAN_PERSIST_CONSENT_TOKEN=1` switch. With the switch absent or set to 0, the existing callback remains memory-only.
- When opted in, a matching Dhan client ID, nonempty token and **timezone-aware future** `expiryTime` are required before atomic token-file replacement. Ambiguous timezone is rejected, not guessed.
- No unattended renewal, timer, PIN/TOTP automation, live trading, token rotation or API call is introduced.
- The callback's response indicates consent completion, **not** verified live quotes or candles.
- Existing provisioned token file may be expired. File existence is not authentication proof.

## Production prerequisites (read-only first)
1. Get explicit owner approval for a separately scheduled deployment and rollback window. Do not enable this switch as part of a routine app update.
2. Confirm production's exact service User and Group via `systemctl show bot-king.service -p User -p Group`; determine the effective user when User is empty.
3. On Oracle, run `python3 /opt/bot-king-server/check_dhan_persistence_readiness.py` **as the service user** after staging the new script. The script does not read token contents, write files, call Dhan or restart services. Do not assume a root-run result applies to a nonroot service.
4. Inspect *metadata only* for `/etc/bot-king`, `/etc/bot-king/dhan-token`, and `/etc/bot-king/server.env`. Do not print their contents. In particular, a root-owned token file cannot be atomically replaced by a different service user under the present fail-closed design.
5. Verify a restricted private directory and service-user write/traverse permission. Resolve ownership only after reviewing systemd sandboxing and existing backup/restore procedures; do **not** automatically `chown` production credentials.
6. Verify Dhan's exact consent callback expiry format in a nonproduction flow. An offset-free `expiryTime` will be rejected if persistence is enabled; do not assume Asia/Kolkata.
7. Confirm service restart behavior, multi-worker locking, health endpoint, and a read-only Dhan profile/market-data check without exposing credentials.
8. Review whether a token's expiry should be stored alongside the file: the current fallback file reader does not carry a persisted expiry. Until this is addressed, do not claim restart-safe **validity** based only on restart-safe **storage**.

## Dry-run validation
- Keep `DHAN_PERSIST_CONSENT_TOKEN=0` while running existing callback regression tests.
- Run GitHub offline CI for `backend/server.py`, `dhan_session_bridge.py`, consent validation, storage and readiness checks.
- Verify that invalid account, missing expiry, ambiguous timezone, expired token, symlink, wrong owner, broad permissions and unwritable directory never overwrite a prior token.
- Validate that a simulated restart can read the saved token and that no token values appear in logs or HTTP error responses.
- Do not test `GET /v2/RenewToken` with the production token merely to discover whether it is eligible; renewal invalidates the previous token if successful.

## Deployment only after explicit approval
1. Record current commit, configuration names (not values), service health and file metadata; arrange encrypted, restricted backup of the existing credential file outside GitHub.
2. Deploy reviewed gateway and helper files, leave the opt-in switch **off**, restart only during the approved window and verify unchanged existing behavior.
3. If the service-user filesystem gate and consent expiry format both pass, separately approve enabling the opt-in and one interactive Dhan login. Verify new token through Dhan read-only API; do not place orders.
4. Check gateway health, Dhan account match, token expiry, quote/candle freshness, file mode/owner and restart survival.
5. If any check fails, turn opt-in **off**, restore prior code/config and **only if necessary and authorized** restore the encrypted credential backup. A token revoked by Dhan cannot be made valid by restoring its file.

## Rollback triggers
- Login callback fails on a valid consent because of timestamp ambiguity or storage permissions.
- Dhan market-data access degrades or account ID differs.
- Credentials appear in any log, HTTP response or CI output.
- Service cannot restart, credential file owner changes unexpectedly or stored token fails Dhan profile validation.

## Approval boundary
All audit-branch commits and offline tests are nonproduction. Production file changes, token replacement, service restart, scheduler activation and any live order require separate explicit authorization.

## Opt-in read-only gateway status verification (audit branch only)
- `DHAN_VERIFY_PERSISTED_SESSION=1` makes `GET /dhan/status` call the Dhan profile endpoint to check the **file-backed** token. The default is off and reports `persisted_session_verification=not_checked`.
- Result is `verified` only when the Dhan profile account matches and the expiry is in the future with a verified timezone. Any failure reports `unverified`, without exposing secrets.
- For Dhan's offset-free profile date, `DHAN_PROFILE_TIMEZONE` must be independently confirmed before setting it; do not assume `Asia/Kolkata` from examples.
- This opt-in check can add up to 12 seconds of network latency to a status request. It does **not** enable renewal, change the market-data token selector, or certify quote/candle freshness. `market_data_configured` continues to mean credentials are present, not that they are valid.
- Do not enable on production until callback tests, timeout behavior, rate limits and service-user file permissions are reviewed.

## Optional strict file-token selector (audit branch only)
- `DHAN_REQUIRE_VERIFIED_FILE_TOKEN=1` makes the file-token fallback verify the Dhan profile and account before returning the token. The default is OFF; existing token selection remains compatible.
- Strict mode never falls back to an unverified file token on timeout, expiry, account mismatch, missing client ID or ambiguous provider timezone.
- In-memory consent tokens still follow the existing expiry logic; this flag covers **file-backed fallback only**. Do not describe it as complete authentication verification.
- Each strict fallback can incur a Dhan profile request and up to 12 seconds of latency. **Do not enable in production** until request-rate, concurrency and caching are tested and Dhan profile timezone is verified.
- `market_data_configured` is still configuration, not confirmed quote freshness. No renewal or orders are enabled.

## Strict token verification cache (audit branch only)
- A per-process 30-second cache is used **only** when `DHAN_REQUIRE_VERIFIED_FILE_TOKEN=1`. The legacy path remains unchanged by default.
- The cache key includes the absolute credential path, Dhan client ID, configured provider timezone, and token-file device/inode/size/mtime/ctime metadata. Atomic token replacement invalidates it; it does not survive service restart.
- A cached token is never returned past its independently verified expiry. Timeout or verification failure after cache TTL expires returns no token; no stale-on-error fallback.
- A per-process lock serializes verification for that process. Separate workers each have their own cache, so profile API load still needs operational monitoring.
- This reduces repeated Dhan profile calls but **does not guarantee low latency on cache misses**, and is not proof of live quote freshness. Production rollout remains unapproved.

## Documented consent IST expiry opt-in (audit branch only)
- Dhan's API key/secret consent documentation describes `expiryTime` as IST. `DHAN_CONSENT_NAIVE_EXPIRY_TIMEZONE=Asia/Kolkata` explicitly enables interpreting **offset-free consent expiryTime only** as IST when `DHAN_PERSIST_CONSENT_TOKEN=1` is separately enabled.
- Default remains fail-closed for naive expiry. Unsupported timezone strings are rejected. Already offset-aware timestamps retain their explicit offset. The normalized expiry is returned in UTC.
- This setting does **not** interpret the separate `/v2/profile` `tokenValidity` field; its timezone remains unverified and strict file-token verification must not infer it from consent documentation.
- No auto-renewal, unattended login, credential rotation or production activation is introduced.
