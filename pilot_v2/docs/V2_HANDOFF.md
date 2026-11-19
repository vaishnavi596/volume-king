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

## VERIFIED CI #90 — Current V2 checkpoint
- Exact code SHA `1bbf63cd45e0ef64c9021ffdf2b41ec948f3af81`; [V2 CI #90](https://github.com/vaishnavi596/volume-king/actions/runs/44371437426) **259/259 SUCCESS**. Previous #89 255/255 and #88 253/253 PASS.
- V2 has three separately selected, V2-device-persisted V1-style Dashboard analysis slots for NIFTY/BANKNIFTY/SENSEX or selected Watchlist equities, shared source-gated 1m quote/candle/factor context, and direct 1m Scanner chart navigation. Invalid/removed choices fail closed. This is **offline-only**.
- Remain NOT COMPLETE: V1 exact styling/click paths, full Options/News/Futures/AI five-source engine and real Super Five, Smart Data refresh/last-good live provider, Master + 3 delegated device secure login, paper-only/alerts UI, full Android APK and actual phone verification; Oracle/Dhan production deployment LAST after approval. See canonical snapshot and remaining functional gates. No V1/server-provider/Angel/Yahoo/credentials/orders changes.


## V2 local-only Settings Backup/Restore — new CI pending
- Last exact source CI #90 run `44371437426`, SHA `1bbf63cd45e0ef64c9021ffdf2b41ec948f3af81`, **259/259 PASS** for V1 three Dashboard analysis slots and prior cross-screen filter/index coordination.
- New feature source `local_settings_backup.py`, V2 `main.py` Settings backup export + confirmation-gated restore, and `test_local_settings_backup.py`. Export contains ONLY Watchlists, Scanner, Smart Data and three Analysis Slots. Strict schema validation rejects old V1 server settings, credentials, provider names, secret fields and wrong/removal/duplicate data. Restore remains local to the app and preserves source-gated filter caches. **New exact CI PENDING**, no real phone acceptance yet.
- The still-missing full V1 callable UI and server-last Dhan data/integration gates remain open. No V1, Oracle, Dhan, live orders or signed APK touched.

## CI #91 local backup assertion failure → corrective CI pending
- Run [#91](https://github.com/vaishnavi596/volume-king/actions/runs/44372461992) at source SHA `74ea3c107118da66fdccd480796db935353dedcd`: **262/263 tests passed, one source-string assertion FAIL**, because backup export call is wrapped across lines. The actual strict local preference roundtrip/security tests passed.
- Only test `test_local_settings_backup.py` source assertion corrected to accept real multiline Flet code. No app logic/auth/provider/credentials changed. **New exact CI PENDING**, do not claim PASS until verified. Historical #91 stays FAIL.


## CURRENT V2 source checkpoint: CI #92, 263/263 PASS
- [GitHub Actions #92](https://github.com/vaishnavi596/volume-king/actions/runs/44372838093) exact executable source SHA `2e35e6a4b6182acdab589360e28981e05aa856ae`, **SUCCESS 263/263 Python offline tests**. CI #91 is historical FAIL 262/263 because of a wrapped call assertion and was corrected in #92; no app logic changes in correction.
- Safe local-only Settings Backup/Restore, selected Watchlists, Scanner, Smart Data and 3 Dashboard Analysis slots passed source/functional regression. Earlier #88 cross-screen five-filter coverage, #89 index→1m Scanner and #90 three independent analysis slots remain green. V2-only, no old server settings, broker secrets, Angel/Yahoo, V1 branch/code, Dhan calls, trades, Oracle deployment or APK.
- **NOT FINISHED:** actual V1 feature-complete Android UI, Alerts, safe Paper operations, authenticated Dhan refreshed data, genuine five-factor News/Futures/Options/Candle scoring/real Super Five, complete CE/PE/OI/PCR/Max Pain, Master+3 delegated login, smart refresh and phone/build checks. Do not mark FULL V1→V2 migration complete or LIVE from offline CI.
- NEXT: inspect last executable source SHA #92, then address remaining local UI/functional parity and missing trusted data contracts in V2-only batches, exact new CI, later Android, Oracle LAST.


## V2 PAPER preview-only clean migration — exact CI pending
- Prior source CI #92 `2e35e6a4b6182acdab589360e28981e05aa856ae`, run `44372838093`, 263/263 PASS. Examined V1 `paper_engine.py` read-only: deterministic math/datetime, no networking, provider or order calls. Copied exact pure blob to V2; added `paper_preview.py`, manual risk/stop/target UI to Settings, and `test_paper_preview.py`. **NO BUY/SELL/EXIT order controls or unattended bot enabled**, manual hypothetical calculations only.
- New exact-code CI PENDING; full V1 5-slot Paper Bot/alerts still NOT ported. No V1/old server settings/Angel/Yahoo/Oracle/Dhan OAuth/live order/APK changes. Remaining gates in V2 tracker.


## Verified current CI #93 — 267/267 PASS / migration not yet complete
- [GitHub V2 #93](https://github.com/vaishnavi596/volume-king/actions/runs/44373958095) exact code `29fd2645d3cc5783175fdf5bac33d81a51e24131`, **267/267 offline PASS**. V1 pure deterministic paper engine copied unchanged; Settings now has non-executing manual Paper risk/stop/target preview, with source-security and negative tests. No broker or live orders.
- CI #92 was 263/263 PASS for local preference backup/restore; earlier #91 historical FAIL fixed. Cross-screen five-filter, Index → Scanner, three Dashboard Analysis Slots also green in source regression.
- Still OPEN: V1 actual five-bot paper ledger, alerts/notifications, exact V1 UI/rich chart, complete verified Dhan five-filter/News/Futures/Options/Super Five, smart refresh, Master+3 delegates, Android signed V2 device tests, Oracle production LAST. This is **not full V1→V2 acceptance**. No V1/old provider settings/Angel/Yahoo, Oracle restart, Dhan calls or APK.


## V2 five PAPER planning slots — new CI PENDING
- Prior CI #93 run 44373958095 at SHA `29fd2645d3cc5783175fdf5bac33d81a51e24131`: **267/267 PASS**. New V2-only `local_paper_slots.py`, `test_local_paper_slots.py`, and real Settings UI add five independent local **manual risk preview** slots; no broker orders, positions/fills or automatic paper trading. Exact new code SHA CI PENDING.
- Read-only V1 `src/paper_bot_slots.py` contains legacy settings migration and event ledger; intentionally **not** imported/copied wholesale. Still missing real V1 five-bot safe journal/alerts/UI parity, verified Dhan data/filters, Master+3 device login, complete Android app testing and Oracle last. No V1, Angel/Yahoo, credentials, Dhan/Oracle server, orders or APK changed.


## VERIFIED V2 CI #94 — 270/270 PASS; five local paper-risk slots
- Exact source SHA `27039f8dfb496f8355ef56f17f9a53efb84bfc8a`, [run #94](https://github.com/vaishnavi596/volume-king/actions/runs/44423433609), job SUCCESS **270/270 offline Python unit tests OK**. New app-only `local_paper_slots.py`, Settings dropdown for Bot 1..5, local manual risk preview save/clear, no trade or order, plus strict source/functional regression.
- Previous code #93 267/267 PASS. These are **planning records**, not V1 5 paper bot execution, ledger, or alerts. Full V1 visual/function parity, verified Dhan/Options/News/Futures 5-filter signals, Smart Data, Master+3 delegates, Android phone acceptance and Oracle LAST remain open. V1/old settings/Angel/Yahoo/server/credentials and APK untouched.


## V2 five Paper slot stale-input safety fix — CI pending
- Last verified CI #94 run 44423433609 exact SHA 27039f8dfb496f8355ef56f17f9a53efb84bfc8a **270/270 PASS**. Subsequent V2 source patch invalidates previously calculated manual paper risk preview whenever manual side/numeric input changes; prevents storing a stale calculation in any of five planning slots. New regression added in `test_local_paper_slots.py`; exact current CI PENDING.
- No broker network, V1 server settings, Angel/Yahoo, OAuth, orders or APK changes. Other full V1/Android/live-data gates remain open.


## VERIFIED CI #95 — PAPER PREVIEW STALE-INPUT GUARD — 2026-11-19
- [BOT KING V2 Pilot CI #95](https://github.com/vaishnavi596/volume-king/actions/runs/44424322447), exact source `b3679df967b84591d7cca06c9bfaed5031af8cf4`, **COMPLETED SUCCESS 271/271 Python offline tests OK**, pilot-contract job SUCCESS (2.229s). Previous #94 at `27039f8dfb496f8355ef56f17f9a53efb84bfc8a` was 270/270 PASS.
- V2 Settings side and any manual numeric paper planning input now invalidate `paper_last_preview` so an old calculation cannot be saved as a fresh five-slot planning record. `test_local_paper_slots.py` explicitly tests both callbacks and the save gate. No broker, server, provider or automatic-trading actions added.
- The current V2 local PAPER feature is five independent manual **risk preview** records, NOT V1 full five-slot Paper Bot trading/ledger execution or alerts. Remaining gates: full V1 UI/interactive charts, nonexecuting paper ledger/alerts, authenticated Dhan-only five filters/Options/News/Futures/AI and Super Five, adaptive refresh, Master+3 delegates, V2 Android build/device acceptance and Oracle production LAST with separate approval.
- Scope: only `pilot_v2/`. V1 code, old server settings, Angel One/Yahoo, credentials, Dhan API, Oracle, orders and APK unchanged. Docs-only follow-up is NOT a new executable CI.


## V2-FT2-LOCAL-ALLOWLIST-NOTICES-20261119
- **Prior exact CI:** #95 run `44424322447`, source `b3679df967b84591d7cca06c9bfaed5031af8cf4` **271/271 PASS**. Last docs-only HEAD `b7dd72b53170859579eaa04eb87f52fecd808ee0` reviewed; V1 `src/main.py` read-only audit confirms V1 alerts panel explicitly **NOT CONNECTED**, notification bell is static and push/delivery is absent.
- **ACTUAL V2 BATCH:** `android_app/src/local_notices.py` keeps at most 20 **session-only** human-readable notices for five allowlisted local app events (Watchlist add/remove, manual PAPER risk-plan save/clear, local preferences restore). `main.py` records these events, Settings shows unread count/list and Mark Read/Clear controls. No raw details/symbol/secret payload stored, no external alert subscription, no live market signal or remote push. No full V1 alerts migration claim.
- **TEST:** `tests/test_local_notices.py` covers five accepted events, unsafe arbitrary event denial, 20-record cap, mark read/clear, AST source/UI event hooks and no provider/broker imports. New exact source CI PENDING until inspected.
- **HARD BOUNDARIES:** V2-only, no V1 changes, Angel One/Yahoo/server setting imports, Oracle, Dhan requests/auth, orders, APK. Genuine price alerts, push notification provider and full Android runtime remain unimplemented. Next exact-SHA CI, if PASS continue safe app-only functional gaps.


## VERIFIED V2 CI #96 — 274/274 PASS — Local Allowlisted Notices
- Exact code commit `eec4869aab3c734162199aabf83f6b10b1366061`, [Pilot CI #96](https://github.com/vaishnavi596/volume-king/actions/runs/44426357518) run `44426357518`, **SUCCESS 274/274 offline Python tests OK** (1.214s), job successful. Previous CI #95 271/271 PASS at `b3679df967b84591d7cca06c9bfaed5031af8cf4`.
- `local_notices.py` session-only event center with five strict no-payload event codes, bounded to 20 notices; `main.py` records Watchlist add/remove, paper plan save/clear, local preference restore, and Settings displays notices/unread/mark-read/clear. No remote messaging, price threshold alert, broker activity, data feed, trading signal, secret or full V1 push/alert parity.
- `test_local_notices.py` checks event allowlist, rejection of arbitrary/secret-bearing codes, bounded history, clear/read and actual V2 Flet handlers. Source-only regression cannot prove actual Android native UI.
- Remaining unfinished: full V1 rich UI/chart and local paper ledger (simulation only), verified source-based five filters/options/News/Futures/Super Five, adaptive Smart Data, Master+3 delegated device auth, Android signed V2 acceptance and Oracle/Dhan live read-only integration LAST. No V1, Angel/Yahoo, old server settings, Oracle production, Dhan requests, tokens, live orders or APK changes.
