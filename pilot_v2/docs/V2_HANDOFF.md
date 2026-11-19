
## APP-OWNED HTTPS QUOTE REFRESH BRIDGE — 2026-11-19
- Owner requested continuous migration progress and no repetitive stopping. Latest exact source `cabda45234a8b0b5a9e82085fa764bfd08a0ef50` CI #108 PASS, 301/301 offline tests, following earlier #106 FAIL resolved in #107. No V1/default branch/Oracle production/APK writes.
- Prepared `android_app/src/app_readonly_refresh.py`: one bounded app-side coordinator accepts a previously authorized `RefreshIntent`, exact current 0-70 distinct selected equities and an instantiated `V2ReadonlyHTTPSReader` (verified-origin HTTPS/bearer client). Runs independent three-index and selected-equity-only protected read-only quote lanes; skips equity fetch for zero selected equities; honors stale selection rejection, offline/not-permitted intent, separate lane failures, sanitized error outcomes and previous-good quote retention.
- The Android Flet `main.py` deliberately **does not invoke** this adapter: secure device login/session/token approval is NOT yet wired. This is prepared app-contract integration, verified only with injected in-process HTTPS mock, not a production Oracle connection, no Dhan token/device bearer saved in app storage. Five filters, Options and Super Five remain source-gated HIST/WAIT, no live orders.
- One consolidated `test_app_readonly_refresh.py` validates 0/5/70 demand, separate index lane, no unselected data, no access without typed authenticated reader/context, local cache retention after equity network error, no main.py real-connection claim. New CI result pending exact SHA.

---


