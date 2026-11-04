# 2.2.0 testing release scope

User authorized building an update over the permanently signed 2.1.0 installation. Date: 2026-11-05 (India). The generated page images are illustrative proposals, not screenshots of the built app.

## Included

- Home, Live, Settings, Scanner and a separate fifth Paper page, with prior practice state preserved.
- Compact Home data/order-permission status; broker positions are shown only from a verified account snapshot. Missing account data is not reported as zero or flat.
- Broker-only provider selection, migration of old Auto/Yahoo preferences, removal of Yahoo network fallback and visible choices. Old non-broker market snapshots cannot substitute for broker failures.
- Broker candles render in TradingView Lightweight or native API chart mode. Old valid broker quotes can be displayed as historical with their actual time; they cannot become current signals. Real-order quote-age guards remain separate and strict.
- Linked option selection, editable LIMIT price, manual confirmation, order/position records and cancellation on Live. Existing live execution guards are retained.
- Scanner retains the selected-symbol final direction, ten filters, coverage requirements, saved agreement threshold and separate higher-timeframe context. Modeled premiums and fixed hypothetical target scenarios were removed.
- Budget listing uses only fresh actual option quotes already loaded for the selected symbol and strike window. Shows per-unit premium and verified one-lot debit before charges; clicking transfers selection to Live without submitting. It is price-ordered quote browsing, not a validated AI suitability or low-decay ranking. An empty/missing window is explicitly reported.

## Checks before packaging

184 offline tests pass, including broker-only migration/failure behavior, stale/nonmatching quotes, budget arithmetic, safe quote selection, Home account snapshot failure/epoch handling and native API chart preference preservation. Python compilation/target grammar, workflow YAML and installer shell syntax pass.

## Not implemented or not verified by this release

Automatic live SL/target/trailing/re-entry, unattended protection, complete Greeks/depth-based AI comparison, real-time Paper automatic marking and a separate News API remain outstanding. News is still explicitly sourced RSS context. Market refresh is polling while the app is open, not tick streaming. The new LIVE server addon and real-broker/device behavior have not been verified/deployed during this build. No real broker order is placed by the build or tests.

The existing permanent signing key must be reused. Verify final APK package, higher version code, signature certificate, intermediate provenance and packaged source before delivery. Do not deliver the intermediate APK as the installable release.
