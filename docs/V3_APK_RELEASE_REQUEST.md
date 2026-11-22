# BOT KING V3 controlled APK release request

Release: B199 scanner failure-detail phone test
Branch: pilot/v1-pure-original-clone-phone-20261120
Preflight: full NO-APK regression PASS, run 44995302997
Adapter/B1/B2: PASS on 36f59c8
Trigger policy: changing this file alone requests one gated APK build; ordinary source commits do not sign APKs. Existing APK workflow tests must pass before signing and upload.
Note: prior B199 run #72 failed; this is a fresh gated verification, not a claim of successful signing.

Release retry: B199-R2 after test gate correction 5bc6797 and pinned signing fix bfb02af. ChatGPT-tracked run. Preserve all fail-closed checks; do not install until APK cert and upload PASS.
