# Verified 2.3.0 testing APK

Authorized after the 31-screenshot audit. Released 2026-11-05 (India).

| Field | Verified value |
| --- | --- |
| File | `BOT-KING-v2.3.0.apk` |
| Size | 66,609,021 bytes |
| Version / code | `2.3.0` / `90778258` |
| Package | `com.botking.bot_king` |
| APK SHA-256 | `b9eb565a793ad7f0d0fa98291040f5c8faf0e07e8f7551629730c9195c7d6b5e` |
| Permanent certificate SHA-256 | `a3e9c32555872f9b577654a585903f3b27844a7fbb7674c446b605f07f09f0f7` |
| Source commit | `c972c575da3347c1eeee6570a0517f5c6af269cd` |
| Build run | [41954816858](https://github.com/vaishnavi596/volume-king/actions/runs/41954816858) |

All 193 offline tests passed locally and the CI test step succeeded. The separate review workflow also succeeded. Artifact ZIP SHA-256: `f45c0ff6774e1acd730f7a8d10392ddd67cf8adddc5910c4d4613d2bca839b45`; artifact ID 13383320566. File provenance and every packaged src/*.py were matched to tested source. Final APK v2 signature validation passed with one signer matching the pinned permanent certificate. All non-META-INF ZIP entries match the unsigned intermediate.

The installed 2.2.0 APK was independently verified against the same certificate. Its version code 90756396 is below 90778258, supporting in-place Update with retained app settings. Do not uninstall for routine updates. Phone installer behavior, authenticated market feeds and real fills still need on-device checks. Reconnect Angel One after the app restarts; credentials and arming are not persisted.

See [included changes and deliberate limits](release-candidate-v2.3.0.md). This does not certify completion of all 26 audit items: data refresh, status/navigation, login hiding, safe read queuing, snapshot deltas, API practice marking and removal of inert controls are included. Live automatic SL/target/trailing, modify order, other brokers, full-chain PCR, validated trade flow and trained AI probability remain unavailable. No production server was changed or real order sent for this build.
