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

## Joint patch 2 — selection, freshness and automatic handoff

This continues groups 2–5 above; it does not create another list of numbered fixes.

- Scanner, Home summary and completed-candle clock are published together. A
  cached replay keeps the original calculation time rather than pretending a new
  source update arrived. Selecting an unloaded symbol clears the old report and
  clocks immediately; changing provider clears the old summary and restarts the
  eligible automatic loop.
- A single newest-5m-history selector is used for Scanner handoff, shared analysis
  and index cards. It ranks actual candle receipt separately from LTP receipt.
  Historical candle analysis can remain visible when an index LTP is unavailable.
- Display-time gates demote expired, disconnected, closed-session and mismatched
  provider evidence. A UI refresh cannot manufacture a verified signal. Invalid
  timestamps cannot reach date rendering; source-mismatched votes are excluded.
- Legacy `scanner_live=False` no longer stops Dhan's automatic analysis paths or
  produces an OFF caption for a running shared feed. Watchlist price cadence,
  request lock, cache durations and provider cooldowns are unchanged.
- Slow optional news does not prevent a completed filter result from receiving
  newer shared candles. Changing selection releases obsolete news work within a
  short context check; an already-running RSS worker may still finish, but cannot
  publish its result into the newly selected symbol.
- Chart overlay visibility is separate from the central Analysis/Chart/Both
  setting. Hiding an EMA line cannot silently change analysis selection.
- A failed candle request remains an active audit/report failure when only older
  cached candles are available. It clears only after a matching candle response
  received after that failure; old local re-analysis cannot turn it into success.
  Last-available evidence remains explicitly historical and non-actionable.

Validation adds real-Flet callback tests for selection clocks, provider switches,
legacy automatic settings, news cancellation, cross-surface history selection,
bad-data demotion and failure recovery, plus pure presentation-gate tests. These
remain offline tests, not real broker/device certification. Build stays deferred
until the final combined audit; no release version or build workflow is changed.

## Remaining joint batch — full coverage and background diagnostics

This closes additional source gaps within the existing groups 2–5:

- The Dhan history scheduler always targets the fixed 51 equities plus three
  indices, even if saved Watchlists are empty or the user removes a stock from a
  list. Displayed Watchlists and their price cadence remain independent.
- Background equity and index candle failures use the same failure registry as
  selected Scanner requests. Last-available evidence is immediately demoted and
  cannot become live through local cached re-analysis. A newer matching candle
  response clears both the active failure and its stale per-symbol error.
- System Health reads the same 54-symbol audit as central filter settings.
  Pending and insufficient coverage remain explicit; error history is labelled
  separately and may contain recovered incidents. Duplicate symbol/audit error
  notices are not counted twice.
- Optional premium simulation failures no longer overwrite successful technical
  candle coverage with a filter failure.
- The Oracle read-only audit previously excluded only NIFTY, which incorrectly
  left two indices in its supposedly 51-equity list. The default is now exactly
  51 equities; `--all-symbols` tests all 54. `--date YYYY-MM-DD` selects a known
  completed past session. Each valid candle response must also produce all ten
  default filter rows. Requests remain sequential, spaced 1.5 seconds apart,
  and stop on HTTP 429/authentication/transport failure. No orders are called.

Server-side acceptance command (on the existing Oracle checkout):

```bash
python3 backend/audit-dhan-51-candles.py --all-symbols --date YYYY-MM-DD
```

Replace the date with a known completed trading session; holidays are not inferred
from empty data. This command has not been run against the user's live Oracle
instance in this workspace. Static app/gateway mapping-name and segment-ID
consistency is tested; that is not a new instrument-master verification.

Tests exercise the actual complete app scheduler with 54 supplied candle feeds
and empty Watchlists, active failure/recovery in System Health, and the complete
54-symbol server-audit program with mocked HTTP, including immediate rate-limit
stop. Real broker freshness, physical Android layout/latency and server deployment
remain acceptance gates. No additional numbered improvement groups are created.

## Final GitHub consolidation and server handoff

- Programmatic symbol changes (including a Super Five card tap) now invalidate
  the selected scan context even without a dropdown event. This clears the old
  report and makes obsolete in-flight work schedule the latest selection.
  Intraday period normalization happens before that context is saved.
- The full-scan ranking phase reuses the newest matching shared history when
  its first-pass history succeeded. It cannot overwrite a newer selected-chart
  result with an older cycle snapshot, and does not retry a failed fetch.
- `backend/run-scanner-audit.sh FULL_COMMIT_SHA [--date YYYY-MM-DD]` downloads four
  diagnostic sources from that immutable GitHub revision into its own temporary
  directory. It uses the existing server Python environment when available,
  runs the 54-symbol read-only audit, and removes its temporary directory.
  It does not install files, edit configuration, restart services or place orders.
  The existing pairing key is read internally by the audit and is never printed.
- The runner is tested with fixture downloads and `--help`, so its test does not
  contact either GitHub or a broker. Invalid revision strings stop before download.

GitHub implementation is ready for server acceptance after its regression checks.
On Oracle, run the pinned runner and return its output first. A successful offline
suite does not establish real feed freshness or mobile performance. Review the
server result before the final APK build; then validate the installed app. News,
Futures and Options still require their real evidence sources and are never
silently treated as verified by a successful candle test.


## Oracle historical acceptance — user-supplied run on 2026-11-15

The user ran the pinned read-only runner at revision
`b35694a71403baf425d472606fbed668cb7c4521` and supplied the complete output:

| Check | Reported result |
| --- | --- |
| Requested session / timeframe | 2026-11-13 / 5m |
| Symbols | 54 valid; 0 empty; 0 invalid; 0 HTTP errors |
| Default filter rows | 10/10 available on each symbol: 540 total evaluations |
| TCS | HTTP 200; 71 bars; 10 available filters; historical BULLISH bias |
| Indices | NIFTY, BANKNIFTY and SENSEX each returned 74 bars and 10 filter rows |
| Orders | No order endpoints called |
| Exchange freshness | Not verified live |

This passes the tested historical local-server API and pure filter-calculation
path for all 54 symbols. It does not establish complete-session coverage,
current live prices, public HTTPS/Nginx transport, prediction accuracy, News/
Futures/Options evidence or Android rendering/latency. No server deployment is
required by these app-only changes.

With the previously requested final-build stage now reached, the next sequential
APK candidate is 2.3.111. Permanent-signing and version-code checks remain in the
existing workflow. Physical update-install, selected-symbol handoff, all 54
report coverage, readability and runtime refresh tests remain mobile acceptance
gates after the APK is built.
