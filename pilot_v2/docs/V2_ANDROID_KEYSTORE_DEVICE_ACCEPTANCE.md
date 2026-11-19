# BOT KING V2 — Android Keystore and Device Acceptance Gates

**Active:** `pilot/botking-v2-smart-gateway-20261118` · **verified source CI:** [#199, 421/421 PASS](https://github.com/vaishnavi596/volume-king/actions/runs/44468157045). **Status: source-only; NO deployed Oracle V2 gateway, live Dhan proof, or signed/installed V2 APK.**

## One source of truth
- `app_p256_signature.py`: canonical DER P-256 `r/s` format only
- `app_p256_public_key.py`: canonical on-curve public SPKI format only
- `app_keystore_login_binding.py`: pure platform callback boundary, only device-login challenge may be signed; public-only SHA-256 fingerprint
- `app_p256_login.py`, `app_device_reader_slot.py`, `secure_https_reader.py`: source-gated HTTPS sign-in and in-memory bearer revocation
- `durable_device_keys.py`, `durable_device_sessions.py`: separately owner-approved public enrollment, signed possession challenge and revocable session on offline server prototype

## MUST pass on an actual supported Android handset before sign-in may be enabled
1. Confirm Flet 0.25.2 Android packaging and tested native plugin entrypoint. Secure private key creation through Android Keystore for secp256r1 only; private key nonexportable, never serialized/logged, never in Flet `client_storage` or Python preferences. Verify key backing/attestation on the target OS; do not substitute a `hardware_backed=True` UI field.
2. Native bridge provides only a canonical public SPKI DER exporter and a P-256 SHA-256 sign callback. Compare public SHA-256 fingerprint to the server's independently authorized enrollment pending fingerprint; **fingerprint equality is not authorization**.
3. Master explicitly approves the intended device ID and limited feed permissions using an independently verified session; delegated phones never receive Master bearer, Dhan token or Admin capability. Complete one-time signed key possession proof; verify wrong signature, wrong key, wrong ID, replay and timeout denial.
4. Verify real owner-approved HTTPS origin, OS TLS verification/hostname, no redirects, and same authorized per-device feed scopes. Reader `401/403` clears local bearer, keeps HIST last-good, blocks next call; `429` pauses without falsely logging out. Local sign-in only through reviewed native callback; no user-entered bearer.
5. Physically test 1 Master + up to 3 Delegates: device enable/disable/revoke, second login rotation, session expiry and manual selected-only index/equity read, global <=70 distinct equities and independent NIFTY/BANKNIFTY/SENSEX access. Preserve 1m index and 3m Watchlist local rules.
6. Verify full user-facing V1→V2 functional parity and scanner chart toggles/timeframes on device. Native chart remains fallback; optional WebView must actually mount/recover after blank/error and never be default until accepted.
7. Require actual Oracle read-only preflight, documented source/candle/option provenance, Dhan entitlement and provider rate-limit/cooldown evidence. Without trusted exchange time, keep HIST or WAIT; do not fabricate five filter votes, sixth remains blank and live orders OFF.
8. Only after app feature/runtime gates and explicit owner-approved build phase: produce a distinct signed V2 APK; verify package ID, versionCode, signing cert, install next to V1, full end-to-end physical acceptance and rollback. Oracle production changes only after separately approved backup/rollout.

## Failure and recovery
Any missing native API, key unavailable, invalid signature, wrong scope, denied session, blank WebView, missing provider, or malformed snapshot: **FAIL CLOSED**, retain last-good HIST where applicable, never claim LIVE, no automatic retry/fetching or trading orders. Do not treat 413 offline test passes as evidence of completed physical gates.

**Standing rule:** Stay V2-only, leave old V1 and its journal untouched, do not expose keys or tokens, no Yahoo/Angel fallback, and combine related code/tests/journal in one coherent CI batch.


## Updated verified source coverage (#199)
- Four-device policy (Master + 3 Delegates) now has cross-device shared cache tests: one 70-equity global union, isolated quote visibility/3 indexes, atomic 71st rejection, disable and fresh reselection. These are synthetic sessions only.
- Read-only HTTPS direct-entry selected-roster checks preclude unnecessary requests; local session rotation and in-flight logout prevent old data acceptance; rate-limited 429 respects bounded Retry-After 30–300s without login invalidation. Exact source CI 421/421 PASS.
- **Still unverified physically:** native nonexportable Android Keystore keys, OS/plugin integration, owner enrollment, revocation after real signed login, real trusted Dhan/Oracle session and signed V2 APK installation. No production approval inferred.
