# BOT KING — Joint Repair Gap Audit (2026-11-16)

**Evidence scope:** GitHub source, journal, work-result tracker, release policy and user-reported phone failures; NOT an Oracle host test or a new APK. **Single mobile only**; defer dual-mobile deployment. Dhan-only read-only market-data/PAPER, `live_orders_enabled=false`. New APK only after all scoped gates.

## Confirmed owner timeframe policy (latest correction)
- **Dashboard**: three index cards and three selectable analysis cards default to genuine completed **1-minute** candle Bullish/Bearish; do not relabel a 5m vote as 1m.
- **Scanner**: vote, candle and filter analysis follow user's **selected timeframe** (1m, 3m, 5m, etc.), isolated by symbol/timeframe/provider generation.
- **Watchlist**: **3-minute**, NOT 5-minute. This explicitly supersedes the preceding journal entry that preserved Watchlist 5m pending confirmation.
- **Super Five**: retain independent 5m ranking until any further explicit change; a Dashboard container must not silently change its ranking calculation.
- **3m backend gap:** `src/main.py::timeframe_spec` knows 3m; `aggregate_3m` is already used for Yahoo; current **Dhan** `fetch_market_data_uncached` permits only 1m/5m/15m/1h. Watchlist `watch_signal_cache`, `fill_watch`, `watch_visible_tick`, `refresh_shared_analysis` and 5m ranking are currently coupled. Implement actual 3m completed bars from Dhan 1m if Dhan direct 3m is unsupported, using exact source and bucket checks, or a verified permitted Dhan 3m feed. A 5m vote may not be relabeled 3m, and a 3m unavailable state must not be filled with a 5m result. This requires independent history/cache and budgeted scheduling.

## Six joint work batches (complete in sequence, journal actual evidence after each)

| Batch | Scope and new findings | Exit gate |
|---|---|---|
| **B1 — Baseline + indices** | Actual Oracle read-only route, auth, collector enablement/age, quota and 429 audit; three index LTP and disappearing red/green Dashboard; historical fallback patch `050cc5ad` and test `1ea0d0cc` | Exact CI head PASS and Oracle/source state separately labeled; three-index mobile not yet PASS |
| **B2 — Timeframe + candle continuity** | Dashboard 1m independently; Scanner selected TF; **Watchlist 3m**, Super Five 5m; per-symbol TF cache, valid completed bars and white/flashing candle recovery | 1m/3m/5m isolation tests, no false live votes, 429 safe, device QA |
| **B3 — SDC-4 workload controller** | Dynamic 70-slot watchlist subscriptions with current 51→31 equities if 20 removed; keep selected Dashboard/Scanner/Super Five/Options references; four logical lanes, measured rate/bytes/cache/age | Pilot source `src/active_symbol_budget.py` commit `211cee48`, tests `62c09227`; no production polling yet; prove actual request reduction |
| **B4 — Filters + derivative data** | Four independent news/futures/options/candle factors and five specific filters OI support/resistance/max pain/PCR/candle; stock PCR eligibility, expiry, OI, 54 verified coverage vs 70 saved | Real mapped Dhan producer and API proof, WAIT unless verified, no made-up percentages |
| **B5 — Page consistency + resilience** | Watchlist 5 lists and 70 unique saved equities, Super Five shared visual, scanner switching/background/resume, status Error Doctor, market-closed/holiday calendar, first-login and last-good retention | Source CI + actual mobile smoke, separate active/stale/unverified labeling |
| **B6 — Release gate** | Final source CI at intended SHA, guarded Oracle backup/diff/deploy/health, selected read-only Dhan probes, one incremented signed APK, actual single-phone acceptance | Release only after verified green gates, versionName AND versionCode, no live orders |

## Other gaps not to lose
- Dynamic 70 saved equity quotes ≠ verified 70 historical/derivative Scanner symbols; registry and Dhan entitlement checks are outstanding.
- 54 configured markets ≠ 54 functioning filters; company/index PCR and five-filter Oracle producer remain unverified/not configured.
- Current 51 fixed equity snapshot still fetches fixed roster even after saved list removal: no real API/byte savings until source subscription/collector changes.
- Concurrent 180s history cache misses may cause unnecessary upstream work; future dual-mobile feature code is not evidence of deployed cache. In present single-mobile mode, avoid extra load.
- UI-local ~2s repaint is not Dhan exchange price freshness; quote index/stock cadence 60s, assessment and historical ~180s in source; Oracle collector production mode still unknown.
- Dhan 429 cooldown and protected token status, expiry/chain errors, fresh/history labeling, scanner chart white on symbol switch and red/green absence remain device acceptance gates.
- The source fallback patch for three Dashboard bars does not itself fulfill Dashboard 1m request; runtime data may still legitimately be unavailable.

