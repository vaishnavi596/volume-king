# BOT KING V2 — Parallel Pilot

**STATUS: isolated source prototype; not an installed APK and not Oracle deployed.**

- Code resides only in `pilot_v2/` on independent branch `pilot/botking-v2-smart-gateway-20261118`; legacy source, installed APK, service and old branch remain untouched.
- Pilot reserved identity: Android package `com.botking.bot_king_v2`, version `2.0.100`, build code `100`. The identity JSON is NOT yet a compiled Android manifest or APK.
- V2-only server API target `/v2-pilot`; disabled by default until authenticated gateway exists.
- Support **1, 2 or 3 phones**, with *one master-owned device* and up to two delegated devices. Master may enroll, limit per-device read-only data feeds, temporarily disable or revoke device sessions. **No secondary phone gets Dhan's main login, API token, master rights, or unrestricted remote device control.**
- Gateway must independently verify master session (strong device-bound auth and short-lived revocable bearer/session) BEFORE passing calls to `DeviceRegistry`. A claimed device ID is NOT proof of authorization.
- Broker token lifecycle is Oracle-only, with real Dhan OAuth renewal capability gating; no invented unattended 24h renewal. Reauthentication may require owner approval.
- Shared Dhan market data and secure per-device revision delivery reduce repeated upstream requests. Five watchlists/70 unique equities plus independent three indexes; five evidence-gated filters, sixth blank.
- No live trading orders. No copying pairing keys/OAuth credentials, access tokens or stale live labels from legacy app. Future allowlisted preference migration only.
- **Next:** read-only Oracle capability inventory; build secure server-side session + collector behind flag; then create a separately signed V2 Flet Android build workflow with actual identity verification and device installation. Legacy service stays enabled until successful cutover and rollback proof.

## New chat / handoff
**Say:** **“बोट किंग इंप्रूव वर्जन का जर्नल देखो और काम आगे बढ़ाओ।”** Open [V2_HANDOFF.md](docs/V2_HANDOFF.md), then [V2_MASTER_JOURNAL.md](docs/V2_MASTER_JOURNAL.md) and [V2_WORK_LOG.md](docs/V2_WORK_LOG.md). Confirm the actual GitHub HEAD/last ten CI runs before changing anything.

## V2-002A: isolated device-session prototype
`pilot_v2/device_sessions.py` adds short-lived opaque bearer sessions, hashed in-memory identifiers and server-verified master action authorization. **No real server HTTP endpoint or Android cryptographic verifier is connected**. Test `pilot_v2/tests/test_device_sessions.py`; revoke/disable is immediate in this single-process mock only. Persistent/revocable multi-worker store and external verified identity are mandatory before deployment.

## V2-002B — device proof and Dhan token status
- `device_verifier.py`: validates Android-compatible P-256 ECDSA signatures over one-use, time-bound server challenge for *already provisioned* device public keys. Production enrollment and shared atomic challenge store NOT implemented. `broker_token_status.py` reports expiry and whether reauthorization is required without storing secrets or attempting forbidden renewals. New offline tests use generated test keys, not Android Keystore hardware.

## V2-003A — common read-only cache delivery
- `shared_quote_gateway.py`: accepts only server-internal validated quote snapshots by contract; each verified mobile session can read its permitted equity selection/indices from the same cached revision. Device selection cannot issue Dhan calls. **All state is in-memory; real shared multi-worker persistence and an authenticated source producer still need implementation.**

## V2-003C: quote request planning
`quote_batch_coordinator.py` creates only offline provider work leases (one at a time), with per-symbol attempt spacing and a safe 429 backoff. No HTTP request, WebSocket, durable lock, authentication or server deployment is implemented. Actual collector must split instrument-specific APIs and use multi-process atomic state; pilot code is not yet ready for live Dhan calls.

## V2-003D persistent quota scheduler prototype
`durable_quote_gate.py` persists a single-host shared lease with SQLite transactions, for preventing duplicate quote work and preserving 429 cooldown across local worker restarts. It has no Dhan network calls and cannot replace the production OAuth, device session or broker endpoint safeguards. Do not deploy without approved local DB permissions and verified server setup.

## V2-004A — persistent device authorization prototype
`durable_device_sessions.py` stores device grants and token **hashes** on a shared single-host SQLite file, with atomic Master Admin disable/revoke and 3-phone limit. Cryptographic identity verification remains an external trusted input; this code is NOT yet an HTTP login endpoint. Never treat a claimed device ID as proof, expose bootstrap to phones or store OAuth tokens in this database.

## V2-004B — Verified Login Composition
`verified_login_gateway.py` joins P-256 signature verification to server-side durable device sessions with per-feed permissions. All proofs are synthetic test keys, not Android Keystore. **No HTTP/login deployment**: nonce store and trusted key provisioning must become durable/atomic across workers before exposing a gateway.

## V2-004C: atomic shared login challenge
`durable_challenges.py` stores SHA-256 nonce digests and consumes them atomically via SQLite before verification, allowing separate local workers to issue and redeem one P-256 challenge. It is **not** a deployed device login; real master-approved key registration, Android native bridge and protected HTTP routes remain pending.

## Standing workflow rule — latest committed batch only (owner change, 2026-11-18)
Before any NEW V2 code/test patch or commit, inspect **only the immediately preceding V2 commit**: its exact changed files, its exact SHA's relevant CI run(s), and any failure logs. If its CI is PASS, proceed; if FAIL, correct that same failure and verify the corrective CI before unrelated changes. If pending or absent, clearly say so and check only that batch's result. Check the files ACTUALLY changed in that commit (whether 1, 2, 3, or more), **never an automatic ten-commit/ten-file sweep**. If the head is docs-only, inspect that latest commit and the most recent applicable source CI; do not claim docs CI proves code. Allow broader history inspection only for a concrete dependency, regression, or safety reason, not as an automatic rule. Keep V2 source, targeted tests, Master Journal, Work Log and Handoff in one atomic commit where safe. No repeated approval for ordinary code/test work.

## V2-004D — Master-approved durable device key lifecycle
`durable_device_keys.py` is an isolated SQLite prototype for registering/rotating delegated P-256 public keys only after Master session and candidate private-key possession proof. **Not a deployed pairing endpoint:** current login verifier still uses a static trusted-key mapping and needs dynamic generation checks before it can safely enforce rotation, and master initial key enrollment/recovery is not implemented.

## Fast-track audit / current direction
See [V2_FAST_TRACK_AUDIT.md](docs/V2_FAST_TRACK_AUDIT.md): four grouped work packets for secure current-key login, versioned server+Android contract, provider-safe data lanes and signed V2 pilot build/deploy. Source, tests, journals and release evidence must remain distinct; this audit itself is docs-only.
