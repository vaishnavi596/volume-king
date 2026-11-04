# Permanent BOT KING APK signing

All releases must retain application ID `com.botking.bot_king`, alias `botking`, and the certificate whose SHA-256 is pinned in `config/android-signing.sha256`. Never regenerate a key for a routine update. Keep the private keystore and its password outside Git and public build artifacts.

The owner's private backup contains the keystore plus two TXT files for the repository Actions Secrets:

- `ANDROID_KEYSTORE_BASE64`: the entire matching base64 TXT file.
- `ANDROID_KEYSTORE_PASSWORD`: the entire matching password TXT file.

Do not paste either value into chat, a GitHub issue, a workflow file, or a command that prints it. The normal `build.yml` workflow requires both secrets and verifies the pinned certificate before publishing.

When the owner has not yet configured repository Secrets, `build-for-local-signing.yml` can package the audited code without handling the owner's private key. Its artifact is an **intermediate, not an installable release for the user**. It includes Android's apksigner tool and a provenance manifest. The release process must download those files, verify the expected commit and file digests, sign the APK with the retained owner key, verify the final APK signature against the pin, and only then deliver the signed APK. Never deliver the intermediate as the final release.

Future build version codes use UTC seconds since 2024-01-01 plus 1,000,000 in both workflows. This avoids resetting the sequence when changing workflow files; GitHub run numbers are workflow-specific. Codes are checked against Android's positive version-code limit. The first owner-signed 2.1.0 build may use the earlier build-workflow code 10101; the subsequent shared-counter codes are higher.

Downloading and opening a later APK signed with this same certificate and a higher version code allows an Android update over the existing install. A phone installation/update smoke test is still required; source and signature checks alone cannot certify every device's installer behavior.

Signing does not activate live broker orders. The separate server LIVE addon and broker configuration must also be deployed and checked. Paper controls and real-order controls remain separate; no automatic live SL/target or unattended protection is provided.
