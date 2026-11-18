# BOT KING V2 — HANDOFF (CURRENT)
**Checkpoint 2026-11-18.** Detailed current category status, CI, blocked work and rules: [CURRENT CANONICAL STATUS](V2_CURRENT_CANONICAL_STATUS_20261118.md). Standing owner rules: [GENERAL FRAMEWORK](V2_GENERAL_FRAMEWORK_RULES.md). Historical batches: [MASTER JOURNAL](V2_MASTER_JOURNAL.md) and [WORK LOG](V2_WORK_LOG.md).

## Resume in 30 seconds
- Repo `vaishnavi596/volume-king`, branch `pilot/botking-v2-smart-gateway-20261118`, V2-only directory `pilot_v2/`. **Old V1 is read-only.**
- Last verified actual V2 executable source: `8739cb9ab4d342f96c58027a5c2ee6fd32b12c30`, [CI #86](https://github.com/vaishnavi596/volume-king/actions/runs/44366294149) **249/249 PASS**. Previous #86 was 246/246 PASS. Pre-journal consolidation HEAD `1cf6e0e15de12a5604ed10e80afb9586d9989c1a` docs-only. Do not treat this docs consolidation as newer tested executable code.
- Historical failures #73–#77 (same missing `OptionEvidenceError` import) fixed in #78 (237/237 PASS). Historical #83 1 old Watchlist text-assertion failure fixed in #84 (244/244 PASS). Then #85 (245/245) and #86 (246/246) PASS. **Failures are not deleted.**
- Ported now: V1 dark-gold partial Dashboard/Watchlist style, header/version/bell, local Help/Error Doctor; Watchlist 5 groups/70 unique, local search and row→Scanner 3m; historic Scanner/chart, native OHLC, guarded CE/PE selected-expiry ATM±3 cache; Super Five historical shortlist with chart jump, verified LIVE ranking WAIT; five evidence-gated filters + blank sixth. All **offline contracts**, not full V1 screen/function parity.
- **Not done:** all remaining V1 UI/engine/control parity, fully sourced options/PCR/max pain/news/futures/AI, real app+Master auth/login, actual Dhan read-only Oracle transport, smart data refresh, device visual testing, signed V2 APK or Oracle deployment.
- **NEXT actual work:** compare *read-only* V1 Dashboard/Scanner/Options/Settings handlers against V2, group missing actual UI callbacks + dependencies; implement safe app-owned V2-only batch with tests; then check exact new CI and update all four journals. Never copy old server settings/provider fallback, Yahoo/Angel or order execution.
- **Boundaries:** App first, Oracle LAST; preserve live V1/production; 1 Master+up to 3 delegates target (older code max-3 including Master still unresolved); 09:10–15:45 IST, 3m Watchlist, 1m index, 1m default Scanner, dynamically 0–70 equities+3 indices, HIST/WAIT unless authenticated evidence; no live orders. No APK yet.
- **Workflow:** `ok` means continue, do not stop. Review latest actual code SHA, CI and failures before patch. Atomic related source+test+journals commit. Docs-only does not trigger code CI. Do not ask user to restate known context.

**Snapshot link:** [V2_CURRENT_CANONICAL_STATUS_20261118.md](V2_CURRENT_CANONICAL_STATUS_20261118.md). This short handoff is CURRENT, not a chronological event log.


## V2-FT2-SCANNER-CHART-WINDOW-CI87-VERIFIED-20261118
- Exact [V2 Pilot CI #87](https://github.com/vaishnavi596/volume-king/actions/runs/44368036631), run `44368036631`, source SHA `51da2bef55e6b59d5ab47dffba7d513ed32a6e96`: **SUCCESS 249/249 Python offline tests OK**, no failing step.
- App source: `pilot_v2/android_app/src/main.py`, new `chart_window.py`; test `pilot_v2/tests/test_chart_window.py`. Scanner chart display selects 15/35/70 cached completed historical bars, 35 default; changing dropdown uses local window only, never refreshes quote/candle data, does not change timeframe or produce a LIVE claim.
- Safeguards: strict window choice type/range; completed history, invalid new data retains last-good; five filter+blank sixth, symbol/timeframe, 70 equities and 3 indices unchanged.
- Limit: source CI not Android Flet rendering or authenticated Dhan/Oracle provider integration. No V1, Oracle, Dhan API, orders, APK.
- NEXT: V1→V2 functional parity inventory and grouped local app control wiring, then exact code SHA CI; Oracle production last.

## LATEST CHECKPOINT — CI #88 & V2 Index Chart Navigation
- Verified latest executable source CI **#88 253/253 PASS** at `c8d06b6af35bf8e5d8f335c7455b50c2a55f0b26`, run [44370132223](https://github.com/vaishnavi596/volume-king/actions/runs/44370132223). Shared five-factor WAIT/HIST coverage now connected across Dashboard, Watchlist, Scanner and historical Super Five; no artificial LIVE or sixth filter.
- Next code batch adds local `1m Chart` buttons to NIFTY/BANKNIFTY/SENSEX Dashboard cards, selecting the validated index in existing Scanner. Source `android_app/src/main.py`; tests `tests/test_index_chart_routing.py`. **New exact CI PENDING** until verified.
- Still NOT final complete V1 copy or live operation: remaining V1 UI controls, options/scoring, smart data, Master+3 delegated auth, alerts/Paper safe functions, signed V2 APK and Dhan/Oracle integration must pass separate gates. Old server/Angel/Yahoo/credentials/orders excluded.


## V2 three Dashboard analysis slots — next source CI pending
- Previous exact CI #88 **253/253 PASS** for shared five-factor context; subsequent exact CI #89 **255/255 PASS** for independent Dashboard Index 1m Chart buttons at `ea4233d8c0d2c27a015fb0ba76515bbba45e0ac9`, run 44370643743.
- Read-only V1 `dashboard_index_analysis()` had 3 selectable analysis panels. V2 app now adds **three V2-local independent slots** for selected Watchlist equity or three indexes; V2 device-only persistence, 1m quote/candle/filter context, 1m Scanner navigation, removed-symbol fallback. New `local_analysis_slots.py` with negative/positive tests. Exact new Actions CI still PENDING, not device verified or provider connected.
- Remaining: full V1 layout, alerts, paper-safe UI, full options/News/Futures/AI, Dhan-only authenticated read-only data refresh, master+3 delegated login, package/Android acceptance and Oracle LAST. Details in `V2_REMAINING_FUNCTIONAL_GATES_20261118.md`. No legacy server settings, V1 code, Angel/Yahoo, OAuth, live order or APK changes.
