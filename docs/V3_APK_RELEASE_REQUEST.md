# BOT KING V3 controlled APK release request

Release: B199 scanner failure-detail phone test
Branch: pilot/v1-pure-original-clone-phone-20261120
Preflight: full NO-APK regression PASS, run 44995302997
Adapter/B1/B2: PASS on 36f59c8
Trigger policy: changing this file alone requests one gated APK build; ordinary source commits do not sign APKs. Existing APK workflow tests must pass before signing and upload.
Note: prior B199 run #72 failed; this is a fresh gated verification, not a claim of successful signing.

Release retry: B199-R2 after test gate correction 5bc6797 and pinned signing fix bfb02af. ChatGPT-tracked run. Preserve all fail-closed checks; do not install until APK cert and upload PASS.

Release request: B199-R3 automatic regression PASS on a855d7e8d5af41ac768f0bdf0936c705a58b7239; B3 run 45010959183 and joint index audit 45010959188 both SUCCESS. One gated APK build requested via existing release-file trigger. Keep signing, Dhan-only, and offline regression fail-closed; no Oracle/V1 deployment.
