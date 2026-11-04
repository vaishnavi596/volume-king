# Verified 2.2.0 testing APK

Authorized by the user for an in-place update test. User-facing release date: 2026-11-05, India.

| Field | Verified value |
| --- | --- |
| File | `BOT-KING-v2.2.0.apk` |
| Size | 66,604,925 bytes |
| Version / code | `2.2.0` / `90756396` |
| Package | `com.botking.bot_king` |
| APK SHA-256 | `d3d192b3b2af95648c1bbc49d612d85348c3267719afba4aa6b94947a47bb481` |
| Permanent certificate SHA-256 | `a3e9c32555872f9b577654a585903f3b27844a7fbb7674c446b605f07f09f0f7` |
| Source commit | `305a03e39cf12ffe506cfda59612c37a90292d45` |
| Build run | [41905319826](https://github.com/vaishnavi596/volume-king/actions/runs/41905319826) |

All 184 offline tests passed locally and the CI test step succeeded before packaging. The intermediate artifact and per-file provenance digests were verified. Final APK v2 signature validation succeeded with one signer and the pinned certificate. The known 2.1.0 APK was separately verified to use that same certificate; its version code is 10101, below the new code. Packaged main.py, scanner_engine.py, analysis_quality.py, live_controls.py, market_feed.py and server_feed.py match the tested source bytes; non-signature APK contents were unchanged by signing.

This is a functional testing update, not a certification of device installation or actual broker fills. Open it over the installed permanently signed 2.1.0 app and use Android's Update operation. The phone installation smoke test remains the user's next step. A fresh broker login is required after restarting/updating the app; credentials and live-order arming are not persisted.

Included and outstanding behavior is documented in [the release candidate scope](release-candidate-v2.2.0.md). Five pages, broker-only market data, compact Home, exact option selection and actual loaded-window budget quotes are included. The generated mockup images are design illustrations, not exact screenshots or proof of implemented future features.

No production server was modified and no real order was sent during this release. Real manual orders still require the compatible LIVE gateway and broker/session permissions. Automatic LIVE SL/target, unattended trading protection, full Greeks/depth AI suitability ranking, real-time automatic Paper marking and a separate News API remain outstanding. News stays explicitly sourced RSS context; market refresh is while-open polling, not WebSocket tick streaming.
