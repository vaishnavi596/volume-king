# BOT KING 226 — Master implementation roadmap

This is the migration target, not a statement that all milestones are implemented.

## Non-negotiable architecture
- Dhan market data, quote collection, historical candle persistence, refresh and scanning belong to the Oracle server. Android displays server-prepared results.
- Android must not require the owner to retype the server URL or a server pairing secret for routine login.
- Initial device enrollment is authenticated once; thereafter use Android Keystore-backed credentials and a short-lived, revocable Oracle session.
- Six-digit local PIN and supported Android biometric authentication unlock the device credential. PIN must never be sent as a Dhan PIN or stored as plaintext. Enforce retry limits and secure recovery/re-enrollment.
- Dhan broker OAuth/token is server-side and separate from mobile PIN/biometric unlock.
- Do not treat a fresh HTTP collection as exchange-verified live market data. Historical/unverified/stale quotes never become live trading signals.
- Real order placement remains disabled.

## Delivery gates
1. Oracle read-only snapshot and persistent candle APIs, with source/freshness and error metadata.
2. Oracle scheduled ingestion, candle retention and rate-limit-safe refresh across the verified symbol universe.
3. Oracle scanner and Super Five ranking with timestamp and data-quality gates; paper-only.
4. One-time owner-controlled device enrollment, revocable sessions, Keystore-backed PIN/biometric unlock, no recurring pairing-key field.
5. Android replacement of direct historical Dhan calls with Oracle cache and scanner APIs; redesigned login/dashboard/watchlist/charts/settings.
6. Options and paper-trading UI with verified-only source labels.
7. End-to-end tests: offline, auth/session expiry, reboot, upgrade, 51-symbol scans, candle gaps, server outage and stale data.
8. Versioned release APK after tests and manual Android verification.

## Current migration warning
The v2.3.79 Android screen still exposes server URL and pairing-key fields and calls Dhan historical endpoints directly. A standalone read-only Oracle client is an incremental step only; it is not device enrollment, biometric login, or complete migration. Never claim milestone 4 or 5 complete until end-to-end tested.
