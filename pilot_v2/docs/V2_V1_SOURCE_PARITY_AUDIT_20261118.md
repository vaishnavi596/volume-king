# V1 → V2 Clean Migration: Source Parity Gate (2026-11-18)

Evidence: read-only GitHub branch `pilot/botking-v2-smart-gateway-20261118`; this is STATIC source audit, not device/runtime acceptance.

## Verified identical staging blobs
All six V1 `src/` and V2 `pilot_v2/v1_clean_staging/` pairs have identical Git blob SHAs:
- analysis_quality.py c60826cd7a049d2b82eac55e5619fe8e954edf84
- candle_retention.py 83ee8682dba8f6a35ee4912c51c1034904578975
- chart_indicators.py 1dffe7d2e30da493fa1f927b5fb5b0d315bcc87a
- dhan_three_minute.py a243558dabb91b072e73e6039e70fd0f3e3ba8e8
- five_engine.py 5bc35f23af8c05917ffa526378a600be97422e5d
- scanner_engine.py fa3ca345c08c7d7f6e60206509eec2277ea560bb

Only chart_indicators.py and scanner_engine.py are additionally present under active `pilot_v2/android_app/src/` with unchanged matching blobs. Four remaining staged modules are NOT active in that source tree. SHA match only means an exact copy, not that dependencies/UI callbacks or real Dhan data work.

## UI / font / functional parity result: NOT READY
Compared `src/main.py` (7,074 lines, Git blob f03fd9ef) to `pilot_v2/android_app/src/main.py` (343 lines, Git blob 9fb3914f). V1 explicitly sets DARK theme and GOLD color scheme, custom BG/PANEL/MUTED colors and denser layout/padding; V2 has no equivalent theme declaration and uses simple default Flet containers. V1 provides full Dashboard/Watchlist/Scanner/Options/Paper/Settings callable screens, custom bottom bar, Scanner WebView+LineChart. V2 offers compact Dashboard index cards, local Watchlist, Settings, Scanner historical LineChart/native candle and CE/PE table within Dashboard; missing complete V1 screen parity, Paper/AI controls, full option refresh, alert/diagnostic flows and exact typography/layout. UI parity cannot pass from matched engine blobs.

## Provider boundary
V1 main still contains Angel/Yahoo and ServerAngelFeed/get_yahoo paths: NEVER copy or execute V1 main unreviewed. Clean six staging modules have no direct Angel/Yahoo or HTTP imports per existing manifest. Active V2 main has no direct Angel/Yahoo paths and expressly has no live Dhan/Oracle client. V2 validates source-gated offline Dhan-shaped candle/option evidence; that does NOT mean all Dhan-dependent features are enabled or supplied with authenticated live data. The old V1 mixed server_feed, market_feed, credentials and order-path modules remain QUARANTINED.

## Safe next migration gate
(1) Review unported supporting local functions and actual V1 UI/asset/font dependencies; copy only audited V2-only safe modules. (2) Restore V1 layout/theme/screens and verified functional callbacks in V2 without importing mixed providers/auth/order execution. (3) Connect V2 app-owned evidence/cache/refresh boundaries to SAFE read-only transport contracts, preserving 70 unique equities, three indices, 1m/3m/5m and 5 evidence-gated filter+blank sixth. (4) Run joint exact-SHA source/security/parity CI and actual signed V2 Android visual acceptance later; Oracle production integration remains LAST. Do not claim live Dhan readiness from synthetic tests.

Last verified source CI #71 231/231 PASS at cc722add; later app-only ATM inbox source/test commits 843ecb5/d569cf2 have no independently confirmed exact-SHA Actions result in this audit. No Oracle, Dhan, order, V1, APK or device changes performed.
