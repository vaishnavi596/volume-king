# BOT KING 2.1.0 verified APK

Built after the user's explicit APK authorization on 2026-11-04.

| Field | Verified value |
| --- | --- |
| Installable file | `BOT-KING-v2.1.0.apk` |
| Application ID | `com.botking.bot_king` |
| Version name / code | `2.1.0` / `10101` |
| File size | 66,609,021 bytes |
| APK SHA-256 | `bb39604f9fb872cae57ed0fc32118ce9257dd1fb8d0b63ade4e6e757817a665a` |
| Permanent signing certificate SHA-256 | `a3e9c32555872f9b577654a585903f3b27844a7fbb7674c446b605f07f09f0f7` |
| Packaged source commit | `c41cb8c106b41ca39b7af730c132b1fe8cb5047e` |
| Successful build run | [41871876805](https://github.com/vaishnavi596/volume-king/actions/runs/41871876805) |

All 165 offline regression tests passed in the build. Android apksigner verifies the final APK's v1, v2 and v3 signatures with exactly one signer and the pinned permanent certificate. Packaged main.py, scanner_engine.py, analysis_quality.py, live_controls.py and server_feed.py match the audited source bytes. Non-signature APK entry contents are unchanged by signing. The intermediate artifact and its per-file provenance hashes were verified before signing.

The owner's private key was retained outside Git and public CI. A private backup was saved for the owner. Do not substitute the intermediate workflow artifact for this signed release. Future releases must reuse this same private key and application ID with a higher version code; both build workflows now use the shared version counter described in [permanent update instructions](permanent-android-updates.md).

## Installation and live-service state

The old app has already been uninstalled by the user. Install this APK, then verify startup, charts, saved selections and Paper behavior on the phone. A future same-key upgrade still needs a phone installation smoke test.

The APK contains Paper controls and a separate manual confirmed LIVE order path. **The production gateway's new LIVE addon has not been deployed during this build.** Real orders require that server update, owner broker login, applicable SmartAPI account/static-IP configuration, explicit session arming and per-order review/confirmation. A visible LIVE button alone does not mean real orders are enabled. No real broker order was sent in these checks.

Server update source is the immutable reviewed commit above, using `backend/install-oracle.sh <commit> --enable-live`. The installer backs up existing configuration before replacing it. A server restart clears broker sessions and requires a fresh login; it does not cancel existing broker orders or close positions.

Automatic live SL/target/trailing, unattended protection and alert delivery remain unavailable. Scanner option premium candidates remain simulations; chart overlays beyond EMA and drawing tools, validated three-source trade-flow direction and additional brokers remain feature backlog. Do not interpret indicator agreement as a calibrated win probability.