## JOINT APP-SIDE DATA READINESS — 2026-11-19
- Owner directive: continue code work to next segment instead of reporting and stopping; one coherent batch, one combined CI. Preflight last 10 relevant commits, latest [CI #107](https://github.com/vaishnavi596/volume-king/actions/runs/44436548126) PASS (298/298) at `4ff96a7fac4ab3dd8f362772af5e5b722c41fa41`. #106 source syntax failure was corrected and passed #107.
- New `android_app/src/app_data_readiness.py` is the single local read-only readiness snapshot for existing selected-only demand (0/5/70, no duplicates), independent three-index lane, five supported 1/3/5/15/30m Scanner intervals, validated quote/candle cache, five evidence-gated filters with blank sixth, selected expiry/option metrics/CE-PE strikes and Super Five WAIT. Does not schedule HTTP work, infer freshness, generate fake ranks, enable live orders or claim verified Oracle login. It explicitly reports zero network calls, source HIST/WAIT, and gateway disconnected.
- Wired the **same** readiness model into Dashboard and Settings with visible truthful labels, not multiple data engines or separate provider fetches. Removed stale scanner selection from app-visible readiness via the existing selected-roster reconciliation. New `test_joint_app_data_readiness.py` checks all five intervals for 0/5/70 equities, rejects unselected scanner symbols, checks sixth slot empty, and static UI reachability.
- Exact new SHA offline regression **PENDING** until CI completes; this is app-owned contract/presentation migration, NOT a functioning authenticated data connection, five-filter/Option data producer, real source-fresh Super Five ranks, Master+3 end-to-end, Android WebView/device acceptance or V2 APK. No V1 or Oracle production changes, no Dhan/Angel/Yahoo, live orders off.

---


## V2 APP MIGRATION — JOINT OPERATIONAL PARITY CANDIDATE, 2026-11-19
- Read latest V2 General/Handoff and prior 10 commits/CI before editing. Exact baseline source `576fb377f2631bd6ef7509baee3301255f769ac8` passed [CI #105](https://github.com/vaishnavi596/volume-king/actions/runs/44435368801) 294/294 offline tests. Previous failure #103 was fixed by #104.
- This coordinated **V2-only** app-side batch addresses V1 operational gaps: the existing app-owned data-only manual intent preview is now reachable from both Watchlist and Settings using **one callback**, still zero network calls; five saved PAPER risk plans can be used in an **explicit-confirmation, session-only manual PAPER simulation ledger**, with independent slot tracking, manually entered exits and hypothetical P&L. Uses saved strict risk plans only; rejects missing/invalid plans, unauthorized slot, missing consent, duplicate simulated position and invalid exit. No broker orders, auto fills, live quotes, Dhan/Oracle traffic, API keys or external callbacks.
- Added `local_paper_ledger.py` and consolidated `test_operational_app_migration.py` for positive/negative and actual UI wiring; strengthened one-run audit to distinguish paper risk previews and manual simulated ledger and shared refresh callback. This is code and tests in **one combined commit**, not multiple feature migrations.
- **PENDING:** new exact-SHA CI result. A green offline source test would show only local component functionality; rich V1 WebView visual parity, authenticated 5-filter/Option/Super Five, data-only real refresh, Master+3 security, production Oracle/Dhan and separately signed V2 APK remain outside verified acceptance. No V1 branch, Oracle server, APK build or real orders changed.

---


## COMPLETE 1m/3m/5m/15m/30m TIMEFRAME SEGMENT — 2026-11-19
- Owner rule: finish all interconnected work in one segment, one combined commit and one CI, not isolated micro-fixes. Latest executable preflight CI #104 SUCCESS at `f6ad846b632c6470026b3eae4711620cbfe350f6`; reviewed prior 10 relevant commits and prior CI failure #103 resolved at #104.
- All five timeframes are allowed by Scanner app selection/saved preference, candle cache, five-filter evidence cache, candle-trend and option-factor input gates, and shared filter-context view. Scanner dropdown includes 1m/3m/5m/15m/30m; 1m index and 3m Watchlist defaults remain unchanged. Sixth slot stays empty.
- One shared `HistoricalThreeMinuteFallback` wrapper now supports historical view over 1m, 3m, 5m, 15m and 30m. Direct accepted candle history takes precedence; otherwise 3m uses the reviewed historical helper and 5/15/30 use only complete session-aligned 1m buckets with gaps/duplicates/unfinished buckets rejected. No Dhan fanout, simulated live, server writes or fabricated candles. Watchlist, Scanner and Super Five historical shortlist use this same adapter (Watchlist 3m).
- Combined regression `test_complete_timeframe_segment.py` checks choice/persistence, all five completed history sizes, selected roster, missing/forming bars, preferred direct data, filter sixth blank and shared cross-screen wiring. Prior invalid saved 15m test updated to unsupported 45m. Migration gate options UI false-negative corrected to inspect the actual visible strike view.
- This commit is **APP-SIDE LOCAL HISTORICAL TIMEFRAME SEGMENT**, not Dhan/Oracle live integration, finished V1 WebView parity, authenticated Master login, real option chain or signed V2 APK. New exact CI result must be verified; no V1/default branch/Oracle production/APK/orders changes.

---


## SINGLE-RUN V2 DELTA MIGRATION GATE — 2026-11-19
- Owner condensed repeated V2 migrations to **one GitHub CI action per combined candidate**: static read-only V1/V2 delta report + existing full offline regression in the same pilot CI job. No additional workflow dispatch is needed for reporting.
- Replaced prior `one_click_migration_gate.py` hardcoded `False` acceptance rows with source-observed UI wiring and separately named PENDING external acceptance (no fake completion). Active `five_engine.py` is correctly treated as staged/quarantined, not falsely reported missing from active app source. AST checks reject known legacy imports and direct provider calls in active V2 Python. `--strict` remains fail-closed until real external gates are independently verified.
- Updated `.github/workflows/v2-pilot-contract.yml` to compile/test once, emit one gap report, and upload same-run report artifact. Separate manual strict workflow remains optional, not required for normal iterations.
- Added `test_one_run_migration_gate.py` covering factual report, report-only vs strict distinction and banned provider import. CI on this new SHA remains PENDING until checked; prior executable [CI #102](https://github.com/vaishnavi596/volume-king/actions/runs/44432398138) SUCCESS.
- This DOES NOT automatically copy V1, integrate Dhan/Oracle, build APK, enable orders, modify V1 or certify device/live acceptance. One-run is one orchestration, not a guarantee that unfinished development is complete. Server production only after separate owner approval.

---

## CURRENT EXECUTION ORDER — TWO ACTIONS ONLY (2026-11-19)

Owner wants the shortest safe path to a completed BOT KING V2 app; no repeated micro-patches or repetitive planning commits.

**ACTION A — SCAN + IMPLEMENT IN ONE LOCAL CANDIDATE:** Run V1 read-only vs V2 full dependency/feature delta once. Reuse already proven V2 code. Within the same bounded candidate, complete every safely app-owned missing screen, navigation, chart, Smart Data policy, Watchlist, Scanner, Super Five, options/filter evidence consumer, settings, Paper offline components and Master local controls, excluding non-verifiable live behavior. Quarantine legacy Angel One/Yahoo/order/credential/server-owned app paths, preserve 70 unique equity selection and 3 independent indices, five filters + blank sixth, and last-good history. Do not publish micro-commits mid-work; use a single joint code change + test change after local checks.

**ACTION B — ONE TEST GATE + CLOSE / CORRECT ONLY FAILURES:** Offline compile, security and full tests run together once per candidate; check exact source SHA CI outcome. Correct only failed checks in same candidate, without rerunning unrelated successful work until source changes. Certify APP-SIDE MIGRATION READY only when all app-side gates pass, NOT live provider/device verified. Production Oracle integration and separately signed APK/device acceptance follow later and require separate authorization. No APK build/server change under current owner guard.

**Integrity:** Collapsing user-visible steps does not remove validation. The manual workflow's hardcoded FALSE acceptance checklist is not a genuine automatic migration implementation; it must be changed to evidence-backed checks before claiming one-click completion. Do not promise timing or call the current V2 fully migrated. Existing latest verified executable source `46e79bfaddcb89cc7794bcb503c39cdf1a978692`, CI #102 SUCCESS; previous docs-only `145b8c0f099508124a18bb0f82bbaff059bd7903`.


---

## CURRENT OWNER DECISION — COMPACT FINAL MIGRATION, 2026-11-19

**Stop incremental micro-fixes.** Use a frozen one-time V1→V2 gap manifest and one coordinated V2-only app migration candidate; do not treat each feature as a separate migration. The purpose is to minimize commits, retests, clicks and CI cost without weakening security.

**Exactly three operational gates (not 18 separate migrations):**
1. **FREEZE / SCAN ONCE:** use V1 read-only and current V2 source; assign each previously inventoried feature one row with source/dependency, V2 entrypoint reachability, data state, missing behavior, risk, and proof. Close scope before modifying code. Group UI+navigation+Settings+Watchlist+Scanner+Super Five+Paper; candle+options+five filters+Smart Data; security+Master+3/auth and provider quarantine. Explicitly reconcile 3-vs-5 watchlists without destroying stored state. Keep Android device/real provider gates separate.
2. **ONE V2 APP CANDIDATE:** implement the entire safe app-owned dependency graph in a dedicated V2-only candidate; preserve existing good implementations, block Angel One/Yahoo/legacy server settings/credentials/live orders, and keep Dhan-only authenticated transport unavailable as WAIT until independently verified. No V1/default-branch/Oracle production/APK changes. Combined fixes and tests in ONE coherent code commit when source is ready. If a regression fails, repair only failures in the same candidate; no ad hoc new migration rounds.
3. **ONE COMBINED ACCEPTANCE:** run static security/compile, all functional cross-screen+0/5/70 roster+index/1m/3m/5m+five-filter/blank-sixth+cache+session/rollback tests together. Require exact SHA CI PASS and source-to-UI reachability; do not call Android device/provider LIVE accepted from offline CI. Gate reports distinguish APP CODE READY, DEVICE PENDING, and ORACLE PENDING. No automatic production merge/cutover or false final COMPLETE.

**Known audited open domains (not independent tasks):** V1 full visual/WebView/device parity; live Super Five/five evidence engines; options CE/PE/OI/PCR/max pain; verified News/Futures/AI; real data-only Smart Data refresh, adaptive shared budget; Master +3 integrated enforcement; safe Paper ledger/alerts; secure Dhan/Oracle transport; signed APK/device acceptance. The existing one-click audit tool has eight hardcoded False acceptance checks and is a fail-closed diagnostic, NOT actual automatic migration; replace with evidence-driven checks as part of coordinated candidate. Do not promise one-click completion before verified automation exists.

**Last known executable verification at decision:** commit `46e79bfaddcb89cc7794bcb503c39cdf1a978692`, [V2 CI #102](https://github.com/vaishnavi596/volume-king/actions/runs/44432398138) completed SUCCESS; previous #101 and #100 also SUCCESS. This handoff revision is documentation only, not new CI evidence.

**NEXT EXACT ACTION:** Produce/freeze one machine-checkable full gap manifest across all V2 modules and V1 read-only callable UI graph, prioritizing missing entrypoint connections and high-risk provider boundary. Then build the one coordinated candidate. No more isolated functionality patches prior to frozen audit.


---

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


## 2026-11-19 — Consolidated V1→V2 migration audit and safe historical batch
- Owner instruction: stop indefinite feature-at-a-time migration. Review the complete V1 callable graph in one audit; migrate only reviewed dependencies into V2 and run one combined regression per coherent batch.
- Preflight: branch pilot/botking-v2-smart-gateway-20261118 HEAD d013929d5112dd6078bf4bc758f41fb4002d0b59 (docs-only); executable eec4869aab3c734162199aabf83f6b10b1366061 passed CI #96, 274/274. Last ten recent source/docs commits reviewed via GitHub branch history; historic failures remain preserved.
- This atomic app-only batch activates three existing exact reviewed V1 pure helpers (analysis_quality, candle_retention, dhan_three_minute) in V2 Android source, adds offline history bridge and combined positive/negative regression; no event loop, new Dhan calls, automatic signals or provider fallback.
- FINAL PARITY AUDIT — OPEN, NOT FALSELY CERTIFIED: (a) V1 full screen/layout/WebView and Android control parity; (b) local Scanner/Super Five verified live five-filter ranking and evidence; (c) Options CE/PE/OI/PCR/max pain, News/Futures and AI measured signal inputs; (d) app data-only refresh scheduler with 0–70 shared demand and independent three index lane; (e) Paper nonexecuting ledger/alerts; (f) Master+3 delegated integrated auth; (g) Android real-device acceptance and independent V2 signed APK; (h) owner-approved Oracle/Dhan production integration after app acceptance. These are distinct from successfully migrated offline helpers.
- Quarantine remains V1 src/main.py, market_feed/server_feed/credential/order paths; no Angel One, Yahoo, server-owned settings, trading action or production edit. Do not call this complete migration until executable reachability + end-to-end gates pass.
- Source commit CI outcome is PENDING; only claim PASS after exact SHA test result. The user's no APK/no server requirement is unchanged.

## One-click safe migration gate, 2026-11-19
- Branch before implementation: afbb09d9ac216f31a1ee52d7ae07261e675f1aac. Exact V2 Pilot CI #97 run 44428135737: completed SUCCESS. Prior #96 completed SUCCESS 274/274; #91 historic FAIL resolved in #92. Ten newest commits inspected before modification.
- Added manual workflow `.github/workflows/v2-one-click-safe-migration.yml` and fail-closed read-only audit `pilot_v2/tools/one_click_migration_gate.py`.
- One Run workflow triggers one combined V2 compile+offline regression, then active-module AST/provider inspection and an artifact report. The job fails if required complete-migration/Android/provider acceptance remains open. It NEVER blindly copies legacy src/main.py or auto-merges unknown code. Runs do not use Dhan, Oracle, token, server, APK, broker or orders.
- Important: the one-click button is a **gate and diagnostic**, NOT a promise to migrate full V1 feature logic automatically or evidence that full migration has been completed. Source migration, Android acceptance and authenticated integration remain explicit open gates.
- No V1 or old journal writes. No production modifications. First dispatch result pending; do not label tested yet.

## V2-FT3-APP-MANUAL-REFRESH-INTENT-UI-20261119
- Last source `afbb09d9`: [CI #97](https://github.com/vaishnavi596/volume-king/actions/runs/44428135737) SUCCESS. One-click gate code `b685d628` [CI #98](https://github.com/vaishnavi596/volume-king/actions/runs/44429121009) SUCCESS. The separate manual workflow has NOT been dispatched; this run is the existing pilot test workflow.
- Implemented V2 Settings local manual refresh PLAN button using the already tested `make_refresh_intent`: exact 0/5/51/70 selected demand and independent index lane; no provider, token, background polling, network call or UI claim of refreshed prices. Inactive gateway is clearly visible. On changing selected equities, preview recalculates from current selection.
- Added AST and positive/negative offline regression `test_ft3_manual_refresh_plan_ui.py`. New exact-source CI PENDING. This closes only app-side intent UI reachability, not real data-only refresh scheduling or source-confirmed Dhan updates.
- One-click GitHub Actions workflow on pilot branch may not appear as a manual dispatch in the Actions UI until it also exists on repository default branch; do not claim an operational button without observing its dispatch. Do not change V1/default branch under current V2-only ownership constraint.
- Remain open: live authenticated data, device/master authorization, full V1 UI/Options/Super Five/Paper, real chart and Android acceptance. No APK/Oracle/production modifications.

## V2-FT3-CANDLE-PARTIAL-NEWER-HISTORY-RETENTION-20261119
- Latest exact source CI #99 commit `61ecb5cc409c5a0d9ec9a76a69e193c9527a8561` [run 44429379524](https://github.com/vaishnavi596/volume-king/actions/runs/44429379524), SUCCESS. Source prior #97/#98 also SUCCESS; reviewed newest 10 commits before patch.
- Found additional partial-window hazard: `LocalCandleHistory.accept` previously rejected old-end replay, but could accept a shorter newer-ended validated window and shrink a 35-bar chart/indicator history to two bars. Fixed fail-closed: when existing history is longer, reject shortened incoming history while preserving original revision and current completed bars. A later complete longer window may still update history.
- Added targeted regression to `test_flet_candle_history.py` for 35-bar retained 3m chart, newer 2-bar partial rejected, and corrected 36-bar refresh accepted.
- This is app-side V2-only cache retention; does not assert live candle or broker data, and does not fetch Dhan. Source CI PENDING until observed. No V1/Oracle/APK/credentials/orders changes.

## V2-FT2-SCANNER-3M-CACHED-1M-OFFLINE-FALLBACK-20261119
- Preflight: V2 Pilot CI #100 [run 44430597636](https://github.com/vaishnavi596/volume-king/actions/runs/44430597636) SUCCESS exact source `cf063efbe6712b03e07144d69d475da487766463`. Reviewed previous 10 V2 commits. Earlier #99/#98/#97 successful.
- V2-only scanner view adapter `historical_three_minute_fallback.py`: if trusted local 3m cache is missing, derive display-only completed session-aligned 3m bars from already accepted cached 1m using reviewed V1 pure `dhan_three_minute` helper. Never mutates primary 3m cache, bypasses symbol selection, invokes provider or creates live evidence.
- Scanner summary, technical historical analysis, native candle and line chart consume overlay; five source-gated filter votes, options and Super Five ranking remain on existing evidence gates. Missing/incomplete/unfinished minutes remain WAIT. Added focused offline regression `test_scanner_3m_historical_fallback.py`.
- CI pending for new SHA; no V1 code, default branch, server, APK, Dhan API, trading, secrets or production edits. Complete V1 migration/device/live data acceptance remains open.

## V2-FT2-SHARED-SCANNER-SUPERFIVE-HISTORICAL-3M-20261119
- Exact [CI #101](https://github.com/vaishnavi596/volume-king/actions/runs/44431985861) completed SUCCESS at executable SHA `6acb6d9221b8150824922aaf4d1049f3d2be0c1d`. Last 10 commit lineage reviewed; no pending earlier source CI failure.
- Fixed UI historical view mismatch: Scanner 3m used the offline cached 1m→3m overlay but the Super Five historical shortlist and its on-click validation used raw 3m cache. All three now use the same `scanner_history` read-only overlay, preserving strict selected-equity checks and historical-only labels. Does not mark actual source-based Super Five LIVE or alter five-filter votes.
- Added shared-view regression `test_scanner_superfive_history_parity.py` to validate source callbacks, 35 complete 3m bars derived from 105 completed 1m bars, non-live presentation and hidden removed equity. New CI PENDING until observed.
- No V1/Oracle/Dhan/API/APK/trading writes. App-side full V1 parity still incomplete; do not mark final migration done.
