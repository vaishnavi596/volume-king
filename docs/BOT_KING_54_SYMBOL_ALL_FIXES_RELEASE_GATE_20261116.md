# BOT KING — 54/54 Historical-Fix Release Gate

Date: 2026-11-16. Status: **BLOCKED — source universe fixed; feature/runtime evidence incomplete**.

## Coverage contract

The fixed Dhan roster is **51 NSE cash equities + NIFTY, BANKNIFTY, SENSEX (3 indices) = 54 distinct symbols**. This is NOT 54 cash equities. Apply all shared fixes to all eligible members of this roster. Do not infer that all 51 cash equities have listed F&O options; fail closed for no listed expiry, missing entitlement or incomplete chain. Preserve Dhan-only, broker rate limits, separate index batch, 30s on 429, cached last valid data and paper-mode read-only orders.

**APK release is blocked** until previous as well as current fixes are audited. A 54-symbol roster test by itself does not prove 54 live data or filter coverage.

## Historical improvements to regression-check on *each* new APK

| Feature / historical issue | Expected universal rule | Source evidence currently | Oracle/device acceptance |
|---|---|---|---|
| Fixed symbols | Exactly 51 equities + 3 indices, distinct, same scanner/shared filter eligibility | `tests/test_botking_unified_54_symbol_contract.py` added | **NOT YET PROVEN** 54/54 device |
| LTP + independent index quotes | All 51 cash quotes checked in bounded batch; NIFTY/BANKNIFTY/SENSEX fetched independently, no watchlist-block | Dedicated batch paths exist in client source | **UNVERIFIED** fresh complete response |
| First refresh + auto refresh | prompt first result, bounded 180s auto cadence, 30s manual guard, countdown where applicable | Historical app test indicated initial refresh delays | **OPEN** phone acceptance |
| Candles 1m/5m/15m | Same candle-rendering and retention semantics for each symbol, with index-specific Dhan segment | Previous source/mobile report had disappearing candles | **OPEN** end-to-end |
| Scanner / Super Five | Shared signal/candle logic, no partial-scan reset, preserve last good on 429/background | Existing common helpers referenced from both | **OPEN** 54-symbol snapshot + five candidates |
| Five-filter Oracle assessment | Same five IDs and four factors per selected symbol; unavailable if data not validated | GitHub backend `/v2/assessment/{symbol}` is a **known placeholder**; mobile poll only selected Scanner/Options/Bot symbols | **FAIL/UNVERIFIED** real producer and 54/54 per-symbol coverage |
| Options/PCR | Uniform eligibility check by symbol, but only request Dhan-listed expiry and chain for actually eligible underlying | Mapping-only helper; selected-symbol requests, no full fanout | **UNVERIFIED** on equities; do not show fabricated PCR |
| News/Futures/Options/Candle scores | Proven data source/freshness for each factor before numerical directional score | No verified four-factor producer | **BLOCKED** |
| Error Doctor / Health | Clearly distinguish active vs historical errors; same error categories per symbol | UI and audit source checks exist | **OPEN** mobile check |
| Background/resume and caches | Preserve last-valid quotes/candles for all 54; resume must not flood provider | Source has generation/cooldown guards | **OPEN** mobile regression |
| Version / installation | New versionName, Android versionCode, visible UI version and signed upgrade | Previous APK artifact #645 was signed; not accepted on device | **BLOCKED — NO NEW APK** |

## Acceptance ledger required before building

For each of the 54 symbols record **symbol, type (equity/index), mapping status, quote status and age, 1m/5m/15m candle status, scanner status, shared five filters (with unavailable reason), individual factor evidence, option expiry/chain/PCR eligibility, API errors, cache retention and resume behavior**. Permit `UNAVAILABLE` when broker truly does not support an instrument/option, but require the reason. The three index sources must be validated independently, not counted as successful just because 51 cash equities passed.

CI evidence, Oracle deployed-source SHA + collector health, and on-device observations are separate columns. All must be documented in `docs/BOT_KING_WORK_LOG.md` and `docs/BOT_KING_WORK_RESULT_TRACKER.md`. No numeric five-factor probabilities without source/age. No 54 option-chain fanout. Release decision stays **BLOCKED** pending true Oracle/server and mobile evidence. Android APK is intentionally not built.
