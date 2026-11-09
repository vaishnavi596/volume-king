# Decision: preserve Flet 0.25.2 and investigate a native Keystore bridge

Date: 2026-11-09
Status: chosen architecture; implementation **not** verified

## Evidence
- The Flet 1.1.2 + flet-secure-storage 1.1.2 Python import probe passed.
- The production BOT KING source uses seven symbols missing from Flet 1.1.2: ChartAxis, ElevatedButton, LineChart, LineChartData, LineChartDataPoint, WebView and app.
- Therefore upgrading the entire app merely to persist a server key entails substantial chart, webview and entry-point migration.

## Decision
Keep production Flet 0.25.2 and current chart, broker and signing behavior unchanged.
Investigate a small Android-only Keystore-backed native plugin/bridge compatible with the pinned Flutter/Flet runtime **on this experiment branch**. The Python VerifiedNativeCredentialStore is an interface, not proof that a native bridge exists.

## Mandatory implementation gates
1. Prove a native bridge can register in Flet 0.25.2 and support async get/set/delete without a Flet upgrade. If impossible, stop and reconsider the framework upgrade.
2. Android Keystore must protect encryption keys; ciphertext may be held in Android private storage, never plaintext or a hardcoded reversible key.
3. Disable insecure backup/restore of encrypted secrets or handle restored ciphertext safely. Preserve application ID, signing certificate and increasing versionCode.
4. Persist only the BOT KING server access key after successful authenticated Dhan status **and NIFTY LTP** checks. Never persist the Dhan broker token on the phone.
5. On startup, reconnect only after verifying the server and live quote. On network errors, retain encrypted credentials for later retry, but never show a false Connected state.
6. Explicit Disconnect deletes the secret. No secret in logs, crash reports, repository, ordinary preferences or UI status.
7. Add unit/integration tests, Android build, real-device cold-start and in-place update tests before merging to main.
8. Do not trigger a production APK build or alter the functioning main branch until all gates are satisfied.

## Current user impact
No new APK, no credential auto-save, and no device changes yet. Existing manual Dhan pairing remains the working path.
