# Live-first five-page layout (2.2.0 preparation)

Source changes only. No new APK was built and the production gateway was not changed in this task. The installed 2.1.0 APK remains unchanged until the user authorizes a later build/update.

| Page | Role |
| --- | --- |
| Home | Selected analysis, Super Five, source/freshness and a link to the real account/order page |
| Live | Option chain, linked contract selection, editable LIMIT price, manual real-order arming/review/confirmation, order records, positions and cancellation; option chart and OI/PCR metrics on the same scrolling page |
| Settings | Broker credentials/connection, data mode, general backup/history, signal threshold and diagnostics |
| Scanner | Selected-symbol timeframe analysis, completed-candle chart, filters and separate higher-timeframe context |
| Paper | All practice contract/risk/strategy/manual-tick/protection/order controls, Paper positions/history and educational strategy selector |

Existing indices 0–3 remain stable; Paper is index 4. Navigation and saved last-page/scroll state now support five pages. Existing Paper positions and preferences are retained, and Paper actions never call the real-order endpoint. Saving general connection settings no longer validates hidden Paper fields; Paper validation belongs to its own page.

## One live selection

Tapping a CE/PE premium selects the exact strike/side in the live form. Only a recent quote (no more than 90 seconds old) can populate an editable LIMIT price; an old quote leaves that price blank. Selection never submits an order or opens a Paper position. Real orders still require server validation, explicit arming, a fresh review and final confirmation.

The main option symbol/expiry picker is linked to the live form. The live strike/type also drive the option-chart context, removing duplicate visible strike/type inputs. Changing the symbol or expiry clears old strike/price/quantity and invalidates the previous confirmation. Cash uses its own visible symbol input. API credentials, arming acknowledgement and live price are not persisted as automatic authorization.

## Data mode

New installations default to Broker API, and successful API login selects Broker API. Existing explicit preferences are retained until changed or reconnected. In Broker API mode a failure never silently requests Yahoo; an available saved snapshot is labeled historical and cannot generate a new current signal/order. Auto/Yahoo remain explicit optional choices in Settings. Existing live-data polling and completed-candle checks are retained; this change does not add WebSocket streaming or an always-on service.

## Verification and remaining gates

174 offline tests pass, including nine new tests for page isolation, fifth-page persistence, live contract/price copying, stale quotes, invalidation on symbol/expiry changes, chart linkage, broker-only routing and login behavior. Existing navigation/language/save-scope assertions were updated for the user-requested relocation; Paper and live-order engine behavior remains covered. Python compilation and whitespace checks pass.

Manual LIVE server deployment and actual broker/device verification remain outstanding. Automatic live SL/target/re-entry/trailing and unattended bot protection are not implemented by moving Paper controls. They remain clearly labeled unavailable. Permanent signing key/certificate is unchanged; use the retained owner key for any later authorized APK.
