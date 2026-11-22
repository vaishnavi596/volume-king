# BOT KING V3 — Permanent signing and phone-data migration release gate

Date: 2026-11-22. Target: `pilot/v1-pure-original-clone-phone-20261120`.
Status: **RELEASE HOLD** until operator-owned signing secrets, fingerprint, and actual device migration acceptance are verified. This is a runbook, not a claim that those actions have occurred.

## Proven problem
B197 and B198 were shipped under Android package `com.botking.sudhar1.bot_king_v1_pure_clone` but with two different `CN=Android Debug` signer certificates:
- B197 SHA256 `a8cba963a95cd13a1ebc18321af3d876fc07a44fee19e9fbdf786b995649e5e2`.
- B198 SHA256 `9e98159e0429a718f1d9472a9d191f79f97871d4609961a817ede6d71580bc25`.
These came from actual `apksigner` CI logs in runs 44941092536 and 44945727664. Ordinary Android upgrades for the **same package** need compatible signing; B197→B198 in-place upgrade is NOT certified and may be rejected. Generating a fresh per-run signing key can never solve this.

## Source protection already applied
The V3 phone APK workflow is **manual dispatch only**, and now fails closed unless protected CI Secrets exist: `BOTKING_KEYSTORE_BASE64`, `BOTKING_KEYSTORE_PASSWORD`, `BOTKING_KEY_PASSWORD`, `BOTKING_KEY_ALIAS`, `BOTKING_SIGNING_SHA256`. It compares the pinned keystore certificate fingerprint **before the build**, and final APK signer fingerprint **after the build**, and refuses upload if they differ. The workflow does not set these values and cannot create or access a private owner key.

## Required authorized owner actions
1. Keep the currently installed B198/V1 installation and data unchanged. **Do not uninstall, wipe storage, or clear app data** in order to work around a signature conflict.
2. Select and securely back up one long-lived Android release keystore; configure the five named GitHub Actions Secrets using GitHub's protected settings. Do not put keystore bytes, passphrases, tokens, access keys or secrets in repository, logs or chat.
3. Have the build owner review whether a **compatible** signing key for the *actually installed* V3 package exists. If not, a same-package in-place upgrade may be impossible. Choose a dedicated **separate package ID** for new stable-signed installs, preserving the old install alongside it, until there is a tested owner-approved data export/import/migration path. Never quietly overwrite package ID or settings.
4. On sacrificial test data/device, validate: signing SHA256, APK v1/v2 schemes, package identity, install/update behavior, saved watchlists/settings and Paper Ledger preservation, SSK reauthorization, no live-order permissions. Only when successful consider production device cutover.
5. Record certificate fingerprint (public only), source commit, exact workflow run/artifact, upgrade result and rollback plan in `docs/V3_MASTER_JOURNAL.md`. Do not report APK `SUCCESS` as PHONE `ACCEPTED` before install validation.

## Do not weaken these safeguards
- No new disposable `keytool -genkeypair` in CI for the same release package.
- No debug-signing fallback, no unsigned APK upload, no bypass of expected fingerprint checks.
- No live Dhan requests, V1/Oracle service changes or real orders for signing/migration.
- Nothing in this runbook transfers user local app sandbox data; data migration needs its own explicit, verified mechanism.

## Exit criteria
`CI_SOURCE_PASS`, `PERMANENT_SIGNER_CONFIGURED`, `SIGNER_FINGERPRINT_MATCH`, `APK_SIGNED`, `SAFE_INSTALL_OR_MIGRATION_TESTED`, `PHONE_ACCEPTED` are **separate gates**. Only a real device and protected CI configuration can establish the final ones.
