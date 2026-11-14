# BOT KING Batch 4 — Five-Engine Intelligence: Audit and Design

Status: UI placement and compact Watchlist implemented in source; five-engine scoring/data integration pending; Batch 4 does not claim all five live feeds are available. Futures live API integration is explicitly deferred to Batch 7 (`bin/batch7-futures/README.md`). No live-order enablement, no change to the Batch 1–3 APK release gate.

## Agreed product contract (2026-11-14)
- Five **independent** directional scales: TECHNICAL, CANDLE / PRICE ACTION, NEWS, FUTURES, OPTIONS. Each has bullish and bearish evidence percentages only when sufficiently supported. Each displays directional bias (bullish/bearish/mixed/unknown), score, data confidence, timestamp, and reason.
- Scores measure *evidence strength within an engine*, **not** probability of profitable trades or actual rupees invested. Never add 100+100+100+100+100 and label it win probability.
- No fabricated premium, OI, futures flow, news impact, or money amount. Missing/unverified/stale source => N/A / WAIT, not 0 or bearish.
- One normalized, cached analysis snapshot powers Dashboard (three fixed indices), Scanner (detail), Watchlist (compact equity-only rows), and Super Five (one compact card with drill-down), keyed by symbol, exchange, contract/expiry, timeframe and source timestamp.
- OPTIONS: ATM plus three **listed strikes below** and three **listed strikes above**, not candle bars; show CE/PE OI, change in OI, volume, LTP premium, premium change, lot size and turnover estimate only where the verified feed supplies inputs. Display units and formula, never conflate OI with cash flow.
- FUTURES (Batch 7 only): only mapped listed contracts; show price change, OI change, volume, turnover estimate and *inferred* long build-up/short build-up/covering/unwinding with limitations. In Batches 4–6 this engine stays N/A / WAIT and never casts a vote. Do not claim actual long/short capital without trade-level directional evidence.
- NEWS: headline sentiment is context, not proven price impact; match instrument and publication times, deduplicate and identify publisher/source, language and negation; show coverage and confidence separately.
- CANDLE: retain validated timestamp/quality gates, timeframe-specific indicators and independent technical score.
- COMBINED: policy-gated directional agreement, explicit conflicts and minimum coverage; unverified engines cannot vote. Preserve existing last-good snapshot only as historical context, never as current signal. No live orders.

## Source audit: existing versus gaps
| Area | Verified in repository | Gap |
| --- | --- | --- |
| Technical scanner | `src/scanner_engine.py`: DEFAULT_FILTERS and OPTION_FILTERS, candle integrity and directional vote score | Separate technical and price-action engines without counting the same correlated candle votes twice; standardized confidence and UI contract |
| News | `src/main.py`: RSS via Google News/BBC, 600s cache, keyword headline_signal and per-symbol fusion | Reliable 0–100 news engine, dedup, sentiment context, freshness/coverage |
| Fusion | `src/main.py`: combine_analysis currently requires candle/options/news agreement and returns WAIT on missing/conflicting inputs | Five-engine schema and explicit policy; current 3-way fusion is neither a complete Futures engine nor an independent Technical + Candle pair |
| Options | `src/server_feed.py`: Dhan NIFTY expiry and unverified PCR/max-pain metrics; `src/main.py` option_snapshots placeholder and CE/PE missing state | Verified full strike rows, ATM ±3, expiry/lot mapping, premium and turnover |
| Futures | No verified Futures money-flow engine found in reviewed main/scanner_engine/server_feed modules | Instrument mapping, futures OI/price/volume data, classification and confidence |
| Surfaces | Scanner fusion_card, Watchlist and Super Five exist | Shared five-engine snapshot, compact and expanded UI consistency |
| Risk | Existing unavailable option votes and WAIT safeguards; live orders disabled | New score-specific regression and end-to-end device tests |

## Implementation sequence and acceptance gates
1. **B4.1 Inventory and UI:** compact BOT KING header, version in Settings, fixed Dashboard indices, Settings-only System Health + Error Doctor, compact Watchlist rows. Source implemented; latest offline suite #1145 PASS. Remaining bottom-only five-tab navigation and five-engine details are pending. Inventory: enumerate screen functions, data paths, symbols, contract support, and currently missing endpoints. Mark implemented / placeholder / unavailable / verified on phone. Count only after complete repo inventory.
2. **B4.2 Schema:** introduce pure normalized five-engine model, confidence, timestamps, reasons and WAIT policy; add offline tests. No network calls in scoring.
3. **B4.3 Technical/Candle separation and News:** improve symbol-specific headline matching, duplicates, negation, publisher and 0–100 evidence strength with explicit uncertainty.
4. **B4.4 Futures:** DEFERRED to Batch 7. Keep the Futures slot fail-closed as N/A / WAIT; do not integrate live futures quotes or require futures entitlement for Batch 4 acceptance.
5. **B4.5 Options:** validated expiry and ATM ±3 listed strikes with CE/PE fields, lot size, price/OI changes and unit-aware turnover estimates.
6. **B4.6 Integration:** one shared cached symbol snapshot for Scanner, Watchlist and Super Five; no per-row API fanout or stale-as-live rendering.
7. **B4.7 Gates:** offline regression, Oracle read-only tests, Android APK/version/signing audit, then phone validation for NIFTY and supported equities, missing data, 429 and resume.

## Navigation and information density
- One bottom-only five-tab bar in this order: Dashboard, Watchlist, Scanner, Super Five, Settings. Remove duplicate top navigation and legacy six-tab layout only with updated navigation/runtime tests.
- Header: compact BOT KING title and bell, no redundant version/paper/live caption. Version appears in Settings.
- Dashboard: NIFTY, BANKNIFTY, SENSEX fixed cards. Watchlist: equities only, compact LTP/change/technical votes, drill-down for details. No fabricated N/C/F/O percentages.
- System Health and Error Doctor share a Settings section; preserve read-only paper-only safeguards.
- Percentage bars are evidence strengths, not calibrated win probability; N/A for unavailable engines, no automatic orders.

## Explicit boundaries
- Existing Dhan option-chain PCR/max pain result has freshness `unverified`, `signal_eligible=false`. Do not promote it into a trading vote.
- Present Dhan client only accepts NIFTY for `option_chain_metrics`; do not claim RELIANCE or other option contracts are mapped.
- The phrase 'three above/three below' is interpreted as **strike levels**. Confirm with user before changing to candle-bar windows.
- Batch 1–3 release build 2.3.106 is separate; do not merge Batch 4 into it without completing its acceptance gates.
