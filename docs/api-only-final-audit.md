# API-only live app: final requirements audit

Requested 2026-11-04. **Report-only checkpoint:** no application source, APK, broker credentials or production server was changed by this audit. The installed APK is 2.1.0; five-page 2.2.0 preparation remains unbuilt. The earlier 174-test result applies to that existing source, not to the new functionality proposed here.

## Verdict

The requested API-only, fully functional live-data application is **not complete**. Yahoo paths still exist; scanner premium candidates are modeled; market updates use polling; Paper strategy marks are manual; automatic real-order protection and an AI order-management engine are not integrated. Broker login and moving controls between pages do not complete these features.

All visible controls should perform a defined, verified operation. Unavailable data must show its cause; market closure, an expired session or missing broker data must not be represented as an always-green LIVE value.

## Twelve work groups

| # | Required change | Current evidence/status |
| --- | --- | --- |
| 1 | Remove Yahoo completely from application data workflows | `main.py` still has Yahoo/Auto provider choices, `get_yahoo` fallback, old chart paths, Yahoo-specific history limits, restore aliases and captions. Remove these paths, not just their label. Migrate saved provider/chart settings to broker-backed modes. |
| 2 | Common real-time broker data service | Existing data refresh is polling while the app is open. Add streaming/subscriptions where supported, controlled REST snapshots/history and reconnect handling; expose actual source timestamp, received time and freshness. Respect broker limits across the watchlist and selected instrument. |
| 3 | Make Home a genuine account/market summary | Keep selected candle/combined analysis, Super Five, market overview, session and news. Replace the large capabilities block with compact data/session/order-permission statuses. Add genuine broker positions/P&L/order summary; missing data is unavailable, not zero. Paper details stay on page 5. |
| 4 | One complete Live/Options workflow | Contract selection, chain, chart, verified lot size, premium, quantity, strategy settings, actual order state and positions belong on the same page. Prepared code covers linked selection and manual confirmed orders; automatic bot management and protection remain incomplete. |
| 5 | Replace modeled premium candidates | `scan_market()` still generates theoretical strikes/premiums and decay scenarios. Match exact contracts from the current broker instrument master, then obtain actual current quotes. The present up-to-nine-strike window is not enough to claim a complete budget search. Expand search with defined limits and report searched coverage. |
| 6 | Add Greeks, volatility and liquidity data | The adapter currently exposes premium, OI, volume, time, token and lot size; it does not expose best bid/ask or connect the Greeks endpoint. Add available depth, Delta/Gamma/Theta/Vega/IV, exact contract matching, units and freshness/provenance. Missing fields are unknown, never a fabricated low-risk score. |
| 7 | Budget-aware candidate comparison | Separate per-unit premium range from total entry-cost budget. Compare only current listed contracts using direction, spread/depth, liquidity, expiry, Greeks and affordable listed lots. Show why a contract qualified or was rejected. No matching contract means no candidate, not an invented strike/price. |
| 8 | Separate analytics from authorized execution | Current engine is rule-based; headline cues are experimental, not a trained all-app controller. Add an explicit analysis service/context and clearly defined permissions. An analytic score cannot bypass account, freshness, quantity, cash, price, idempotency and exposure checks. Manual confirmation remains the implemented path. Any future Auto mode needs its own explicit authorization and tested limits. |
| 9 | Broker-confirmed order monitoring and live protection | Reconcile acceptance, partial/complete fills, rejections and cancellations with broker records. Implement any SL/target/trailing/re-entry/partial-exit behavior using actual supported broker operations and filled quantity. A planned SL field is not proof of a working protective order. Persistent journal, reconnect/restart behavior, order deduplication and emergency controls must be tested. Existing source has manual LIMIT placement/reconciliation/cancellation, not automatic protection. |
| 10 | Paper practice using the same real data, independent simulation | Fifth-page controls are prepared, but runtime evaluation still consumes manual marks. Add exact Paper-contract broker quote updates and simulated fills/SL/target evaluation without a live order call. Keep Paper contract state, limits and ledger independent from Live. Pause on stale/missing quotes. |
| 11 | Honest settings and provider capabilities | Remove duplicated capability blocks and nonfunctional mode controls. Keep broker/session/language/common preferences in Settings, detailed strategy settings on their own Live/Paper pages. Angel One is the implemented broker; other broker names do not imply integration. Future adapters must normalize contracts, data, Greeks and order capabilities. |
| 12 | News and end-to-end acceptance tests | Current news is public RSS and experimental phrase cues, not an Angel One market-data endpoint. If every external input must be API-backed, choose/integrate a documented news API with source/time and separate status. Validate the entire flow on recorded/fresh data, reconnects, malformed/missing data, and device behavior; measure strategy results separately with costs and out-of-sample checks. Existing tests do not certify the proposed automation or accuracy. |

