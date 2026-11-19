## 2026-11-19 VERIFIED CURRENT V2 RESUME — CI #186 401/401
- V2-only branch `pilot/botking-v2-smart-gateway-20261118`. Latest VERIFIED executable **b4b6eabd35493540658b7c4e15a8fd74c8a85a62**, [CI #186](https://github.com/vaishnavi596/volume-king/actions/runs/44464942720) SUCCESS **401/401 tests**, zero source security findings, UI source wiring 9/9. Prior #182 396/396; #183 398/398; #184 399/399; #185 400/400 all GREEN. Previous documentation status snapshots are historical.
- Master/Delegate V2 signed read-only source contract now covered end-to-end OFFLINE: P-256 master login (server independently verifies), Master-approved delegated key enrollment, delegated `quotes` scope with forbidden `indices`, revoke preventing further reads, session expiry 403 invalidation, cache last-good retention, no second network call when auth is revoked. App-owned single session holder rotates readers and prevents late/superseded sign-in from resurrecting a cleared session (generation guard). All signed keys in tests are ephemeral synthetic; no live Oracle or Android Keystore binding.
- Manual selected-only read-only refresh source gate is complete but **DORMANT** on real Android until non-exportable native Keystore signer, approved Oracle TLS origin and owner-provisioned public key are verified. No automatic live market polling, real Dhan proof, live five-filter options provenance, deployed V2 routes, signed V2 APK or actual phone acceptance. Do NOT mark app done or claim LIVE.
- NEXT REAL INTEGRATION DEPENDENCIES (NOT ALREADY IMPLEMENTED): (1) Android Keystore P-256 non-exportable key generation and signer callback compatible with `P256ChallengeVerifier.signed_message`; (2) independently authorized Master and Delegates enrollment + remote revoke; (3) real HTTPS Oracle gateway deployment preflight, official Dhan source/provenance and rate budget checks; (4) device-tested Android Flet 0.25.2 optional WebView/native fallback, chart/Scanner refresh; (5) separately approved signed V2 APK/versionCode/in-app version acceptance. Keep current guard: NO APK build or Oracle production changes until app-side review/owner-gated phase, live orders OFF, no Angel/Yahoo fallback, V1 and old journal READ-ONLY.
- Work rule: user's OK means continue to the NEXT CONCRETE safe V2 job. Always read latest V2 journal and exact SHA CI before source modification; batch coherent tests/code+notes; avoid rerunning already green CI.

---

# BOT KING V2 — App-side Exit and External Acceptance Gates

**Latest source-only baseline:** [CI #199](https://github.com/vaishnavi596/volume-king/actions/runs/44468157045), commit `059ae9ae729603e10ab1d9599be36e5b34f947f7`, **421/421 offline tests PASS**, zero source security findings, source UI wiring 9/9. Android/Oracle runtime remains unverified.

## App-side source validated
- Five migrated V1 UI controls: Scanner show/hide, chart style, timeframe, expiry selection, native historical chart.
- 70 unique equities across five Watchlists, separate NIFTY/BANKNIFTY/SENSEX lanes, local app settings, strict read-only last-good quote/candle/evidence caches.
- Five source-gated filters plus deliberately blank sixth. Historical/WAIT labels without exchange-authenticated timestamps; never invent scores.
- Revision-stamped shared collector cache and Android mock enforce independent per-symbol replay rules; old numeric-only collector data remains unverified.
- Device/collector-facing contracts are **offline implementations**. No live data producer is attached to `main.py`.
- Source-only automatic lane cadence now independently claims index/equity due windows under confirmed 09:10–15:45 IST session without issuing network requests. Mounted native Scanner Line/Candles chart, historical EMA/RSI/ATR/levels and five-filter source-gated labels update from accepted cache without a full-page render. This does NOT implement actual live Scanner polling or WebView parity.

## Unmet source/runtime acceptance
1. Rich V1 WebView chart feature: PARTIAL SOURCE-ONLY. A separately tested local no-remote-asset historical SVG/HTML candidate now has a default-OFF optional Scanner Flet WebView preview with native fallback. It is NOT verified on a phone, and original V1 rich controls/gesture parity and production live sync remain pending. V2 pins Flet 0.25.2; V1 had about:blank recovery and native fallback after blank WebViews. Keep native default; require pinned-runtime capability check, isolated local HTML adapter, and actual Android blank/ready/fallback testing before enabling.
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
