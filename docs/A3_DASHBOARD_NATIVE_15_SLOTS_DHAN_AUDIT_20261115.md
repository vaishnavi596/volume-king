# BOT KING — A3 joint audit and Android release gate

Date: 2026-11-15. Target branch: `fix/botking-2399-candle-retry-20261114`.

## Exact screenshot scope
The user circled the **Dashboard** card titled **CANDLE + OPTIONS + NEWS • NIFTY • 5m**, containing **WAIT • 0/3 directional inputs**. Its single Dashboard `fusion_card(..., compact=True)` instance was removed. **Do not delete or hide Super Five, CANDLE ANALYSIS, OPTIONS DATA, watchlist historical signals, or the independent five-engine evidence subsystem.**

## Applied code changes
- Dashboard's three persisted selectable analysis slots reuse existing Dhan 5m OHLC history. A bounded 24-candle native mini-chart renders red/green OHLC without WebView or any additional Dhan request. Empty/invalid history shows an explicit unavailable message, not a fabricated chart or live claim.
- Filters: retain the original ten defaults and their saved order, with up to five additional selectable slots (15 total). Existing selected filters are retained up to 15; previous remove/add behavior remains. Never infer an OI/news directional vote from missing or unverified data.
- Scanner Android chart: first run after migration defaults to the native BOT KING renderer, while explicitly selecting Lightweight is still possible. The native display cannot have a blank WebView.
- Production UI: Dhan-only visible source and broker dropdowns; Settings, generic help and option-chart visible captions refer to Dhan, not external legacy provider login. Archived source-compatible legacy backend/test paths remain in code, but are not selectable from the production UI. Full removal or isolation of legacy internal code is a separate audit gate; do not claim zero legacy references in the repository.

## Dhan Option Chain / OI / PCR / Max Pain audit
- Client uses Dhan-only `/dhan/option-expiries` and `/dhan/option-chain` for NIFTY, matching exact broker-listed expiry.
- Adapter validates numeric PCR and Max Pain, `source=dhan`, unverified freshness, and `signal_eligible=false`. If a seven-strike ATM window is returned, strikes, CE/PE OI, and premium/volume fields must meet strict input checks; missing prices stay missing rather than zero.
- Existing dedicated offline tests cover broker-listed expiries, rate limiting, option-chain route authentication, invalid chain handling, call/put OI PCR calculation, Max Pain and ATM windows, and prohibit any live directional vote from unverified options.
- **Not verified here:** a current live Oracle authenticated response, token validity at time of APK test, whether the seven-strike window is actually returned, or CE/PE premium candle history. Real Options/OI signal readiness stays WAIT until independently verified. No live order routing.

## Acceptance
- Offline regression suite must PASS on A3's final commit, including new dashboard chart/no-unwanted-card/Dhan-only/15-slot guards.
- Signed APK workflow must PASS all steps: full unittest, certificate SHA-256, `aapt` package, versionName and versionCode, artifact upload.
- Android smoke test: selected Dashboard symbols have native red/green mini charts when cached candles exist; 0/3 Dashboard card absent; Super Five and Candle Analysis remain; 15 active slots cap and preference persistence; Dhan-only Settings; Scanner white WebView issue gone on default native chart.
- Android/Oracle integration tests still needed for Dhan options and live freshness. **GitHub CI does not prove broker-side availability.**
