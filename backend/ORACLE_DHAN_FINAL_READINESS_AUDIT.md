# Oracle–Dhan final production readiness gate (2026-11-09)

**Decision: NO-GO for production activation or unattended renewal.**
Scope: review of audit branch code and completed offline GitHub Actions; no live Oracle inspection or Dhan renewal call was performed.

## Verified by code and offline tests
- Consent persistence is explicitly opt-in and validates account/expiry before atomic token replacement.
- File-backed restart verification uses a read-only Dhan profile request and fails closed on expiry, account mismatch and unknown timezone.
- Optional strict file-token selection uses a 30-second per-process cache; file metadata rotation, expiry and TTL invalidate entries.
- Offline tests cover concurrency, simulated timeout, account mismatch, token rotation and stale-cache rejection.
- The gateway's in-memory consent token path is separate from the file-backed strict selector. A configured credential is not proof of a live market-data feed.

## Blocking items before any deployment
1. **Renewal is not implemented.** Determine with Dhan whether this account and token issuance flow are eligible for a supported unattended renewal path. Do not probe `/v2/RenewToken` with a production token: successful renewal invalidates the prior token. Never automate a PIN, TOTP or unsupported consent flow.
2. **Timezone is unverified.** Dhan profile's offset-free `tokenValidity` and consent `expiryTime` require independently confirmed timezone semantics; otherwise strict verification and persistence intentionally reject them.
3. **Oracle service-user metadata unverified.** Check effective systemd user, directory/file permissions and sandbox restrictions read-only; no secrets or token values in output.
4. **Live performance unverified.** Cache-miss profile calls can block up to 12 seconds. Concurrent requests serialize within one process, but separate workers do not share cache. Rate limits and API availability need safe nonproduction validation.
5. **Status semantics need explicit UI acceptance.** `market_data_configured` reports configured credentials, not authenticated/verified token or fresh quote/candle data. The in-memory consent path is not verified by the strict file-token switch.
6. **Restart and rollback unverified in production.** Exercise a nonproduction rehearsal, confirm token-file owner/mode, callback behavior, service health and rollback plan without placing orders.

## Deployment sequence after separate owner approval
- Read-only metadata preflight, validate Dhan documentation and response timezone.
- Stage branch in a nonproduction environment with all opt-in flags off.
- Run callback, restart, token rotation, timeout and quote freshness tests.
- Obtain explicit approval for a production deployment window; deploy with flags off first, then separately authorize each flag and monitor.
- Do not activate live trading or auto-renewal in this release.

## Conclusion
Offline CI success is not proof of production readiness or 24-hour auto-renewal. Keep main and Oracle unchanged until blockers close.
