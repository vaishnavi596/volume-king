# BOT KING — filter and refresh consolidation

Baseline: `cde0d6aa6d48464a9fa0eaa55f6b41d898a47074` (installed candidate 2.3.110).
Scope: 51 equities plus NIFTY, BANKNIFTY and SENSEX. Number related findings
under these five groups; do not count every caption or symptom as another fix.

| No. | Consolidated change | Source implementation | Remaining acceptance |
| --- | --- | --- | --- |
| 1 | Central filter settings and readable compact controls | One filter editor in Settings; Scanner links to it. Responsive symbol/candle/period row, collapsed premium simulation inputs, no manual Scanner refresh button. Hidden fields no longer reserve help rows; reused wrappers follow visibility. Text helper minimum 14; principal symbols/prices 16; no fixed control heights. | Actual Android font scaling, 360/420dp width, touch and scrolling checks. 90% occupancy is a design goal, not a measured claim. |
| 2 | Complete per-symbol filter reporting | Selected filters retain explicit unavailable/Chart-only rows on incomplete analysis. Audit distinguishes analyzed, insufficient, error and pending, scoped to provider/settings and timeframe. Candle failures include symbol and stage. | Real gateway input for all 54, including TCS; verify instrument IDs separately. Analyzed does not mean verified live. |
| 3 | Coordinated data and analysis updates | A local 2-second change check reuses available 5m candles, detects completed OHLC revisions and filter changes, and skips unchanged inputs. New history results publish without waiting for a full cycle. Separate candle receipt metadata prevents LTP receipt time from winning candle selection. Other Scanner timeframes wait while the shared history scan is active; existing HTTP lock/cooldown and 30-second automatic request floor remain. | Measure server-to-app-to-display latency and provider capacity. No promise of new upstream data every 2 seconds. Existing history/cache cadence has not been accelerated blindly. |
| 4 | Shared display updates | Watchlist signal cache, Super Five and index views receive shared analysis; selected 5m Scanner report also updates. A busy selected scan receives the latest shared report on the next local pass. Price polling intervals and navigation destinations remain. | Device consistency between Scanner, Watchlist, Super Five and index cards; resume/background behavior. News/Futures/Options availability is not invented. |
| 5 | Coverage and regression audit | Settings has a 54-symbol 5m technical/candle coverage panel, per-symbol stage and reason, candle count and measured local calculation duration. Runtime tests supply candles for all 54 without broker I/O; unchanged inputs, corrections, settings changes and provenance are checked. | Actual market/session data, real network timing and APK/mobile acceptance remain pending. |

## Validation

- GitHub regression run `43666758251` passed for batch commit `6676dc1`.
- Full offline unittest suite: 674 tests passed before the final candle-receipt
  metadata regression was added; subsequent targeted tests cover that change.
- Actual Flet controls are used in runtime tests. These are not Android screenshot
  or live brokerage tests.
- Existing source-only tests were adjusted for the filter editor's intentional
  move, the local 2-second interval and the serialized alternate-timeframe guard.
  Two existing pytest source slices also needed to include nested scan helpers;
  reading `connected` is allowed, while row-level HTTP calls remain forbidden.
  Additional pre-existing pytest expectations were corrected to inspect all three
  index warmups and the index card helper on Dashboard. The Watchlist caption
  now says 60 seconds, matching the existing poll throttle; the rate is unchanged.
  Super Five still ranks 51 equities, while shared coverage includes all 54.
- No release version change, APK workflow dispatch, live orders or Oracle
  deployment is included. Source pushes run regression workflows only.

## Deferred, not silently marked complete

The five engine slots remain Technical, Candle, News, Futures and Options. This
batch does not create unavailable derivatives/news feeds, prove independent
engine evidence or convert agreement percentages to accuracy. Running-candle
provisional signals, streaming feeds and server rate changes need separate
validation within the same groups above rather than inflated fix counts.
