# BOT KING 226 Android Keystore integration gate

## Current implementation
The Android app is **Flet/Python** (`src/main.py`), built by `.github/workflows/build.yml` with `flet build apk`. The repository has no checked-in native Android Kotlin/Java source or verified Flet bridge for Android Keystore / BiometricPrompt. `src/secure_credentials.py` intentionally fails closed without a native service. Backend P-256 ECDSA verification is available, but **does not implement an Android key or fingerprint UI**.

## Required native Android work (not yet implemented)
1. Implement and verify a Flet native plugin or a maintained Android bridge that generates a **non-exportable EC P-256 signing key** using AndroidKeyStore and returns only its DER SubjectPublicKeyInfo.
2. Sign exactly `b"BOTKING226:DEVICE-AUTH:v1:" + base64url_decode(challenge)` with SHA256withECDSA. Transmit the DER ECDSA signature as base64url. Server stores public key with `p256:` prefix and verifies with `verify_android_p256_signature`.
3. Require Android BiometricPrompt/OS authentication for key use, with an explicit device credential fallback policy. A local six-digit PIN must never be transmitted to Oracle or stored in plaintext; local PIN verification alone must not claim hardware-backed security.
4. Enrollment requires authenticated **owner approval** and device-key possession proof, not a client-supplied boolean. Build a revocable server session, HTTPS only, and prevent session logging.
5. Verify actual Android device behavior: enroll, unlock, sign, replay failure, key invalidation, reinstall, offline state, expiry, revocation, restart, and app upgrade.

## Production blockers
The 226 auth router is **not mounted**. SQLite challenges and lockout are implemented, but per-IP abuse protection, real owner enrollment, Android plugin, biometric integration, rate-limit policy, secure storage, and Oracle deployment audit remain incomplete. Do not expose these endpoints or replace the existing production login until those gates pass.