## Home status rule

Display separate statuses for: data LIVE/stale/market closed; broker session connected/expired; real-order permission disabled/disarmed/armed; actual protective order acknowledged/absent. A data connection must not imply order permission or protection. A market closed indicator can coexist with valid last-session history. For absent inputs, show unavailable and an actionable explanation rather than a decorative caption.

TradingView Lightweight Charts can remain as a rendering library supplied only with broker candles. Removing Yahoo does not require removing this chart renderer. Legacy `BOT KING / Yahoo` naming and Yahoo data paths must be removed or migrated.

## Requested premium selector

- User example: NIFTY premium range INR 100–200 **per unit**, editable by the user; stock options use their own selected range and total capital budget. Confirm these as separate UI fields rather than treating a displayed premium as the full cost of a lot.
- Estimated entry debit = actual limit/purchase price × verified current units per lot × selected lots + estimated charges. Show the charges/estimate separately and refresh them when available. Do not hardcode current lot sizes.
- Start with a supported direction from completed candles on the selected timeframe. Show higher-timeframe conflict separately. A 70% indicator-agreement score is not a 70% chance of profit.
- Search actual current broker-listed contracts and quote coverage; rank only after freshness, quote/depth and budget checks. Show contract, expiry, CE/PE, bid/ask, premium, lot, estimated debit, liquidity and available Greeks with provenance.
- Assess time-decay exposure with available Theta, expiry and premium context; assess direction sensitivity with Delta and volatility sensitivity with IV/Vega. These are conditional sensitivities, not a promise of a slowly declining or profitable premium. Absolute low price alone is insufficient.
- If quote, liquidity, Greeks or required coverage is missing, either explicitly label the comparison incomplete and block automated selection, or return no verified candidate. Do not fill gaps with the current simulated model and call the result live.
- Do not map every bullish underlying directly to an unconditional call-buy recommendation or every bearish underlying to an unconditional put-buy recommendation. Eligibility, timeframe conflicts, costs and risk checks still apply.

## Primary documentation checked

- [Angel One SmartAPI documentation](https://smartapi.angelone.in/docs/ResponseStructure): FULL quotes include depth; the `marketData/v1/optionGreek` endpoint returns contract Greeks and IV. Its documentation describes Greeks support for NSE; coverage and freshness must be verified for the actual selected contract and account rather than assumed for every exchange.
- [NISM equity derivatives FAQ](https://www.nism.ac.in/wp-content/uploads/2021/02/Equity-Derivatives-FAQ-document-1.pdf): option value includes time value, which decays toward expiry; time decay works against option buyers. This supports checking decay exposure, not promising a premium that cannot erode.
- [NISM derivative risks](https://www.nism.ac.in/investor-educations/understanding-risks-while-trading-in-derivatives/): liquidity and operational risks can prevent timely or fairly priced exits.

## Implementation order before another claimed complete live release

1. API-only provider migration plus broker data freshness/reconnect behavior, compact Home and actual positions.
2. Actual listed-contract quote/depth/Greeks pipeline and budget-based candidate comparison.
3. Separate real-data Paper engine and real-order monitoring/protection, with independent state and explicit execution permissions.
4. Complete news/provider integrations as scoped, remove unsupported/decorative controls, then run functional/device and broker acceptance checks.

No application edits, additional automated strategy deployment or APK build were performed for this report.
