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
