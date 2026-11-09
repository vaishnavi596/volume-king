# BOT KING Android Keystore device acceptance checklist

This is an **experimental** security test, not a BOT KING release APK. The existing Flet-client debug artifact only compiles the native control and does not automatically include this Python test UI.

## Build gate
- Package `prototype/device_keystore_smoke.py` as the Flet application entry point and include `src/keystore_control.py` in the Python package.
- Register `botkingkeystore` in the **same** Flutter client bundled with the test APK.
- Use a different Android application ID from production `com.botking`; do not replace or uninstall the user's working BOT KING 2.3.65 app.
- Never copy actual server access keys or broker tokens into test fixtures, logs or screenshots.

## Device acceptance
1. Install experimental APK. Press **Write random test token** and verify the success message.
2. Press **Read and compare**. It must confirm a match.
3. Force-close the app, reopen it, and press **Read and compare** again. It must confirm persistence after restart.
4. Press **Delete and verify**. It must confirm the credential no longer exists.
5. Force-close and reopen; reading again must not recover the deleted token.
6. Upgrade the **experimental** APK in place with the same package ID and signing certificate, and confirm a saved test token persists across that update.
7. Uninstall the experimental APK and reinstall. The test must **not** claim a restored credential is valid without a fresh secure read/verification.
8. Test native errors and absence of the control. They must never produce a success or saved-credential message.

## Release decision
Do not enable automatic production login or merge into `main` until the above tests pass on an Android device and the BOT KING packaging path is proven. Native compilation and Python unit tests alone do not meet this gate.
