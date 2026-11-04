# BOT KING: install future APKs as updates

Current APK package confirmed: `com.botking.bot_king`.

This branch prepares permanent release signing. It is not activated on main and does not start a build. Existing APKs were not built with this permanent key. The first APK signed with it may require one clean installation; after that, preserve this same key for every update.

## One-time setup on your own computer

1. Install/use Java JDK 17 and Python.
2. Download `tools/create_signing_key.py` from this branch and run `python create_signing_key.py`.
3. The script creates a new private `BOT-KING-signing` folder under your user directory. It refuses to overwrite an existing folder/key.
4. Open GitHub repository Settings > Secrets and variables > Actions.
5. Add these **repository secrets**, pasting the full contents of the matching local text files:
   - `ANDROID_KEYSTORE_BASE64` from `ANDROID_KEYSTORE_BASE64.txt`
   - `ANDROID_KEYSTORE_PASSWORD` from `ANDROID_KEYSTORE_PASSWORD.txt`
6. Keep a private encrypted backup of the JKS and password. Never put either secret in source code, chat messages, logs or APK artifacts.
7. After the secrets exist, apply this branch workflow to main and build the first permanently signed APK.
8. Verify the package, increasing version code and signing certificate. Export app settings before the one-time clean installation if required.
9. From then on, open each newer APK and choose Update/Install. Do not change the key, package ID or clear app storage. Android normally preserves app-private settings during an accepted update; credentials still follow the app's explicit no-persistence policy.

## Workflow checks

- Missing signing secrets stop the build rather than publish a temporary-key APK.
- Private signing material lives only in the runner's temporary directory and is removed with an always-run cleanup step.
- The final APK is signed with alias `botking`; its certificate digest must match the configured keystore certificate.
- The package must remain `com.botking.bot_king`.
- Version code is generated from workflow run number and attempt; normal subsequent runs increase it.
- The first build and a subsequent build still require an actual Android update-install test.

This supports manual APK updates. It does not silently install APKs on a phone or introduce Play Store distribution.
