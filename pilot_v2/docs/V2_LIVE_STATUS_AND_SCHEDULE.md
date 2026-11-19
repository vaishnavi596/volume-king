
## COMPLETE V2 NATIVE CHART HISTORY WINDOW PERSISTENCE / BACKUP — 2026-11-19
- Owner requests **report + immediately continue**. Latest exact tested source `67c3c53c8c635ba367de98f878a87ce8b289f927` [CI #121](https://github.com/vaishnavi596/volume-king/actions/runs/44442747259) **335/335 PASS**. #120 previously FAILED two UI test assertions after making the header bell clickable; fixed both at #121. Old failed SHA need not rerun. CI #118 330/330 and #119 333/333 were successful.
- Completed next coherent chart preference segment: 15/35/70 historical chart bars now stored in the app's **local** `botking.v2.chart_window.v1` device setting with strict selection and fail-safe malformed-save behavior. Existing Scanner timeframe/candle cache untouched.
- Local preferences backup **schema 3** strictly includes both `chart_style` and `chart_window` on new exports; previous schema 1 and 2 backups still read without modifying unavailable newer preferences; validation of ALL sections before any Settings state replacement; credentials/provider keys and invalid windows rejected. Updated V2 UI backup/restore callbacks, original schema 2 source assertion, and added `test_persisted_chart_window.py` validating 15/35/70 and legacy/no-secret behavior. New exact CI pending; no V1/Oracle production/APK/order changes.
- NOTE V1 native chart control parity is improving, but TradingView WebView, real automatic data-only refresh, verified five-filter market signals, Master+3 device end-to-end and physical Android acceptance remain pending. These are not implied by offline tests.

---


## V2 DASHBOARD BELL → SETTINGS LOCAL NOTICE CENTER — 2026-11-19
- Immediately following completed [CI #119](https://github.com/vaishnavi596/volume-king/actions/runs/44442219567) **333/333 PASS** at `21339fc1b22fefeabb927e508b5845c59a51825d`, inspected V2 header and main. Before this batch the gold bell was a decorative `ft.Icon` and Settings already had bounded session-only notices.
- Finished one safe V1→V2 header callback segment: `v1_header` bell is now a clickable `ft.IconButton` with optional callback, preserving trophy/title/version and three bottom navigation tabs. Clicking navigates directly to existing Settings local-notice center; displays unread local event count with clear `market alerts unavailable` message. No new provider, polling, invented market alert, persistent notification or push integration.
- Corrected Settings local backup caption to mention the already-supported chart style setting. Added offline regression `test_v2_local_notice_bell.py` covering actual header callback and V2 source route/no live orders. CI on new exact SHA PENDING until checked.
- Remaining V1 parity includes richer WebView/visible live chart sync, authenticated Master/Oracle Android connection, actual source-gated five filters and real market-alert policy; no APK, V1, Oracle production or real orders touched.

---


## NEXT V2 LOCAL ACTION ALERTS / NOTICES PARITY — 2026-11-19
- Latest executable `4bd814a0c13005bfad1f1ad512b2d7bb9adabc58` [CI #118](https://github.com/vaishnavi596/volume-king/actions/runs/44441859427) **330/330 PASS**, including read-only cached Scanner EMA20/50, RSI14, ATR14, support/resistance panel. Previous #116 FAIL was repaired with #117 327/327 PASS; no reruns needed.
- Complete next **app-only local-notice** segment: V2 `LocalNoticeCenter` now allowlists `PAPER_SIM_OPENED`, `PAPER_SIM_CLOSED`, `CHART_STYLE_CHANGED`; in Flet main notices are recorded **after** successful manual PAPER entry/exit or strict chart-style choice. Existing bounded 20-session notice list, mark-read and clear operations preserved. No free text, broker order, market signal, price-trigger or external push notifications; market alerts remain PENDING actual authenticated live feed and explicit policy acceptance.
- Added `test_local_action_notices.py` to verify new events, spoofed market alert rejection, limit, button-side action order and absence of legacy calls. New exact CI pending. No V1, server, Oracle production, APK or credentials touched.
- NEXT: finish other missing V1 UI callbacks and one coherent app acceptance audit; do not mistake historical-only controls for V1 live/WebView parity.

---


## V2 CHART TECHNICAL PANEL — FULL NEXT FEATURE SEGMENT (2026-11-19)
- Owner workflow: tell real commit/CI failure & fix, but **continue immediately to next concrete work**. Latest tested V2 executable `74a63cfd43458f7b5591dd0998218f2b1e08db37` [CI #117](https://github.com/vaishnavi596/volume-king/actions/runs/44441434039) **327/327 PASS**. Previous [CI #116](https://github.com/vaishnavi596/volume-king/actions/runs/44441299677) FAILED one 327-test equality assertion: test-reloaded `SmartDataSettings` class identity mismatch despite identical values; corrected the test to compare strict serialized preference values, without changing application validation. Do not rerun #116.
- Next V1→V2 **completed, cache-only technical chart panel** candidate: `historical_indicator_panel.py` reuses existing reviewed `historical_scanner_analysis()` and already accepted cached candles. V2 Scanner shows EMA20/50, RSI14, ATR14 and approximate local historical support/resistance; displays WAIT unless >=30 validated completed bars exist, never presents these as five core OI filters, NEWS/FUTURES factors, LIVE or order signals. All five 1/3/5/15/30m scanner timeframe choices remain independent; zero new network calls or external provider requirements.
- A joint regression `test_historical_indicator_panel.py` checks empty/unselected isolation, 36 completed-bar display, rejected incomplete refresh retaining last-good, real Flet UI wiring, fifth-filter/sixth-blank independence. New executable CI outcome **PENDING** until verified.
- Next: V1-vs-V2 callbacks and safe app-owned alert rules/data-only refresh; full richer TradingView WebView and authenticated Dhan/Oracle remain pending. Do not touch V1/old journals, Oracle production, APK, live orders.

---


## V1→V2 LOCAL CHART PREFERENCE BACKUP/RESTORE PARITY — 2026-11-19
- Owner directive: do not stop after a progress report. Latest source audit [CI #115](https://github.com/vaishnavi596/volume-king/actions/runs/44440845149) `3ce0ced85e0baa504e6dac48aa8942529566806a` **323/323 PASS**; #114 chart style selector `ccb00f5` 321/321 PASS. V1 read-only `src/main.py`, V2 `main.py`, local backup and current V2 journals reviewed.
- Found missing end-to-end local settings parity: Chart Style Candles/Line persisted separately but older V2 Backup/Restore didn't include it. New backward-compatible `local_settings_backup.py` **schema 2** includes strict whitelisted `chart_style`, preserves all existing Watchlist/Scanner/Smart Data/Analysis Slot fields; **schema 1** backups still parse as legacy four-section tuples, without resetting current style. Only schema 2 returns optional fifth validated style. Unknown provider, WebView, credential, token or extra keys fail closed. Does not copy V1 external WebView code.
- V2 Settings source export now includes current chart style; restore validates complete schema before changing any section and persists style alongside existing local preferences. Existing backup source assertion updated, new `test_backup_chart_style_parity.py` covers both versions, invalid keys/schemas and source callbacks. New exact CI pending.
- Live chart, app data auto-refresh, alerts, V1 full screen parity, authenticated Dhan/Oracle, signed APK are still pending acceptance; no V1, Oracle production, APK, server credentials or orders touched.

---


## V1→V2 MACHINE-CHECKABLE UI CONTROLS AUDIT, 2026-11-19
- Exact last tested executable `ccb00f5528ec748c07e6c75d90cf4fb9ba01f46b` [CI #114](https://github.com/vaishnavi596/volume-king/actions/runs/44440548888) **SUCCESS 321/321**. This established V2-only native Candles / Line style dropdown, device-local strict preference and source checks; the original read-only V1 `src/main.py` has richer WebView but V2 does NOT.
- Existing **one** `one_click_migration_gate.py` migration-report now carries a source-derived seven-row **callable V1→V2 control parity** section (native line/candle style, Scanner timeframe, expiry picker, native chart, rich WebView, visible live chart sync and auto-refresh). Rows display `SOURCE WIRED` vs `PENDING` only, not phone/runtime/market-data proof; report remains fail-closed for external acceptance in strict mode. No additional workflow, CI job or market fetch.
- Added `test_v1_v2_control_gap_report.py` confirming exact V1 read-only callback/control indicators and V2 native source controls. Rich WebView/visible live sync/market auto-refresh intentionally remain pending. New exact CI pending.
- NEXT source-gap segment should implement V2 safe app-owned data-only controls and alert policies without copying unsafe V1 server/provider calls, then full coherent app-side parity regression. No V1 edit, Oracle production, APK, credentials or orders.

---


## V1→V2 SCANNER NATIVE CHART-CONTROL PARITY — 2026-11-19
- Owner directive: continue to next actual work, not just summarize. Reviewed V2 General/Handoff, last 10 commits, CI #113 **317/317 PASS** at `bbf765aa116a429eab79885f21030281788397f7`, and read-only V1 `src/main.py` (7,074 lines). V1 has explicit `scanner_chart_style_change`, `scanner_compact_chart`, WebView recovery and scanner chart toggle; V2 had native historical line/candles but no style control.
- This V2-only coherent candidate adds strict app-local Scanner **Candles / Line** style control, native cache-only rendering switch and device-local `botking.v2.chart_style.v1` setting. A corrupt saved style is rejected without overwriting original stored preference. Existing 1/3/5/15/30m timeframe, 15/35/70 chart window and Scanner/Watchlist/Super Five navigation remain separate. No provider, external URL or network code copied from V1.
- New `chart_style.py`, `test_v2_native_chart_style.py` and source-oriented `test_v1_v2_native_chart_parity.py` compare actual V1 control names and V2 native behaviors. **V1 Lightweight TradingView WebView / Android renderer is NOT migrated, NOT tested or declared complete**; separate authorized Android acceptance and full control parity remain mandatory. Offline CI on new SHA pending.
- No server/Oracle production, V1, APK, real orders or access credentials changed. NEXT: finish remaining V1 app control/event parity and automated source-delta coverage in one coherent batch; retain no-build/no-server guard.

---


## VERIFIED SOURCE CI #113 — DEVICE PERMISSIONS + FOUR-FACTOR V1 ASSESSMENT, 2026-11-19
- Exact current source `bbf765aa116a429eab79885f21030281788397f7` [V2 Pilot Contract CI #113](https://github.com/vaishnavi596/volume-king/actions/runs/44439686265) **317/317 PASS** (compile, regression, migration-report artifact). Predecessor `a8ce20b3526c3ad286551077d4b563f05e543610` [CI #112](https://github.com/vaishnavi596/volume-king/actions/runs/44439262854) **313/313 PASS**. No retransmission/re-run of older successful tests.
- CI #112: app evidence cache cannot be updated through the staged integration contract without server-verified session and every required feed permission. Existing Master/delegate revoke/expiry and server-owned feed checks exercised in OFFLINE synthetic integration tests. This does NOT prove actual Android identity/login.
- CI #113: independent four-factor assessment `news, futures, options, candle` source-gated and displayed on Scanner. Five core trading filters remain independent; sixth core filter stays blank. Four assessment rows WAIT when no accepted evidence; no percent accuracy or fabricated news/futures/AI directions. Removing a Watchlist equity or local restore invalidates its retained assessment evidence. This is **app-side parity**, not a live Dhan/Oracle factor producer.
- CURRENT APP-SIDE REMAINING: compare full source read-only V1→V2 visual/layout, all callbacks and cross-screen control parity including rich WebView chart and market alerts; finish secure Android Master enrollment and real delivery transport only against an authorized server contract. Production server modifications and APK remain OWNER-BLOCKED until app-side candidate ready. One coherent feature batch/one CI per segment; only V2 branch writes, V1/old journals read-only, live orders OFF.
- NEXT EXACT WORK: consolidate V1 callable-UI source parity audit as one machine-checkable gap report, then implement remaining safe V2-only screen/callback functionality in a coherent candidate. No further strategy-only commits.

---


## VERIFIED DEVICE SESSION AND V1 FOUR-FACTOR ASSESSMENT MIGRATION — 2026-11-19
- Confirmed exact-source [CI #112](https://github.com/vaishnavi596/volume-king/actions/runs/44439262854) **SUCCESS 313/313** for `a8ce20b3526c3ad286551077d4b563f05e543610`: offline server-owned `DeviceSessionGateway` checks every authorized evidence permission (candles, options, assessment), expiry/revocation before atomic app cache delivery; mock session proofs only. This does NOT establish production Oracle/phone login.
- Next joint **V1 assessment parity** source batch adds V2-local `local_assessment_evidence.py` for four independent `news/futures/options/candle` assessment factors, strict trusted Dhan-source/context/revision checks, unselected equity isolation, no fake AI probabilities. Scanner UI displays four factor rows and `0/4 historical factors` status (WAIT without eligible evidence). Separate five active filters remain unchanged; sixth intentionally empty. On Watchlist removal/restore, assessment cache forgets removed symbols. No broker requests, endpoint, fabricated news or order execution.
- Added `test_local_assessment_parity.py` for 4-factor defaults, partial independent revisions, source/permission/schema rejection, removed equity and actual Scanner source reachability. New exact-source CI is **PENDING**, not a claim of live News/Futures integration or complete V1 parity.
- Owner guard unchanged: V1/old journals read-only; no Oracle server production changes and no APK build. NEXT: full V1 visual/control parity and authenticated app data delivery acceptance; the Dhan/Oracle production phase later only after authorization.

---


## V2 VERIFIED-SESSION / EVIDENCE DELIVERY JOINT CONTRACT — 2026-11-19
- Owner requires uninterrupted next work, one coherent segment and combined CI. Reviewed 10 latest commits, V2 General, Handoff and baseline exact-source [CI #111](https://github.com/vaishnavi596/volume-king/actions/runs/44438674534), 309/309 PASS at `83f8ac184e5bb4b5fc437327baa8758ed142d999`. Documentation HEAD `be4ba30328d64b6363e993073df377e1a1b14765`.
- New **offline** `pilot_v2/session_evidence_contract.py` connects existing server-owned `DeviceSessionGateway` verification to existing V2 app-local atomic `app_evidence_batch.apply_staged_evidence_batch`. For every ordered evidence batch: strict event kind/size; preflight ALL server-issued revocable bearer permissions against the same verified device (candles, options, assessment combinations); only then enter app cache with trusted delivery. Denied, revoked or expired session never updates app cache. Super Five is not a fabricated evidence producer or added feed endpoint.
- New joint `test_session_evidence_contract.py` proves approved Master, delegated permission denial, disable/revoke and expiry/logout, invalid event, unselected symbols and missing assessment privilege. Mock proof verifier exclusively in offline tests; **do not treat bearer or `trusted_transport=True` itself as login proof**. Server/device registry is a prototype and never deployed via this change.
- New exact SHA CI pending. No V1 edits, Dhan/Oracle production modifications, APK build or live orders. Android Flet main remains disconnected until real master-side verifiable login/device enrollment + Oracle authenticated transport/endpoint is implemented and accepted. Next app-only segment: true V1 screen feature/callback parity and final one-shot app contract audit; after that owner-approved server integration and Android testing.

---

## VERIFIED CI #111 — ATOMIC CROSS-FEED V2 APP EVIDENCE, 2026-11-19
- Actual tested source **`83f8ac184e5bb4b5fc437327baa8758ed142d999`**, [BOT KING V2 CI #111](https://github.com/vaishnavi596/volume-king/actions/runs/44438674534) **SUCCESS 309/309 tests**; compile, integrated source/gap check, report artifact PASS. Previous verified executable CI #110 305/305. No previous CI rerun required.
- Staged app-only `app_evidence_batch.py` validates existing retained candle/expiry/options/strikes/factor modules in a copy, commits state to original cache holders only if entire event sequence valid; malformed/unselected/unauthenticated-caller input does not partly mutate cache. Unit tests confirm cross-lane success and rollback. **No real auth login provided; `trusted_transport` must only be set by independently authorized caller; current Flet main remains disconnected.** This passes an *offline local-contract segment only*, NOT live Dhan/Oracle/Android or complete migration.
- **NEXT:** one coherent app-only verified device session and feed contract, linked to existing source transport and cache policy; do not invent endpoints nor permit bearer string to stand as verified identity. Remain under no production server changes/no APK/no V1 guard. Continue on same V2 branch and combined workflow, then full V1 UI reachability parity.

---


## V2 JOINT EVIDENCE STAGING BATCH — 2026-11-19
- Owner instruction: do not stop after a report; next executable app-side migration segment after CI #110 305/305 PASS (last tested source `f4d91e0`). Reviewed current V2 General, consolidated handoff and latest branch commits/CI before edits.
- New `android_app/src/app_evidence_batch.py` stages at most 32 prevalidated Dhan-only evidence events in a deep copy of the *same existing* `DeviceEvidenceInbox`: candles, candle-trend, verified expiry roster, option metrics, CE/PE strikes, listed ATM window, option-derived factors. Explicit current selected-symbol cap/unique roster; rejects malformed event schema or missing caller trust; existing expiry/candle exact-observation guards remain intact. Any event failure causes **zero cache mutation**. On complete validation, copies data to the existing cache holders so Scanner/Watchlist/filters references stay attached. No HTTP endpoint, no broker, no generated signal, no counterfeit login, no fake LIVE.
- Added one combined offline regression `test_app_evidence_batch.py`: dual-lane success, rollback on later invalid expiry, original cache holder identity, unauthorized/unselected or unknown schema rejection. New exact-source CI outcome **PENDING** until Actions result seen.
- This does **NOT** connect the actual Android app to Oracle or independently establish revocable phone credentials. Future authorized transport must be authenticated outside this helper before passing `trusted_transport=True`; a boolean alone is not authentication proof. Actual V1 visual/WebView parity, News/Futures, live five-filter producer, verified Super Five, 1 Master + 3 delegated devices and APK remain pending. No V1, Oracle production, APK, or order changes.
- Next coherent app-side work: bind the staged evidence receive contract to a verified device-session/transport object (no new speculative production endpoint), and complete reachability/parity tests; keep one combined regression workflow.

---

## CURRENT CONSOLIDATED JOURNAL / OWNER HANDOFF — 2026-11-19

**Read this first:** [V2_SESSION_CONSOLIDATED_JOURNAL_20261119.md](V2_SESSION_CONSOLIDATED_JOURNAL_20261119.md) contains ALL confirmed work and failures/fixes from the current migration session, completed vs pending features, GitHub commit chain, acceptance boundaries, owner rules and **NEXT EXACT WORK**. This note preserves all prior category entries below.

**Latest verified executable:** `f4d91e0c35d45d693add39599e7da200174a464c`, [V2 CI #110](https://github.com/vaishnavi596/volume-king/actions/runs/44437755242) **305/305 offline tests PASS**. #103, #106 and #109 are *historical failures fixed by* #104, #107 and #110 respectively. Journal-only HEAD after CI is not additional test evidence. No live Oracle link or APK validated.

**Next:** Complete consolidated authenticated evidence/app-device-session contract and full V1 feature reachability, test as one coherent V2-only batch. **Do not stop merely after reporting; continue next concrete segment.** No V1 edits, Oracle production modifications, APK build, Yahoo/Angel fallback or live orders until owner authorizes later phases.

---


## VERIFIED — JOINT HTTPS QUOTE REFRESH BRIDGE, CI #110 (2026-11-19)
- Exact tested code `f4d91e0c35d45d693add39599e7da200174a464c`: [BOT KING V2 Pilot Contract Tests #110](https://github.com/vaishnavi596/volume-king/actions/runs/44437755242) **SUCCESS, 305/305 offline regression tests**, compile, gap-report and uploaded artifact successful.
- Previous #109 at `dce24bb18e41b169d8e6c522995ddbf0cab455b0` FAILED 8 tests owing to test-import/module-identity clash after a legacy test reloads `smart_data`; correction moves test imports into runtime `setUpModule()` rather than weakening `SmartDataSettings` validation. The earlier owner-reported #106 was separately fixed and #107 PASS. **Do not rerun #106/#109.**
- Accepted app-only integration: `app_readonly_refresh.apply_approved_quote_intent()` requires approved `RefreshIntent`, exact 0/5/70 selected-only roster and a configured `V2ReadonlyHTTPSReader`; isolated index/quote reads, failure retains last-good. Verified with injected mock, NOT a production Oracle call. Flet main stays disconnected until verified Master device authentication is approved and wired; source displays WAIT/HIST, no false LIVE. Production server, broker calls/orders and APK unchanged.
- NEXT V2 app-side whole segment: trusted-transport session bridge for all evidence feeds (candles/options/five factors) and UI/event parity, followed by consolidated regression. Keep current owner guard: no Oracle production edits and no APK build until app-side contract is ready.

---

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

# BOT KING V2 — LIVE STATUS & NEXT WORK SCHEDULE
**As-of 2026-11-18; no background task exists outside active turns.** Current authoritative details: [canonical snapshot](V2_CURRENT_CANONICAL_STATUS_20261118.md). Owner rules: [General](V2_GENERAL_FRAMEWORK_RULES.md). Historical evidence remains in [Master](V2_MASTER_JOURNAL.md) / [Work Log](V2_WORK_LOG.md).

## Verified state
**Source:** `51da2bef55e6b59d5ab47dffba7d513ed32a6e96`; **last CI #87** run `44368036631`, **249/249 SUCCESS**. Previous #86 was 246/246 PASS. Pre-docs HEAD `1cf6e0e1`. Current docs consolidation contains no executable code changes and therefore is not an additional source PASS.

| Lane | State | Unclosed acceptance gate |
|---|---|---|
| FT1 Master/login security | PARTIAL offline prototypes | Trusted enrollment, master + 3 delegates exact role/cap, integrated app and protected gateway |
| FT2 V1 layout + functional copy | PARTIAL, multiple actual UI controls wired | Full Dashboard/chart/Options/Super Five/Settings/alerts/Paper-safe feature parity, Android visuals |
| FT3 Dhan smart data/filters/candles/options | PARTIAL offline, guarded contracts | Real source/transport/token entitlement, adaptive selected roster, full option PCR/OI/news/futures and five-filter verified evidence |
| FT4 regression + V2 APK + eventual Oracle | NOT STARTED / NOT APPROVED | Full functional and device regression, separate signed V2 package, staged production backup/deploy/rollback |

## Executable next work order
1. Review latest commit (#86 source plus docs-only HEAD), update missing V1→V2 callable parity matrix for currently unported app-owned UI + controls.
2. In one small cohesive V2-only batch wire the next missing **actual** local handler/data-view behavior, with negative/positive regression and no server imports. Run exact-SHA Actions, inspect failure logs if any.
3. Record actual SHA/run/tests/limitations, update this file, Handoff, Master and Work Log together. Keep failed run history.
4. Repeat on other app-only screen groups; do not build APK now.
5. Only after app feature/regression gates and owner-approved build: independent V2 signed candidate and Android phone checks; then controlled Oracle production service integration and authenticated Dhan read-only tests **LAST**.

**Hard exclusions:** No V1 updates, no Angel One/Yahoo/old server settings or credentials, no unverified LIVE label, no order execution; Dhan OAuth and production require separate privileged review/approval. No automation/background monitoring implied.

**Continue command:** “BOT KING V2 journal अनुसार आगे बढ़ो” or “ok”. Read current snapshot, check newest GitHub code+CI, then perform a real safe batch. Never repeat planning as if code is already complete.


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
