# BOT KING Android secure storage compatibility gate

Status: **NOT VERIFIED**. This is a research checklist, not authorization to upgrade or build an APK.

## Current baseline (main, 2026-11-12)
- Python: >=3.11; Flet 0.25.2; flet-webview 0.1.0.
- GitHub Android build workflow pins Flutter 3.24.5, Java 17 and Gradle 8.7.
- Runtime uses `ft.WebView` integration, existing navigation, Dhan/Angel HTTPS pairing, and signed upgrade installs.
- `src/secure_credentials.py` is an adapter only. No verified Android Keystore bridge or secure persistence currently exists.
- No credential may be written to Flet preferences, JSON, logs, source code, APK assets, or reversible encryption with an embedded key.

## Gate A: resolve dependencies before modifying production configuration
1. Determine the exact compatible releases and Python APIs of `flet`, `flet-webview`, and `flet-secure-storage` from their package metadata and upstream documentation. Do not assume the latest releases work together.
2. Confirm required Flutter SDK, Dart SDK, Android minSdk/compileSdk, Gradle, Java and Flet packaging extension mechanism.
3. Create a dependency lock and run a disposable environment dependency resolution (`pip check`). If the current 0.25.2 runtime cannot host the extension, test a pinned, compatible upgrade in this branch only.
4. Check all deprecated Flet controls and callbacks in `src/main.py`; preserve navigation, chart WebView and offline behavior.
5. Never upgrade the `main` build workflow based only on a Python import test.

## Gate B: native integration and secret lifecycle
1. Implement a real Flet-registered secure-storage service backed by Android Keystore, with async get/set/delete; no plaintext fallback.
2. Use an origin-scoped storage key for BOT KING pairing secrets; validate HTTPS origin before use. Keep broker access tokens server-side.
3. Restore the pairing key only after native storage successfully reads it; do not display it in UI or log it.
4. On explicit Forget Key / account reset, delete the secret; ordinary disconnect and app restart semantics must be specified separately.
5. Handle native unavailable/locked/corrupt/denied states with safe messages and no automatic fallback.
6. Never auto-submit a restored key to a changed server origin.

## Gate C: acceptance
- Offline tests for storage success/failure, redaction, provider changes, no plaintext persistence, and logout semantics.
- Android device: fresh install, restart, process death, upgrade over previous signed version, secure read/write/delete and failure handling.
- Preserve package name, signing identity, version code progression and no live orders.
- Confirm no secrets in app preferences, logs, backups or screenshots.
- Only merge after all applicable tests pass; **do not dispatch APK build without a separate release decision**.

## Current blockers
Exact `flet-secure-storage` compatibility with Flet 0.25.2 or a pinned upgrade is not established. Native Android runtime testing has not been performed. Do not claim secure key persistence is complete.

## Public package research (2026-11-12)
- PyPI publishes official `flet-secure-storage==1.1.2` (Nov 6, 2026), Python >=3.10; the Flet service documentation says Android uses Keystore through Flutter `flutter_secure_storage`.
- PyPI also publishes `flet==1.1.2`; official built-in extension documentation gives `flet>=1.0.0` in its example, **not** proof of a working Flet 0.25.2 integration.
- Official example uses `flet_secure_storage.SecureStorage` and AndroidOptions. Its exact method signatures and runtime registration still require verification before implementing the BOT KING adapter.
- Current `flet-webview==0.1.0` compatibility with Flet 1.1.2 and the app's `ft.WebView` usage is **not verified**. Do not blindly change dependency pins.
- Official modern publishing documentation resolves Python versions differently from the existing 0.25.2 build. Changing Flet may also require a controlled Android toolchain migration.
- A disposable local PyPI dependency resolution attempt was blocked by network DNS failure. It is **not** evidence of package incompatibility.

References:
- https://pypi.org/project/flet-secure-storage/1.1.2/
- https://pypi.org/project/flet/1.1.2/
- https://flet.dev/docs/services/securestorage/
- https://flet.dev/docs/extend/built-in-extensions/
- https://flet.dev/docs/publish/
