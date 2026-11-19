# BOT KING V2 — App-side Exit and External Acceptance Gates

**Latest source-only baseline:** [CI #170](https://github.com/vaishnavi596/volume-king/actions/runs/44459269573), commit `22e378d9c4e5df53fb84eecc89cba778b63c13bd`, **375/375 offline tests PASS**, zero source security findings, source UI wiring 9/9. This is NOT a completed Android build or live integration.

## App-side source validated
- Five migrated V1 UI controls: Scanner show/hide, chart style, timeframe, expiry selection, native historical chart.
- 70 unique equities across five Watchlists, separate NIFTY/BANKNIFTY/SENSEX lanes, local app settings, strict read-only last-good quote/candle/evidence caches.
- Five source-gated filters plus deliberately blank sixth. Historical/WAIT labels without exchange-authenticated timestamps; never invent scores.
- Revision-stamped shared collector cache and Android mock enforce independent per-symbol replay rules; old numeric-only collector data remains unverified.
- Device/collector-facing contracts are **offline implementations**. No live data producer is attached to `main.py`.
- Source-only automatic lane cadence now independently claims index/equity due windows under confirmed 09:10–15:45 IST session without issuing network requests. Mounted native Scanner Line/Candles chart, historical EMA/RSI/ATR/levels and five-filter source-gated labels update from accepted cache without a full-page render. This does NOT implement actual live Scanner polling or WebView parity.

## Unmet source/runtime acceptance
1. Rich V1 WebView chart feature: NOT MIGRATED. Need supported Android WebView runtime, local navigation/session safety, and real device check.
2. Authenticated chart sync: NOT CONNECTED. Require verified P-256 device session and validated, source-stamped candle evidence from approved Oracle pipeline.
3. Scanner supervised automatic refresh: NOT CONNECTED. Require app-owned market window 09:10–15:45 IST with explicit exchange session evidence; shared bounded index/equity lanes; cache reuse; no page-wide redraw.
4. Owner/master and delegated phones: offline contract only; no verified end-to-end login, revoke or device-acceptance evidence.
5. Real Dhan token entitlement and Oracle gateway: **NOT VERIFIED**. Do not use Yahoo/Angel silent fallback.
6. Signed independent V2 Android APK: **NOT BUILT**, device compatibility and visible versionCode still unverified. Do not build in this app-side guard.
7. Filters/options/news/futures: live provenance and actual Dhan data remain unverified. No LIVE labels or trading orders.

## Safe next sequence
- **App-side acceptance pass:** use latest V2 source and combined gate; add source-only controls for pending Scanner sync and WebView where viable, but never treat mock data as live.
- **Authorized integration preflight:** redacted Oracle preflight, verified device login/TLS origin and Dhan routes (no secrets or live orders). Shape source-gated transport and rate budgets from actual app contract.
- **Joint integration and controlled release:** backup/rollback and explicitly authorized production gateway change, combined regression, separate signed V2 APK with package/versionCode/certificate verification, actual device test.

**Permanent guard:** no changes to historical V1 app/journal; no credentials printed or saved; no Yahoo/Angel fallback; no enabled live broker orders.
