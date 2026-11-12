# BOT KING 226 device enrollment security contract

Status: **design / offline primitives only**. Not implemented in the Android UI or Oracle production API.

1. Owner authorizes one-time enrollment over the trusted HTTPS Oracle origin using an existing owner-controlled credential. Never expose a public unauthenticated enrollment route.
2. Android generates a non-exportable device-bound signing key in Android Keystore. Prefer hardware-backed keys where available; record whether hardware protection is actually supported.
3. Oracle stores a device ID, public key, revocation status, creation and last-seen timestamps, and hashed opaque session tokens. Enrollment is explicitly approved and rate-limited.
4. The six-digit PIN unlocks local encrypted credential access; Android biometrics use BiometricPrompt to unlock the same Keystore-bound credential. Never transmit PIN or fingerprint data to Oracle.
5. Oracle issues short-lived access sessions and revocable rotating refresh credentials, bound to the enrolled device proof. Revoke on lost phone, logout, repeated abuse or re-enrollment.
6. A device restart or app restart requires PIN or biometric unlock, not re-entering the server URL or pairing key. Never store the pairing key as a permanent substitute for device enrollment.
7. Apply PIN retry throttling, lockout and a separate owner-controlled recovery path. A salted PIN hash alone does not defend a six-digit PIN against offline guessing if its database leaks; device hardware protections and retry limits are mandatory.
8. Do not enable enrollment routes until threat model, storage permissions, device binding, replay protection, tests and manual Android review are complete.
9. Dhan OAuth and Dhan PIN are separate from BOT KING device unlock. Live order placement stays disabled.