## Work begun this session
- `050cc5ad`: Dashboard red/green last valid Dhan historical fallback when unusable nonempty current candle history; no fabricated live signal. `1ea0d0cc`: source regression test. CI/phone not yet verified.
- `211cee48`: pure active symbol workload planner only (no live network calls/deployment). `62c09227`: test cases 54→34 and retained consumer symbols. Exact CI not yet verified.
- Next: finish watchlist 3m data path with true 1m→3m aggregation and timeframe-specific cached analysis, then Dashboard 1m; add regression before changing polling, respecting Dhan limits and release gate.

**Status:** Source gap audit complete for the named pathways only; cannot truthfully assert no other runtime error exists before Oracle and Android end-to-end tests.


## B4 FILTER FRAMEWORK — mandatory full acceptance (owner 2026-11-16)

**Do not call all five filters 100% repaired from a GitHub regression PASS alone.** This is a release-blocking feature, and it must not be skipped while completing B1–B3. There are two related but different existing concepts: (a) selectable Scanner technical filters (the up-to-10 active slot editor and timeframe-aware candle votes), and (b) Oracle five assessment filters. They must be labeled separately and composed without double counting.

### Five Oracle assessment filters, all individually gated
| Filter ID | Data contract | Required actual success proof |
|---|---|---|
| `oi_support` | Per-symbol, listed-expiry option-chain OI and strike/underlying mapping | Correct valid strike/support, timestamp and OI evidence |
| `oi_resistance` | Same-chain OI resistance | Correct mapped resistance, timestamp, no stale/phantom contract |
| `max_pain` | Supported strikes CE/PE OI calculation, exact expiry | Reproduce on bounded fixture and authorized mapped broker chain |
| `pcr` | Put OI divided by Call OI, valid nonzero denominator | Exact mathematical test and per-equity/index real entitlement, WAIT otherwise |
| `candle_trend` | Real completed 1m/3m/5m candles as required by consuming page | No wrong timeframe, malformed OHLC, partial bar or historical vote marked live |

### Four independent factor categories
- `news`: traced symbol-specific published headlines and timestamps, no fabricated sentiment.
- `futures`: eligible and mapped futures instrument, price/volume/OI source; not derived blindly from cash LTP.
- `options`: actual chain and money-flow inputs, preferably bounded near-ATM window, no unsupported entitlement assumptions.
- `candle`: completed historical technical indicators with chosen page's timeframe; avoid counting identical technical votes twice as independent factors.

**Acceptance matrix**: for NIFTY/BANKNIFTY/SENSEX, default fixed equities, and each selected custom equity, test source name, symbol, security ID, exchange segment, expiry where relevant, timeframe, input timestamp/freshness, available/unavailable status, numeric domain, score range (only if genuinely defined), common Bullish/Bearish rendering and red/green continuity; valid error, 429 and stale states remain WAIT with last-good historical data clearly marked. Test no option entitlement for unavailable symbols, no source fallback, zero orders. Cross-check Dashboard 1m, Scanner selected timeframe, Watchlist 3m and Super Five 5m.

**Current evidence:** `src/shared_assessment_ui.py` has exact IDs `oi_support, oi_resistance, max_pain, pcr, candle_trend` plus factor keys `news,futures,options,candle`. It is a strict **presentation/validation** client; it explicitly says `News/Futures/Options/Candle: no verified 0–100 scores` and returns `WAIT • server producer not configured`. This protects against fake signals but does not produce real scoring inputs. The existing technical Scanner filter editor and 5m signal votes are separate. **B4 is OPEN, not functional PASS.** Required: actual Oracle data producer and authenticated bounded source parity, independent score definition, tests and mobile acceptance. Do not artificially populate five values to remove WAIT.
