# BOT KING secure login: compatibility gate (2026-11-09)

## Verified state
- Current Android app is pinned to Flet 0.25.2; no verified native secure-storage service is present in that release.
- Flet's current official `flet-secure-storage` extension uses Android Keystore, but is developed against newer Flet services. Its Python dependency on `flet` alone does **not** prove compatibility with 0.25.2.
- The current Dhan server access key is deliberately not persisted. Dhan broker credentials remain server-side.
- Security regression tests pass. This document does not claim login persistence is implemented.

## Release gate
1. On a separate test branch, prove a minimal Flet secure-storage app builds on the *same* Android arm64 toolchain, or plan and test a full Flet upgrade with all existing pages.
2. Demonstrate Android write/read/delete on a physical phone and after force-stop/restart.
3. Demonstrate in-place APK update with unchanged package ID and signing certificate; confirm encrypted key survives update. A clean install is **not** a valid persistence test.
4. On successful Dhan status and NIFTY LTP validation, save only the BOT KING server access key to Keystore-backed storage. Do not save the Dhan token.
5. On app startup, read the key and revalidate the server; do not mark connected until the check passes. Network failure should retain encrypted key for later retry without showing false live status.
6. On explicit Disconnect/Clear, delete the encrypted key and clear in-memory sessions. On uninstall or Clear Data, expect re-login.
7. Prevent Android cloud backup from restoring encrypted preferences without their Keystore keys; verify manifest backup configuration.
8. Confirm watchlist 51/51, scanner, chart, and errors behave exactly as before. Never log, print, export, or commit the secret.
9. Only then merge and build a user-facing APK. No plaintext preferences, JSON, reversible APK-bundled encryption, or unverified extensions as fallback.

## Current decision
Keep the successful Flet 0.25.2 production APK unchanged while the Android secure-storage bridge is validated. `src/secure_credentials.py` intentionally fails closed; it is not yet wired into login.
