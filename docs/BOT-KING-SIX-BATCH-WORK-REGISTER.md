# BOT KING — Six-Batch Work Register (2026-11-14)

This is the persistent handoff/checklist for BOT KING. Update the status only after verifying code, tests, Oracle deployment, and phone behavior separately. A commit is not a deployed fix.

## Batch 1 — Dhan data path, index LTP, watchlist refresh (ACTIVE)

**Scope:** 51 equity symbols + 3 indexes = **54 displayed instruments**. Preserve the equity-only 51-symbol scan, equity snapshot, and Super Five ranking. Index quotes/candles are separate from the equity snapshot. Do not count the three indexes as additional equities or claim exchange-timestamp-verified live data.

| ID | Work item | State / evidence |
|---|---|---|
| B1-01 | Dhan index mappings: NIFTY IDX_I/13, BANKNIFTY IDX_I/25, SENSEX BSE_I/51 | Backend mapping committed; NIFTY previously Oracle HTTP 200; BANKNIFTY/SENSEX **not deployed or verified** |
| B1-02 | Oracle read-only LTP for all three indexes | NIFTY previously passed; BANKNIFTY/SENSEX returned HTTP 422 before mapping; requires backed-up Oracle deployment and authenticated retest |
| B1-03 | Dashboard three configurable symbol/index cards; independent index refresh | Index quote path added, serialized, one cycle per >=60s, last-good retained, truthful missing-quote message; CI and Android verification required |
| B1-04 | Watchlist shows 51 equities + three persistent index cards = 54 instruments | Separate index cards added above existing capped equity lists; index cards excluded from 51-equity snapshot and scan; Android UI verification required |
| B1-05 | Watchlist refresh, polling cadence, UI update, cache age, reconnect/resume | Manual, 30s poll, index change detection, and resume refresh added; index refresh decoupled from snapshot cooldown; foreground-only operation, **not continuous background service**; Android verification required |
| B1-06 | Regression and integration: index mapping, LTP, refresh, cache and 54 display | CI green at f0122cd; new rate-guard and status tests added, newest CI pending; Oracle deployment, phone verification, signing/version bump and APK still pending |

**Batch 1 acceptance:** authenticated read-only Oracle LTP for each mapped index; 51 equity snapshot remains independent; 54 display without adding indexes to equity ranking; watchlist refreshes on schedule and after resume; last valid quotes retained but labelled unverified; no Yahoo/Angel fallback; regression green. Keep live order routing disabled.

## Batch 2 — Historical candles and charts (QUEUED)
- Audit prior screenshots: only two/three equities displayed candles; many symbols lacked candles.
- Verify 5-minute and other selected timeframe candle availability for all 51 equities and three indexes; distinguish missing history, rate limiting, cooldown, and chart UI errors.
- Chart search/select for NIFTY, BANKNIFTY, SENSEX; preserve candle timeframe isolation from scanner quotes.
- Validate candle timestamp/freshness; historical_unverified is not a live signal.

## Batch 3 — Scanner, Super Five, signals (QUEUED)
- Audit the two previously reported scanner screenshots/issues and their error/progress states.
- Validate 51-equity scan completion, priority scheduling, Super Five ranking, bullish/bearish votes and paper-bot behavior.
- Avoid per-equity request fanout, duplicate polling and misleading confidence; keep real orders disabled.

## Batch 4 — Dhan options and market metrics (QUEUED)
- Listed expiries, option chain, OI, PCR, Max Pain, premiums, source and freshness.
- Preserve expiry validation and 422 on invalid expiry; fail closed when signal eligibility is false.
- Read-only options integration; no implied automated real trading.

## Batch 5 — Watchlist UI, presentation and usability (QUEUED)
- Five saved lists, filters, per-row bullish/bearish percentages, chart status, diagnostics, compact navigation.
- Coordinate presentation with Batch 1 index cards; do not duplicate the data acquisition work.
- Persist Dhan connection preferences and protect secrets.

## Batch 6 — End-to-end release (QUEUED)
- Run backend, offline regression and Android build checks; investigate failed CI rather than assuming success.
- Verify versionName **and** versionCode advance, signing identity, install/upgrade path, release artifact and phone test.
- Check Dhan-only provider isolation, lifecycle recovery, 54-instrument display and 51-equity scanner; live orders OFF.

## Execution discipline
Work on Batch 1 first; track fixes in small related commits (2–4 items per pass). Mark a task DONE only when relevant tests and real deployment/phone verification support it. Keep backup before Oracle production edits. Update this register whenever batch scope/status changes.


### Batch 1 grouped-audit note
- GitHub branch: `botking-b1-index-mapping-20261114`; draft PR #111. Commit is not deployment.
- Newly found/fixed: index polling was blocked by equity snapshot cooldown; concurrent or frequent index polling risk; stale dashboard warning incorrectly claimed BANKNIFTY/SENSEX mapping unverified after mappings were added.
- Never expose pairing credentials or overwrite Oracle `/opt/bot-king-server/server.py` without comparing with repository and taking a timestamped backup.
- Acceptance requires actual HTTP 200 + positive LTP for all three indexes, verified watchlist/dashboard display, and a clean new versioned signed APK.
