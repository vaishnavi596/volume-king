# BOT KING 2.1.0: final source audit before APK authorization

Date: 2026-11-04. Supersedes the source-state notes in [the earlier recheck](recheck-v2.1.0.md).

**Source test verdict: PASS. Release verdict: BLOCKED pending signing setup and deployment/device verification.** No APK was built, no production server was changed, and no real broker order was submitted during this audit.

## Preserved scope

The next release includes the 2.0.3 chart-state, field-width and number-format corrections on top of 2.0.2. No 2.0.2 main.py function has been removed. Existing four-page navigation, 50-company selection, Super Five, Paper trading/manual ticks, broker/server login, Yahoo fallback, option chain and metrics, persistence, backup and language tests remain in the suite.

The earlier report's statement that analysis_quality.py, scanner_engine.py and i18n.py were unchanged describes the earlier revision only. They are now intentionally extended for filter coverage, explicit counts and selected-symbol captions.

## Five new selected-symbol improvements

| Improvement | Implemented source behavior |
| --- | --- |
| Separate final caption | At the top of Scanner: exact selected symbol, chosen timeframe, and BULLISH / BEARISH / WAIT. Independent of the Super Five list and of the three-source combined card. |
| Transparent agreement | Displays bullish, bearish, neutral and unavailable counts, available/selected filter counts, directional agreement and the user's saved threshold. Agreement is not trade success probability. |
| Minimum coverage | At least 60% of selected filters must be available, with a minimum of three. At least 60% of available filters must be directional, with a minimum of three. Existing majority, trend/structure, candle quality and saved-threshold checks still apply. Insufficient coverage produces WAIT. |
| Higher-timeframe context | Selected-only confirmation: 1m→5m, 3m→15m, 5m→15m, 15m→1h, 30m→1h, 1h→1d. Shows AGREES, CONFLICT or UNCONFIRMED separately. It does not silently replace the user's selected timeframe. No higher timeframe is invented for 1d. |
| Freshness and refresh clarity | Source, last completed candle, data age and existing refresh status are visible. Stale, cached, failed or superseded selected data cannot retain a current directional caption. Caption freshness is checked while visible; refresh remains polling while the app is open, not tick streaming or an always-on service. |

Only completed candles are analyzed. At least 30 valid completed candles are required. Missing source volume is unavailable data, not evidence of bearishness. Super Five remains a separate 5m watchlist analysis; these changes do not claim 50-instrument simultaneous tick streaming.

Changing the agreement threshold invalidates the old selected result and marks prior ranking results historical, so an older signal is not retained under a newly chosen threshold.

## Other code corrections retained

- Full-width Lots field; wrapping of long labels; help wrappers follow hidden fields and Cash/Options selection.
- Exact selected quote/lot/expiry copying into Paper entries; current quote required; open Paper positions cannot have their plan inputs overwritten by a blocked new entry.
- Truthful chart loading/error/source state, stale option health, expiry provenance, HTTPS origin validation, and obsolete-fetch rejection.
- Correct negation boundaries for experimental headline cues.
- Separate manual LIVE controls, explicit arming/review, fresh exact-contract quote checks, server caps, durable order request IDs, reconciliation and cancellation. Concurrent duplicate submissions are fake-broker tested to send once.
- Form editing, app backgrounding/reset and session changes invalidate obsolete LIVE confirmations. An obsolete same-session arm response triggers a disarm attempt.

## Validation and its limits

- **165 offline regression tests pass**, including the 117 tests retained from the 2.0.2 baseline.
- Twelve selected-signal tests cover exact selection/timeframe, threshold changes, counts, missing coverage, stale/cache/failure states, confirmation conflicts and errors, obsolete responses, and English/Hindi page/control structure.
- Python compilation and target grammar compatibility, installer shell syntax and whitespace/conflict checks pass.
- No trained AI model, measured 70% win rate, completed backtest, actual broker fill, Android WebView certification or successful same-key upgrade is claimed by these tests.

## Three release gates still open

1. **Permanent Android signing:** GitHub preflight reported `SIGNING_NOT_CONFIGURED`. Both `ANDROID_KEYSTORE_BASE64` and `ANDROID_KEYSTORE_PASSWORD` must be configured, and the public certificate SHA-256 must be pinned in `config/android-signing.sha256`. The build workflow blocks debug-key fallback and key/certificate mismatches. The availability-check job returning success is not proof that secrets exist; its reported marker controls this conclusion.
2. **Gateway/manual LIVE deployment:** the new server addon has not been deployed to the existing production gateway. Verify owner authentication, broker access and real session behavior during the release/testing phase. Existing Paper automatic controls do not manage real orders.
3. **Authorized APK/device verification:** after the user authorizes building and signing is ready, verify startup, charts, selectors, persistence, exact broker contract, order review and actual order/position/cancellation state on the phone. Then verify a second higher-version APK signed with the same retained key updates in place. This requires built APKs and cannot be certified by this source-only audit.

## Feature backlog, not completed by this release

- Automatic live SL/target/trailing, alerts and unattended background protection.
- Scanner premium candidates derived from actual listed quotes instead of simulations.
- Chart overlays beyond EMA and drawing tools.
- Validated option trade-flow direction and fully validated candle/options/news combination.
- Broker integrations beyond Angel One, and fuller Hindi help/status coverage for the separate LIVE forms.

The user has not authorized an APK build in this phase. Keep changes on the review branch until the release gates and explicit build instruction are satisfied.
