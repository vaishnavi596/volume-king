## 2026-11-18 — DOCUMENTATION CLEANUP PHASE CLOSED LIMITED: 2 LEGACY REPORTS PRUNED
- Category index: [docs/README.md](docs/README.md). **Current docs = 43 (42 old + index)**, down from 44 old + index. Controlled history-only removal: A3 Dashboard legacy report commit `fe730700`, A2 chart/filter/options legacy report `54761833`; original evidence/commits and immutable history links retained in the index. No current AI/Filters/Oracle/security runbook erased.
- Post-second-prune GitHub CI #1846 [run 44163895968](https://github.com/vaishnavi596/volume-king/actions/runs/44163895968), test SHA `84f6722bf0581a941f2d294d64322b83b3afde26`, **COMPLETED SUCCESS: 1220/1220 tests**, repository-wide reference scan 349 files, 42 remaining non-index docs, 31 with external incoming references, 11 zero-inbound retained on content review, 0 broken relative Markdown links. This validates documentation cleanup source/CI only; Oracle/prod, APK, mobile unmodified.
- **No further automatic deletion needed** for this batch: remaining zero-reference docs carry useful future security, AI/Filters, commands or regression context. Reopen pruning only for a new specific redundant file with preserved provenance + reference check, not merely the user's older 60% heuristic. Continue open Android/Oracle integration gates separately.
- All new work uses category-prefixed dated entries in one `docs/BOT_KING_WORK_LOG.md`; don't write a second general journal. Old "pending" status lines further below are historical, superseded by the latest evidence here.

## 2026-11-18 — DOCUMENTATION CATEGORY ROUTER (current)
- Read [docs/README.md](docs/README.md) **before** opening scattered old audits. It categorizes all 44 `docs/` files into Core, AI/Market Memory, Filters/Market Evidence, Commands/Oracle, Android/UI, Release/Tests, and historical audit archive candidates.
- `AGENTS.md` now requires new entries in the **single** `docs/BOT_KING_WORK_LOG.md` with topic tags `[AI]`, `[FILTER]`, `[COMMAND/ORACLE]`, `[ANDROID]`, `[CI/RELEASE]`, `[DOCS]`; category index links topic documents without copying whole logs.
- Classification is not a deletion/archival result. Do not permanently delete historical evidence based on guessed 60% usefulness. First verify dependencies, unique CI & rollback/source hashes, and archive/rewrite links; no old failure is erased.
- Current live work remains T09 Oracle Assessment candle publisher bridge (GitHub source+CI PASS only; customized Oracle deployment unverified), Smart Memory/research planner pure source/offline only, five filters runtime not proven and sixth visual slot blank. No new APK and no live orders.

## 2026-11-17 — ACTIVE CONTINUITY RULE (supersedes historical handoff snapshots)
- `AGENTS.md` is authoritative: **OK means do the next safe task within this turn, not report and stop**. Read current GitHub evidence, fix or audit the next unblocked related item, and append accurate results to the canonical Work Log. Stop only at real access/approval/safety boundaries; no claim of background work after the turn.
- **Pre-edit review: last 3 relevant changes + associated CI**, not an automatic 10/15-file sweep. Additional evidence only when a demonstrated dependency or failure requires it.
- **CI parallel policy:** `.github/workflows/test-only.yml` workflow concurrency cancellation was removed at `ccf10fc5`; #1809 SUCCESS for that commit (source CI only), so old in-progress tests should not be auto-cancelled by new pushes under that workflow. Runner scheduling can still queue jobs. Six visual filter slots = five existing evidence engines plus one inert blank placeholder, no sixth score.
- **Open boundary:** source-only GitHub Option Evidence Cache writer/reader is present; customized running Oracle `assessment_api.py` / option-chain producer parity is NOT established. Do not invent verified bullish/bearish signals or deploy to Oracle without protected operator proof, backup and gate. No new APK until release acceptance.

## 2026-11-17 — CURRENT RELEASE HANDOFF: Joint #6 CLOSED; Oracle integration remains separate
- Exact immutable [Joint #6 run 44042605910](https://github.com/vaishnavi596/volume-king/actions/runs/44042605910) on SHA `b413b23f676f00478b2f0b38d2c01f3e53b06be5`: **COMPLETE SUCCESS 5/5 jobs** (full offline, login/watchlist/index, candles/scanner/Super Five, options/five-filter, Android release contract). Runtime source under test ends at T13 `879d71bd`; newer commits through this handoff are docs/CI comment only. **Offline source/CI = CLOSED — VERIFIED. Do not rerun unchanged tests.**
- **Separate open prerequisites:** T01–T03 deployed market/index quotes freshness, T09 actual external five-evidence factors, T11 broker equity option entitlement, T12 Dhan/Oracle collector request budget, T14 deployed assessment and T15 auth/orders-OFF runtime all require read-only operator evidence; T16 new signed versionCode/versionName APK and phone market test are NOT complete. Existing handoff contract warns deployed Oracle `/opt/bot-king-server/server.py` differs from GitHub `backend/server.py`; never blindly copy source to prod. Global-70 cross-watchlist server enforcement S18 remains unverified deployed; must remain a distinct gate.
- Existing read-only operator scripts: `scripts/audit_oracle_app_routes_readonly.py` (local deployed source only), `scripts/audit_oracle_five_filters_readonly.py` (source-only, no proof of real producer), `scripts/audit_oracle_collector_runtime_readonly.py` (3 bounded local GETs requiring operator pairing key, no Dhan calls/orders). These **were inspected in GitHub, not executed on Oracle**; do not mark prod pass. Actual operator runtime access unavailable here. No production restart, token changes, broker calls or APK in this stage.
- Permanent owner rule in `AGENTS.md`: evidence-backed result ledger and **CLOSED** tasks remain closed unless new requirement, changed code/provider/production, actual failure or explicit credible suspicion; preserve test run/SHA and don't initiate duplicate checks. All future filters and free-TV app remain deferred and separate.
- Next action: obtain actual sanitized Oracle operator read-only evidence once authorized access exists; classify 70-global/watchlist, routes, current collector and option/assessment actual availability; prepare APK only after release gates and visible version bump are met.

## 2026-11-17 — LATEST HANDOFF: Joint #5 5/5 GREEN; T13 manual after-close selected 3m HIST CI pending
- Branch `fix/botking-joint-audit-70-15-20261115`; before every edit inspect the **last three relevant changed files/commits and associated CI results**; `OK` means continue actual safe work. Owner rules: root `AGENTS.md`; evidence `docs/BOT_KING_WORK_LOG.md`, `docs/BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md`.
- Joint Gate #5 [44037564321](https://github.com/vaishnavi596/volume-king/actions/runs/44037564321) at `7268685314` **5/5 PASS**, full **1143/1143 PASS**; closes prior Joint #4 real zero-clock cold-login/watchlist 1m failure and option/assessment first-request throttling tests. This validates prior SHA only.
- T13 new source `5e0dc852f`: Watchlist explicit **Refresh data** button remains market-hours-independent for equity+index quotes (30s manual floor). Only if market is closed and Watchlist visible, attempts ONE eligible selected 1m Dhan historical input via `warm_selected_watch_three_minute_early(generation,explicit_closed=True)` for 3m HIST, not automatic off-hours history, not all 51 symbols. Same shared 3/180 request budget, 30s provider gap, per-symbol 180s floor, Dhan cooldown, 5m history scan busy skip and last-good 1m/3m retention; live verification never asserted. Status string changed to explicit `HIST ... (NOT live)` at `879d71bda`.
- Test updates: cold-boot manual callback+busy tests `376eca4b7` (+2), early-helper actual after-hours quota/provider/retention `8aaf4feff` (+3), old manual quote-hours contract `cd820f6e1`; at latest checkpoint #1748–#1752 offline regressions **IN_PROGRESS**. #1749 at `376eca4b7` 1145 tests, **three test-only FAIL**: expected HIST uppercase, old prohibition on literal refresh_hours in manual quote body, old early-helper guard literal; all corrected in subsequent source/test SHAs. Check #1752 [44039501498](https://github.com/vaishnavi596/volume-king/actions/runs/44039501498) job 133890359021 and exact full test log BEFORE marking PASS. Once clean, trigger ONE controlled five-scope No-APK Joint gate using existing workflow, then journal results.
- T01/T03/T10 actual Oracle and on-phone login/index/Watchlist data; T09 independent five verified evidence engines; T11 NSE equity option entitlements; T12 real collector age/429 budget; T14 deployed assessment; T15 orders OFF/auth/read-only; T16 signed APK + actual mobile remain **UNVERIFIED**. `pyproject.toml` still 2.3.130; do not bump/build/restart/execute orders until release gate.
 
## 2026-11-17 — LATEST HANDOFF: JOINT #4 fast-boot failure repaired; #1747 retest pending
- Branch `fix/botking-joint-audit-70-15-20261115`. User `OK` = continue safe source/test work. **Before every write** inspect exact last 10 changed files/commits and 10 GitHub CI outcomes. Journal `docs/BOT_KING_WORK_LOG.md` and T01–T16 matrix `docs/BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md` are authoritative.
- Joint #3 **5/5 PASS** 1117 suite; T04 early selected 3m source/test CI #1739 **1126/1126 PASS**; T10 NIFTY/BANKNIFTY/SENSEX 1m early source/test CI #1741 **1135/1135 PASS**. But Joint #4 [run 44034990865](https://github.com/vaishnavi596/volume-king/actions/runs/44034990865) **FAILED** fast `login-watchlist-index` job (7/74) although complete offline 1135 PASS: zero/uninitialized monotonic clock treated as recent request for first 1m Watchlist 30s global and 180s per-symbol cooldown. Source fixed in `6eade527d` + `d7b2d1914`; three new fake-clock tests `2c26197bb`. CI #1744 [44035523988](https://github.com/vaishnavi596/volume-king/actions/runs/44035523988) **1138/1138 PASS**. **Joint must be re-run**, old failure not relabeled PASS.
- Related first-request zero-clock source bugs in manual LTP refresh, auto equity quote, Watchlist page entry, resume, auto options and per-symbol Oracle assessment cache fixed `e23eff853d85ca768c8222c42cdce40f00d8248e`, full #1745 [44036159361](https://github.com/vaishnavi596/volume-king/actions/runs/44036159361) **1138/1138 PASS**. Five new executable callbacks at `4c35e7f63`; #1746 **1143 tests, 1 test-only FAIL** due checking `select()` while actual nav guard lives `render_page()`; test-only correction `94014be81772f4fa2e98aabf732996032d03b319`. #1747 [44036845005](https://github.com/vaishnavi596/volume-king/actions/runs/44036845005) syntax PASS, full offline **RUNNING at last checkpoint**. Inspect completed logs before new source changes; if green trigger one controlled no-APK Joint #5.
- All above are offline GitHub proofs, not actual Oracle/Dhan/phone evidence. Five external evidence engines can show legitimate WAIT. T13 explicit after-hours *3m candle* refresh remains missing (manual equity/index quotes exist), T11 Dhan equities option entitlement/deployed Oracle route, T12 upstream 429/caps, T14 deployed assessment, T15 orders disabled production, T16 signed APK/one-phone still unverified. `pyproject.toml` still 2.3.130; DO NOT touch release version, restart Oracle, fetch secrets or send real orders.

## 2026-11-17 — LATEST HANDOFF: T04 + T10 1m priority source/CI PASS, integration still blocked
- Branch `fix/botking-joint-audit-70-15-20261115`. User `OK` means advance to next safe work; **before each edit inspect the actual last 10 commits/changed files and 10 CI results**. Append every result to `docs/BOT_KING_WORK_LOG.md` and T01–T16 matrix, retain historical failures.
- Full Joint Regression Gate #3 [44031362802](https://github.com/vaishnavi596/volume-king/actions/runs/44031362802) at `676fc1e4e` **5/5 PASS**, full 1117/1117 tests. T04 early one-selected Watchlist 1m→3m before long 5m tail: [CI #1739](https://github.com/vaishnavi596/volume-king/actions/runs/44033512195), source/test SHA `4586d74c0`, **1126/1126 PASS**. T10 early serialized index 1m for NIFTY/BANKNIFTY/SENSEX: [CI #1740](https://github.com/vaishnavi596/volume-king/actions/runs/44034186877) source `3f00d978d` **1126/1126 PASS** and [#1741](https://github.com/vaishnavi596/volume-king/actions/runs/44034335037) source+nine tests `6082278618f1d3baad939c5c2b9a93d13d347aa5` **1135/1135 PASS**. These are **OFFLINE SOURCE/CI ONLY**.
- Dhan 1m new acquisitions reuse the serialized history lane, 1.5-second spacing, 30s / 3-per-180s selected-watchlist budget and existing 180s index clock, with 429 cooldown and last-good historical/not-live flags. Source and mock tests passed, **actual mobile startup latency, provider 1m freshness, equity/index quotes and 5 evidence engines are not proven**.
- Still blocking T01–T03 actual first-login/index/watchlist, T09 News/Futures/Options evidence WAIT where source absent, T11 RELIANCE/HDFCBANK equity option-chain Dhan entitlement/deployed route, T12 upstream request counts/rate, T13 after-hours manual Watchlist *candle* refresh (quote-only button exists), T14 deployed Oracle assessment, T15 production auth/orders-off proof, T16 new version/sign/build/one-phone test. Oracle production was NOT accessed, no signed APK or live orders. `pyproject.toml` remains **2.3.130**. Do not bump/build until release gate policy.
- Next safe task: T13 explicit one-symbol after-hours manual 1m→3m request bounded by user action/provider cooldown, or Oracle read-only operator audit if access becomes available; rerun full joint regression after source freeze. Current latest evidence is in the Work Log / Matrix, not historical paragraphs below.

## 2026-11-17 — JOINT-GATE-3 CURRENT HANDOFF (read this before further edits)
- Working branch: `fix/botking-joint-audit-70-15-20261115`. Latest executable source/test SHA `03eb8ce8cf63a935cfcec836a836625472180db4` passed offline CI #1736, **1117/1117 PASS**; the prior 5m-fixture fix passed #1733, **1114/1114 PASS**. Current HEAD includes subsequent **documentation** and a no-semantic-change workflow trigger commit. Check live GitHub HEAD and last 10 commits/runs before writing.
- Single controlled [Joint Regression Gate #3](https://github.com/vaishnavi596/volume-king/actions/runs/44031362802) pinned to `676fc1e4e1fdf9731ff16a426bed06d2ddc0c757`: four groups **PASS** (login/watchlist/index, candles/scanner/Super Five, options/five filters, Android release contract); complete offline suite syntax PASS, full test step **RUNNING** at latest observed checkpoint. Do not claim final joint PASS until job 133863838602 completes.
- Source areas repaired since prior phone app: Watchlist bounded 1m→3m historical warmup, safe last-good 3m votes, selected Scanner 1m default and history retention, automatic Scanner exchange-hours guard, Android resume 1m/5m cache isolation. These are source/CI proofs only: **mobile actual functionality not verified**.
- Independent source risk: initial serialized 54-symbol 5m scan keeps `dhan_history_scan_active` true, so selected Watchlist 1m→3m warmup and index 1m poll yield until main scan completes; cold-start 3m WAIT delay remains unmeasured/unresolved. After-hours manual Watchlist refresh updates quotes, not 3m history. Five independent evidence engines may rightly show WAIT when News/Futures/Options lack verified source.
- Oracle PRODUCTION parity, Dhan entitlement for RELIANCE/HDFCBANK option chains, real collector request age/pacing, and protected assessment routes are still not attested. Do not deploy/restart server or build/sign APK without release gates and authorization. `pyproject.toml` currently **2.3.130**; UI derives visible version dynamically; any future release requires a newer versionName and versionCode, signed artifact verification, then real one-phone validation.
- Main proof journal: `docs/BOT_KING_WORK_LOG.md`; current T01–T16 queue: `docs/BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md`. `OK` means keep moving on the next safe task, not a declaration of PASS.

# CURRENT CROSS-CHAT RULES — 2026-11-17

**READ FIRST:** [AGENTS.md](AGENTS.md) contains the permanent BOT KING working rules. **"OK" means continue to the next safe test/repair**, not merely report and stop. Before edits inspect the last three relevant changed files and related CI results; maintain a consolidated T01–T16 test matrix, batch coherent fixes, keep CI/tests moving when independent, journal evidence and block APK until final gates pass. This is a workflow rule, **not** a claim of autonomous background work after the chat ends. Current matrix: [docs/BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md](docs/BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md).

## 2026-11-16 — ORACLE-FILTER-AUDIT-01: no-network five-filter deployed source classifier
- #1571 [43832625673](https://github.com/vaishnavi596/volume-king/actions/runs/43832625673) at `4b28e245` **932/932 PASS**; #1570 at `3fa20d64` **931/931 PASS**. Latest-eight CI inspected.
- New `scripts/audit_oracle_five_filters_readonly.py` commit `2bba9280` uses AST parse/sha256 on deployed custom `/opt/bot-king-server/server.py`, classifies missing / recognized known `not_configured` five-filter placeholder / other source. It NEVER labels a nonplaceholder as functional; outputs `producer_proven_functional=false` and `deployed_runtime_route_verified=false`. No HTTP, env/key, Dhan requests, imports from custom server or writes. Offline tests `tests/test_oracle_five_filter_runtime_source_audit.py` commit `e6677c7f`; latest CI still pending at handoff creation.
- Three Oracle checks are now prepared: `scripts/audit_oracle_app_routes_readonly.py`, `scripts/audit_oracle_collector_runtime_readonly.py` (protected GET requires secure local operator key), `scripts/audit_oracle_five_filters_readonly.py`. **None executed on production** because no SSH execution tool available. Need actual sanitized outputs before staged backup-first custom Oracle fixes. Source five-filter producer still absent, index/equity PCR entitlement not proven, no new APK under owner release gate. Journal and 6-stage tracker updated.

## 2026-11-16 — PCR equity source gate-02, no APK
- Prior exact #1569 [43831492105](https://github.com/vaishnavi596/volume-king/actions/runs/43831492105) **931/931 PASS**, #1568 **928/928 PASS**. Backend new `GET /v2/option-underlying-status/{symbol}` `3fa20d64`: authenticated, bounded, **mapping-only**; expiry/chain/PCR all unverified, zero Dhan calls. Guard regression `4b28e245`, #1570/#1571 initially in_progress. This GitHub backend source is **NOT installed on Oracle**.
- All five Oracle assessment filters are still hard-coded unavailable in repository backend; real producer, stock F&O entitlement and fresh PCR unproven. Do not interpret historical 100/0 as five-filter probabilities; no new APK before permanent release gates.
- Next: finish latest CI, perform operator's grouped read-only deployed custom Oracle routes/source hash and collector age audit, inspect one/two selected equity listed expiries with quota guard, stage backed-up server changes and genuine separated filter inputs. Details in `docs/BOT_KING_WORK_LOG.md` / `docs/BOT_KING_WORK_RESULT_TRACKER.md`.

## 2026-11-16 — PCR + five Oracle filters: source audit and no-fanout diagnostic
- Prior #1567 [43830743529](https://github.com/vaishnavi596/volume-king/actions/runs/43830743529), job `133175214724`, **928/928 PASS**; audit source tests include mapped equity PCR and five WAIT filters. #1566 initially in_progress.
- New `backend/option_underlying_status.py` [38926b79](https://github.com/vaishnavi596/volume-king/commit/38926b79f890199dc9933f2ee5fabaed90c79c63) returns bounded **mapping-only / no expiry or PCR verified** information for indices and equities; `tests/test_option_underlying_status.py` [ee08f363](https://github.com/vaishnavi596/volume-king/commit/ee08f3635817d00e54950e7184caedf6c3694fbe) tests no broker requests and false entitlement claims. New #1568/#1569 CI **in_progress** initially; inspect latest.
- Critical: user says equity PCR seems absent and ALL 5 Oracle assessment filters do not work. Code has index+equity PCR APIs for selected underlying only, but option expiry/chain entitlement for equities NOT proven. GitHub backend `GET /v2/assessment/{symbol}` remains **placeholder not_configured/all unavailable**; no 100-point live filter producer, no provider validation. Source utility is NOT deployed on custom Oracle and does NOT fix UI WAIT. Next: real Oracle route/collector and bounded per-selected-equity listed expiry/chain diagnostics, source-backup-first integration and five-filter producer from trustworthy per-symbol evidence. No APK before release gate, live orders OFF.
- Exact journal `docs/BOT_KING_WORK_LOG.md`, six-stage tracker `docs/BOT_KING_WORK_RESULT_TRACKER.md`.

## 2026-11-16 — PCR EQUITY + FIVE FILTER AUDIT: NOT YET IMPLEMENTED END-TO-END
- Owner: suspects PCR appears for NIFTY/BANKNIFTY/SENSEX but not most equity symbols, not yet exhaustively phone tested; reports five bullish/bearish filters NOT working. **Source audit proves no index-only restriction**: `src/server_feed.py` option expiry/chain methods admit 51 mapped equities, backend supports `NSE_EQ` for verified option underlying when instrument master maps it. But equity LTP mapping ≠ available Dhan listed option expiry / options entitlement, so no assumption that all stocks have PCR. `src/main.py` auto-requests only SELECTED underlying/expiry, not all 51; respects 3.25s option pacing and 422/429 cooldown.
- **Specific confirmed source gap**: `backend/server.py::GET /v2/assessment/{symbol}` **always returns not_configured, five assessment filters unavailable and four factors unavailable**; `src/shared_assessment_ui.py` correctly renders WAIT. A source placeholder is not a working Oracle factor producer. Real Oracle server.py may differ and has not been audited; Historical technical/candle B/S percentages are NOT 5-filter probabilities or verified live.
- PCR offline contract test `tests/test_dhan_equity_pcr_contract_audit.py` commit `695e5d9c`; five-filter no-fabrication audit `tests/test_oracle_five_filters_source_audit.py` commit `a0faec39`. Both **test-only**, CI still needs latest-run verification; no APK and no Oracle deployment.
- **NEXT**: actual Oracle route + collector Read-only scripts, bounded instrument-master / listed expiry / chain status for one or two mapped equities (not fanout 51); implement accurate validated 5-filter producer with per-source freshness and unavailable classifications rather than invented percentages; test index/equity PCR and five-factor UI on phone; update `docs/BOT_KING_WORK_RESULT_TRACKER.md` and `docs/BOT_KING_WORK_LOG.md`. Permanent owner rule APK LAST.

## 2026-11-16 13:45 IST — FOLLOW-UP PHONE STATUS: local analysis recovered, upstream unverified
- Three more screenshots of **same v2.3.130** show Settings green `No active errors reported`, **54 analyzed / 0 errors / 0 insufficient / 0 pending**, an improvement from earlier 52/54 and two active errors at 13:40. Historical Error History still correctly lists previous FeedErrors; absence of active errors at 13:45 does not prove Oracle live quotes or independent index 3/3 restored.
- Scanner technical indicators show historical VWAP bearish, Pivot bullish, neutral SMC/order block/FVG/liquidity sweep. OI PE highest strike 25,200, CE highest strike 25,300, ATM ±3 strikes available, Max Pain 25,250 **displayed but UNAVAILABLE / unverified / display-only**, so four-factor/option signals remain NOT VERIFIED. Do not fabricate live options scores. Earlier Super Five HTTP429 + 38 unattempted, watchlist stale/invalid, BANKNIFTY/SENSEX LTP unavailable remain unresolved pending new evidence.
- Exact records in `docs/BOT_KING_WORK_RESULT_TRACKER.md` and `docs/BOT_KING_WORK_LOG.md`, both updated. Priority still read-only actual Oracle deployed-route/collector audit before server edits or next APK. Signed Build #645 itself passed; phone end-to-end is partial, live orders OFF.



## 2026-11-16 13:39–13:40 IST — ACTUAL PHONE SCREENSHOTS: v2.3.130 NOT ACCEPTED
- Signed Build #645 [43825726713](https://github.com/vaishnavi596/volume-king/actions/runs/43825726713) **SUCCESS**, job `133159009980`, `919/919 PASS`, versionName `2.3.130`, versionCode `74501`, package `com.botking.bot_king`, pinned signer and artifact [14206624325](https://github.com/vaishnavi596/volume-king/actions/runs/43825726713/artifacts/14206624325) verified. **Phone visibly launches v2.3.130, but end-to-end FAILED/PARTIAL.** Do not build another APK before permanent release gates.
- **7 user phone screenshots**: NIFTY LTP `25,063.70` ~28s collected (exchange time unverified), **BANKNIFTY and SENSEX unavailable**; Oracle watchlist snapshot **stale/invalid** and last-correct prices retained; System Health **2 failures BANKNIFTY/LT**, 54-symbol filters 52 analyzed 2 errors; Error Doctor `dhan_index_ltp_batch` recovered at 13:38:27, `dhan_options`, `oracle_assessment`, `watchlist_dhan_batch`, `scanner` and `dhan_batch` subsequent FeedErrors.
- **Super Five historical scan HTTP429/cooldown**, 38 symbols not attempted; 1 history unavailable; 5 engines 0/5 verified overall WAIT. Watchlist historical votes present but LTP cached NOT live; News/Futures/Options WAIT. NIFTY 5m historical chart/indicators display but signal WAIT NOT live. Six bottom tabs visible, old three-tab UX direction not yet enforced.
- **Primary next action:** Oracle operator run two already-written **read-only source 9-route audit** + **protected collector snapshot age/status audit**; log only sanitized codes, state/age/count. Without deployed custom-server SHA/flag, do not blame one isolated source or blindly deploy. Stage source vs Oracle diffs, timestamp backup, targeted repair and rollback. Then test index 3/3, watchlist snapshot, options, Oracle assessment and 429 historical pacing; journal CI/Oracle/device separately.
- Canonical work-result ledger `docs/BOT_KING_WORK_RESULT_TRACKER.md` has 13:39–13:40 user evidence; `docs/BOT_KING_WORK_LOG.md` has signed Build and detailed phone-audit entry. Current source-only CI 919/919 PASS does **not** override actual phone failure; source Test errors earlier closed. No live orders or Yahoo fallback.
## FIRST READ IN NEW CHATS — SIX-STAGE WORK/RESULT/ERROR/REPAIR TABLE

Use [`docs/BOT_KING_WORK_RESULT_TRACKER.md`](docs/BOT_KING_WORK_RESULT_TRACKER.md) FIRST. It is the owner's permanent **Stage 1–6** audit checklist with columns for work, source CI, Oracle proof, APK/build/device result, error→repair and next action. Then read the append-only `docs/BOT_KING_WORK_LOG.md` and release gate `docs/BOT_KING_RELEASE_GATE_POLICY.md`. Update all relevant records **together with each change**, not merely at release time. As-of 2026-11-16 GitHub regression #1565 at `39b34182` is **919/919 PASS**. v2.3.130 #645 remains diagnostic while customized Oracle deployment is unverified. No next APK before all release gates.

# BOT KING — START HERE IN EVERY NEW CHAT

**Project:** BOT KING (Dhan-only Android scanner and simulated Paper Bot)
**GitHub:** `vaishnavi596/volume-king`
**Current integration branch:** `fix/botking-joint-audit-70-15-20261115`
**Latest verified release APK:** `2.3.126` (GitHub Build #641 PASS); **installed phone:** `2.3.125` with reported first-login refresh/Super Five issues. No 2.3.126 mobile PASS. Confirm newest HEAD/build before making subsequent changes.
**Latest verified APK build run:** https://github.com/vaishnavi596/volume-king/actions/runs/43753960172 (2.3.126, `versionCode=74101`, signed, artifact ID `14177263980`). Previous 2.3.125 run: 43751755544.
**Latest verified 2.3.125 build:** SUCCESS, 804 tests PASS, versionName=2.3.125, versionCode=74001, pinned signing verification PASS; GitHub artifact `volume-king-apk` ID `14175849838` uploaded. **Device test still pending.**
**Canonical master improvement checklist — READ NEXT:** `docs/BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md` (12 work groups, source/CI/Oracle/device evidence and journal corrections).
**Historical 14–15 Nov step-by-step audit:** `docs/BOT_KING_PREVIOUS_TWO_CHATS_STEP_BY_STEP_20261114_15.md` (51 numbered checks with provenance and limitations).
**Prior verified full offline suite:** 804/804 PASS at commit `ee1d75a4137a172d776d0e6d607986fe4659605a` (run 43751577312).

> **Required new-chat procedure:** Fetch this file and
> `docs/BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md`, `docs/BOT_KING_WORK_LOG.md`, and
> `docs/BOT_KING_ORACLE_APP_CONTRACT_20261115.md` at the **latest branch HEAD**;
> inspect newest GitHub Actions result and actual `pyproject.toml` version BEFORE
> editing or claiming any APK is final. Do NOT assume this document is
> automatically loaded into a new chat: give the new chat the repository URL or
> this document link. Never report a stage PASS from a historical run.

## 1. Confirmed system facts (Oracle and user terminal output)

- Oracle host `bot-king-vnic`, service `bot-king.service`, directory
  `/opt/bot-king-server`; Nginx public HTTPS. Production Oracle
  `server.py` contains assessment and expiry-cache features not present in
  the GitHub `backend/server.py`. **NEVER replace wholesale.**
- Health HTTP 200 and service active. Oracle health intentionally reports
  `broker_connected=false`, `live_orders_enabled=false` (not a failure).
- S17 13/13 unauthenticated route security checks PASS.
- Authenticated Oracle `GET /dhan/status`: HTTP 200,
  authenticated=true, market_data_configured=true, token_source=oauth_consent,
  token_validity=expiry_checked, reauthentication_required=false.
- Authenticated Oracle `GET /v2/snapshot`: HTTP 200, source=dhan,
  51 equity quotes; snapshot age at probe 79.1 seconds,
  freshness=unverified, error=null.
- S19 authenticated `POST /dhan/index-ltp-batch`: HTTP 200 with
  NIFTY 25144.3, BANKNIFTY 61034.1, SENSEX 81592.45; unavailable=[],
  freshness=unverified. This validates response at test time,
  **not current market prices**. Do not claim these are exchange-live.
- Oracle S15 server route patch deployed and health passed.
  S18 **WatchlistStore** global-70 / cross-list-duplicate patch remains
  **staged in GitHub only**. Do not claim Oracle production is updated.
- Do not modify Dhan OAuth, credentials, token renewal or enable orders while
  fixing quote display; never print keys in reports.

## 2. User-approved behavior

- On every successful login, whether market is open or closed, **load the last
  available verified-origin equity quotes, three indexes and available cached
  candles** to Dashboard/Watchlist/Super Five. Label timestamps/freshness
  honestly: last-known/unverified, not exchange-live.
- While market is CLOSED: pause repeated market-data auto polling after initial
  load; allow bounded first-load recovery of missing quote data, not a
  never-ending API loop. The full 51-historical scan after login is distinct.
- When open (~09:15 IST, follow existing session-calendar guards): regular
  independently throttled quote pipelines should run again.
- Index batch is independently scheduled, not blocked by the Watchlist
  scanner. Super Five and scanner reuse available cached data; Dhan calls
  serialized and 429 cooldown respected. Avoid repeated 51-candle fanout.
- Five saved watchlists, **maximum 70 equities TOTAL across all five**.
  Each symbol may be in **ONE LIST ONLY**. To move it, remove from old
  list first. Never delete user's saved watchlists.
- Separate prices from signals. Missing/untimestamped News/Futures/Options
  evidence must remain WAIT rather than inventing BULLISH/BEARISH.
- Paper Bot is simulation, must not submit real orders.
- User prefers GitHub+Oracle work in 2–4 coherent edits/tests per batch,
  minimal repeated questions, no generated screenshots unless requested.

## 3. Confirmed GitHub work (not automatically deployed to device)

- 2.3.124 signed APK workflow PASS (run
  https://github.com/vaishnavi596/volume-king/actions/runs/43746262145),
  but that build predates latest first-login recovery.
- New branch 2.3.125:
  - `4e50d226`: Login fallback from failing individual NIFTY LTP
    (unless 429) to authenticated three-index batch, with strict
    source/safety checks and price retention after provider reset.
  - `6bf04e96` and `ea22fb2e`: earlier intermediate closed-market
    bootstrap attempts FAILED older regression tests. **Not release heads.**
  - `ee1d75a4`: restored old market-open polling code patterns and
    added bounded closed-market first-load bootstrap. Verified 804/804 PASS.
  - `e587485b`: version bump to 2.3.125 and signed APK build trigger.
  - Report only the ACTUAL current Actions result at the time you check.

## 4. Critical open issues

1. Device report: Watchlist, all three index prices, Super Five prices and
   automatic scanning appeared blank/stuck on the installed app. The installed
   app's version was **not confirmed**; do not equate current GitHub source
   with the installed APK. Oracle authenticated data checks passed.
2. Need finish/check 2.3.125 signed APK build, versionName/versionCode,
   package/signing identity, artifact before recommending installation.
   An APK build PASS != on-device PASS.
3. Need test first closed-market login, missing-data recovery and market-open
   refresh on Android; check Error Doctor and reconnect status. Normal
   market-hours refresh should not restart indefinitely.
4. S18 Oracle WatchlistStore global-70 uniqueness enforcement needs backup,
   staged patch review, server tests, guarded deployment and rollback. Existing
   watchlist data must be preserved.
5. Selected batch stock quotes and multi-symbol options remain to be
   tested end-to-end against Oracle with authenticated bounded calls.
6. Independent Super Five, scanner and candle cache parity / stale-history
   labels need actual device verification.

## 5. What to record after *every* substantial work batch

Before leaving a chat, commit a dated update to THIS file or
`docs/BOT_KING_WORK_LOG.md` containing:
- **Baseline**: exact branch, HEAD SHA and installed APK version (if known).
- **Change**: files modified, functionality and reasons; link commit(s).
- **Test**: CI run and actual PASS/FAIL with test count; Oracle results
  separate from device/user tests.
- **Production status**: staged / deployed / restarted / rolled back;
  backups and which credentials untouched.
- **Known issues / next three actions**: never hide unfinished work.
- **Safety**: read-only market-data vs paper mode vs live orders disabled.
If an item has no proof, write **UNVERIFIED**, not PASS. Do not upload
private keys, Dhan credentials, logs with tokens or user account details.

The historical authoritative contract is:
`docs/BOT_KING_ORACLE_APP_CONTRACT_20261115.md`.
The append-only batch journal is:
`docs/BOT_KING_WORK_LOG.md`.

## 2026-11-16 urgent phone feedback

- **Installed v2.3.125**: old saved quote values visible (RELIANCE ₹1339.70), but login Watchlist refresh not confirmed.
- Code defects patched `5da68b3a`, `9d94169a`, `bd5c2212`: stale saved quote prevented closed-market retry; Login outcome did not synchronize Watchlist status. New dedicated behavior tests PASS 809/809 on run 43753705425.
- Release candidate 2.3.126 is to be built and **independently signed/installed/tested**; don't call the phone fixed from offline tests.
- Market-open 09:15–15:30 IST polling and 60-second equity/index timers were preserved. The price may be numerically unchanged when the exchange is closed; inspect the displayed 'Login snapshot' status and snapshot collection age instead of demanding an impossible live tick.
- No Oracle restart or token reset was performed for this fix.

## 2026-11-16 master checklist and correction checkpoint

- The **authoritative current improvement inventory** is `docs/BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md`; start new chats there before implementing further batches. It separates original requests from actual Source/CI/Oracle/API/Device proof and reconciles older conflicting journals without deleting history.
- Current Android code uses **15 movable filter slots (10 defaults + 5 extra)**; the previous 10-slot-only status was an intermediate branch, not the latest integrated source. Original historical audits still use 10 default calculation filters.
- **2.3.126 Build #641 SUCCESS** with versionName `2.3.126`, versionCode `74101`, signing and artifact. **Phone 2.3.125 remains failing/unverified for first-login refresh, data and Super Five B/S**; newer APK is not automatically a device fix.
- Futures real acquisition, authentic News and verified independent Options directional scoring remain **PENDING**; Oracle S18 total-70 unique-watchlist server patch is **NOT DEPLOYED** as far as existing evidence shows. No real orders enabled.
- Older “need to finish 2.3.125 build” and “2.3.126 to be built” paragraphs above are **historical**; this checkpoint supersedes them. Do not silently edit/delete those historical records.


## 2026-11-16 — NEWER DEVICE FAILURE AND 2.3.127 REPAIR TRACK

- **Most recent user device report supersedes earlier installed-version notes:** v**2.3.126** was installed; **automatic refresh after login still fails/not observed** and Super Five B/S filters/data remain incomplete. Option Chain for HDFCBANK and other supported underlyings needs end-to-end verification. **MOBILE FAIL overrides any older "device untested" label for the reported behavior, but does not prove all screens failed.**
- **Do NOT call 2.3.126 fixed merely because Build #641 and 809 offline tests passed.**
- **Approved next repair programme:** `docs/BOT_KING_2_3_127_JOINT_REPAIR_PROGRAMME_20261116.md`. Read it before touching app: batches 127-A through 127-E (login bootstrap; independent equity/index; Super Five historical B/S; Options/HDFCBANK; regression/build). Version 2.3.127 is a **planned candidate, not yet built**.
- App source audit found per-login session bootstrap is not guaranteed on app-open; connected-only poll guards and closed-hours option loop are potential blockers. Actual mobile and server correlation remains unverified.
- Oracle production and Dhan OAuth unchanged; live orders OFF. Preserve old app data, 15 filters, five watchlists/global 70, historical 51+3 and signed package/versionCode policy.


## 2026-11-16 — New handoff checkpoint after 127 source joint work

- **Integration branch:** `fix/botking-joint-audit-70-15-20261115`; latest source full-regression verified commit `6fb58023a61c0ca55548fa48eb18860dcbadc933` [run 43759426158](https://github.com/vaishnavi596/volume-king/actions/runs/43759426158) **825 tests PASS**. Documentation commits after that do not change the tested app code.
- **Batch 127-A:** session-scoped login bootstrap, equity/index statuses, no second provider generation reset; offline CI PASS. Existing phone 2.3.126 Login Auto-Refresh **MOBILE FAIL**, v2.3.127 device test NOT DONE; secure auto-login on app restart still requires enrollment/reconnect design.
- **Joint 127-C/D source:** closed-hours local Super Five historical votes and saved rankings/technical B/S, bounded five-symbol headline context (not voting News score), selected Dhan broker-listed expiry/Option Chain first-login request, session-isolated RELIANCE/HDFCBANK/index option contexts and CE/PE OI/ΔOI/Volume preview, Error Doctor Paper Bot status, and trusted broker SessionExpired 401 handling. These are GitHub source/CI evidence only.
- **Read-only Oracle audit pending:** `scripts/check_127_oracle_readonly.py` is ready for authorized operator execution (requires preexisting env-supplied `BOTKING_URL` and `BOTKING_PAIRING_KEY`; never log/persist secrets). It summarizes 51 snapshot, 3 indexes, optional <=70 selected NSE equities, RELIANCE and HDFCBANK listed expiry/chain, 429/422 results. **It has not run on Oracle.** Never overwrite Oracle-custom `server.py` with repository backend.
- **Paper Bot:** already five manual simulated profiles, Start/Pause/Stop and paper ledger; source shows state in Error Doctor. Not an unattended Dhan-tick autobot; actual Android behavior UNVERIFIED. Live orders remain OFF.
- **Unfinished release gates:** independently verified News/Futures directional engines are WAIT; authenticated 51+3 refresh and listed stock CE/PE/provider entitlement checks on current Oracle are PENDING; Android tests for open/closed login, historical Top Five, option selection and Paper Bot are PENDING. **No new APK or version bump.** Current installed user version is still 2.3.126. Do not trigger final 127-E signed APK before the required functional gates; CI success is not device success.
- **Journal detail:** See latest append-only `docs/BOT_KING_WORK_LOG.md` entries for each patch, failed intermediate CI, successful run, production nonchanges and next tests. Treat this checkpoint as superseding older “127 audit only” status, without removing history.


## 2026-11-16 — Current status: 831-test index Login Recovery PASS

- Batch 127-B source fixes are now at tested SHA `7caac968c18437229a2d6384e99b1d9708fce6dc` ([Offline Regression CI 43786961360](https://github.com/vaishnavi596/volume-king/actions/runs/43786961360), **831 tests PASS**, verified log).
- Closed-market index recovery no longer treats saved historical NIFTY/BANKNIFTY/SENSEX prices as proof of a new login's complete 3/3. A single bounded retry is allowed only after current-generation PARTIAL/FAILED/COOLDOWN, never concurrently with LOADING or after 3/3 LOADED. All index/equity Dhan quotes remain exchange-time unverified.
- The durable full audit history—including intermediate failures and fixed tests—remains append-only at `docs/BOT_KING_WORK_LOG.md`; do not revert the newer index gate to a cached-price condition.
- **Required live acceptance:** run the committed, credential-safe `scripts/check_127_oracle_readonly.py` from an authorized operator environment, then inspect actual Oracle 51/3 + selected extra quotes and RELIANCE/HDFCBANK option listed expiry/chain. Current chat has no Oracle shell, so this has **not been done**. No build v2.3.127, signed APK, device acceptance or Oracle production modification; source CI PASS is not a mobile/market-data PASS.


## 2026-11-16 — 127-B persistent Watchlist snapshot recovery: 836-test PASS

- Root cause candidate identified from source: Oracle's `BOTKING_226_INGEST_ENABLED` defaults to off, while the app previously read only `/v2/snapshot`; without active cache collection the saved watchlist quotes would not advance even though the UI timer kept polling.
- Implemented a **read-only, fixed 51-equity Dhan direct batch fallback**, only after missing/stale cached Oracle snapshot, using preexisting `/dhan/ltp-batch` and at most one direct attempt per 180s per authenticated app session. Strict full-universe quote/unavailable contract; last-valid quotes are retained; no exchange-live claims, no per-symbol fanout, no live orders. Applied to Login and scheduled/Watchlist refresh.
- Source/test commits: `d38599f8`, `6c4625f5`, `f45d0f92`, source-string test updates `21ecf5e9`, `6b3af492`. Latest [offline GitHub CI run 43789687353](https://github.com/vaishnavi596/volume-king/actions/runs/43789687353): **836/836 PASS**, actual job log checked at SHA `6b3af492`.
- **Not production-proven:** Oracle runtime ingest flag and authenticated `/dhan/ltp-batch` entitlement were not checked. No production server change, Oracle read-only probe run, app versionCode/versionName bump, signed APK or mobile acceptance. Continue authorized production metadata smoke, then release version 2.3.127 test APK and explicitly confirm fresh login prices, 180s refresh, 3 indices, selected equities, stock option chains and Super Five without fabricated 5/5 signals.


## 2026-11-16 — S2D Server ↔ Dhan port/key/rate-limit repair checkpoint

- User requested first a full Server-to-Dhan rule reconciliation rather than another premature APK. The existing Android 127-B equity direct fallback/option work remains in branch; **do not replace or deploy** the customized Oracle server without timestamped backup and runtime comparison.
- Official Dhan v2 docs: `api.dhan.co/v2/marketfeed/ltp` uses `access-token` plus `client-id`, up to 1000 instruments per request, 1 quote request/sec; 24h access tokens, separate paid Data API entitlement, 3s option pacing. Distinct `X-BotKing-Key` is only BOT KING server pairing. Nginx external HTTPS443 ↔ Uvicorn loopback `127.0.0.1:8000` one worker; Oracle outbound Dhan data and OAuth both HTTPS443.
- Source fixes: `backend/dhan_feed.py` shared cross-instance 1.05s quote lock (commit `772c38ef`), no redirects/proxy forwarding for market-data headers (`e79f2669`), OAuth consent/key headers never follow redirects (`c61ab240`), corrected source-only operator script recognizing protected OAuth session or legacy token (`25cab964`, `16c88a58`), port 8000 loopback and no-key outbound Dhan data `api.dhan.co`/OAuth `auth.dhan.co` TLS443 checks (`6553ca83`, `cbca474e`), and guarded source regressions including one-worker requirement (`be10b4da`, `527ab932`).
- Latest proven CI source checkpoint `5a4f73b5`: [run 43792643011](https://github.com/vaishnavi596/volume-king/actions/runs/43792643011) **846 tests PASS**; full final `527ab932` run [43792941657](https://github.com/vaishnavi596/volume-king/actions/runs/43792941657) initially pending. Follow `docs/BOT_KING_WORK_LOG.md` for individual evidence/failed runs.
- **Cannot assert actual deployed connection rules are all enabled.** Production's real systemd User/EnvFile, token file vs OAuth session path and permissions, inbound public 443/firewall/TLS, outbound HTTPS, Dhan `/v2/profile` Data API subscription and 24h token validity, 51 stock+three indices+option chain live responses remain untested because there is no authorized Oracle SSH/credential access. A public host check from this environment could not resolve the DuckDNS host, which is **not proof the owner's Oracle is down**. No production edits, restart, Dhan OAuth rotation, order enablement, APK/version bump. Live orders OFF.


## 2026-11-16 — LATEST journal reconciliation and four-pipeline refresh design (SOURCE/PLAN, not deployed)

- **READ FIRST:** `docs/BOT_KING_EVIDENCE_AND_COMMAND_RUNBOOK_20261116.md` (new minimal-command evidence ledger; GitHub source commit `91eb6536`) alongside `docs/BOT_KING_WORK_LOG.md`, then `docs/BOT_KING_REFRESH_DEMAND_INVENTORY_20261116.md` (20 refresh consumers; source `af25d0c2`). Older handoff entries above are historical snapshots, **not the latest APK or production status**. Do NOT rerun proven nginx/listener/TLS/staged fake-quote tests just for new-chat orientation.
- **LATEST VERSION STATUS:** `pyproject.toml` source release version `2.3.128` from commit `48182f1b`; user reports the v2.3.128 GitHub Build **FAILED**, exact Actions run/job/step not yet inspected. No signed 2.3.128 APK, no device PASS. Last independently logged signed Build PASS is v2.3.127 #642 / run `43805532600` / 862 tests; v2.3.127 real user mobile screenshots FAIL (stale Oracle snapshot, seven issues, missing candles/filter votes). `src/main.py` 2.3.128 patch `70defe99` preserves shared 5m history and Super Five HIST; test source `2bb5fb2c`, no newly confirmed offline PASS.
- **FOUR LOGICAL PIPELINES user-approved for coordination (NOT IMPLEMENTED):** (1) equity+index quote snapshot; (2) 54 completed candles / Scanner / Super Five; (3) options CE/PE/OI/PCR/max pain + future independently verified derivatives; (4) News RSS + cached assessment/health. One Oracle-owned coordinator, global budget/cooldown, per-source revision, one shared cache, no extra request fanout. Four channels do NOT imply every channel firing concurrently, nor four direct Dhan requests. Dhan-only read-only orders OFF.
- **CURRENT vs TARGET:** App still: stock/index/option min 60s, Oracle assessment 180s, index candles 180s, 54-candle sequential scan then 180s rest, Super Five local 10s, Scanner local 2s, Watchlist mounted cells local 2s, News TTL 600s. Conditional tested targets: Oracle index 10–15s, equity quote 15–30s, selected option chain 30s, derived 2–5s local, completed 5m bars at candle close. Faster intervals **NOT DEPLOYED**; require Oracle production 429/latency/freshness verification. Market weekday 09:10–15:45 auto, 09:15–15:30 exchange-live eligibility; global outside-hours manual button requested but not implemented.
- **Oracle 1.05s quote gate:** staged module original SHA256 `7a8db92e...beb75` and proposed `beccda30...c33c` full in runbook; owner fake-quote test 1.051s, 429 cooldown, 0 network requests, dry-run PASS and production UNCHANGED. Quote-gate actual Oracle production deployment NOT PROVEN; do not assume applied or replace customized server files. Earlier Oracle 443/Nginx/8000/TLS health validated; see exact one-time command outputs in runbook.
- **NEXT MINIMUM ACTION:** First retrieve failed v2.3.128 Build job log, narrow fix and CI, then read-only verify stale snapshot collector and index HTTP stage (with no keys in output). Implement four-channel coordinator in bounded tested batches; advance signed versionCode/versionName only after tests; device acceptance separate. After every discussion/patch/command/test/deploy append dated evidence-backed journal entry, report PASS/FAIL/PENDING distinctly. Update root handoff after substantial status changes, never silently rewrite old history.


## 2026-11-16 — MANDATORY 7–8 latest GitHub Actions error-audit preflight

- **Owner's permanent workflow rule:** BEFORE each new batch/source patch/APK release read the **latest 7–8 Actions runs** on the same working branch, including Offline Regression and Build APK; inspect each failed step and actual job log, group repeating assertions into root causes, correct previous red tests/code before proceeding. Persist the run/job IDs, tested count, fail count, exact issue, repair commit, and PASS/FAIL/PENDING state in `docs/BOT_KING_WORK_LOG.md`. Group safe Oracle commands 2–4 together, track actual outputs, and never repeat already-proven server commands without reason.
- **FIRST reference:** `docs/BOT_KING_CI_EIGHT_RUN_PREFLIGHT_20261116.md` (commit `15006de5`, later expanded `69310d5a`), contains run/job failures #1536–#1541, build #643, exact assertion names, source/test patches and current status #1542–#1545. Old tests expected `dhan_feed.connected`, direct `quotes.get` and hardcoded local 10s; corrected HIST shared-cache/2s behavior remains offline-only and needs latest full CI.
- **Current source test-repair sequence:** `51321c92` joint bootstrap, `c08b7791` mobile regressions, `5ca1e8f0` watch incremental. GitHub #1541 failed with four old assertions; #1542–#1545 in progress on first check. **NO PASS** or signed APK inferred. No Oracle change, credentials or order operations. Don't bump version until current post-repair full CI PASS.


## 2026-11-16 — Latest CI/release and Oracle parity checkpoint

- **CI green:** Offline #1549 [43815714273](https://github.com/vaishnavi596/volume-king/actions/runs/43815714273), job `133127168728`, commit `0ab3e3f4`: **893/893 PASS** (543.626s). #1546–#1548 failed the same single obsolete test literal; fixed in `0ab3e3f4`. Use last-eight CI rule before next patch. Detailed result in `docs/BOT_KING_WORK_LOG.md` entry `APP↔ORACLE-03`.
- **Build green on OLDER head:** APK Build #644 [43814744656](https://github.com/vaishnavi596/volume-king/actions/runs/43814744656), head `52acae7b`: signed APK `com.botking.bot_king`, `2.3.129` versionCode `74401`, artifact `14202710472`. This APK **does NOT include later Oracle readiness/server contract patches** and has NO mobile PASS. No 2.3.130 release initiated.
- **Backend APP↔Oracle source:** seven core route pairs checked; new protected `/v2/server-readiness` source `f3163d4c`, regression `b4e3f9bc`, test correction `0ab3e3f4` CI PASS. App also calls `/v2/assessment/{symbol}` not present in repository `backend/server.py` source. Actual customized production server may differ. Snapshot ingester opt-in default disabled and 60s minimum in source; actual Oracle deployment/env/token status **NOT inspected**. Do NOT infer live app-server parity from CI; require sanitized collector enabled/age/count, protected route & index smokes, backup and staged comparison before server restart. Four-lane source policy is NOT Oracle deployed. Broker orders OFF.


## 2026-11-16 — APP↔ORACLE-06 grouped live readiness probe handoff
- **Source CI:** #1552 [43818041629](https://github.com/vaishnavi596/volume-king/actions/runs/43818041629) at `7a8db8ac`, exact job `133134482033`, **898/898 PASS**. Earlier #1551 **894/894 PASS**, #1549 **893/893 PASS**.
- **New grouped Oracle read-only probes:** GitHub scripts `scripts/audit_oracle_app_routes_readonly.py` (syntax/9 protected route decorators + SHA256; source only) and `scripts/audit_oracle_collector_runtime_readonly.py` (3 localhost GET-only checks: /health, authenticated /v2/server-readiness and /v2/snapshot, aggregate collector enabled/status/interval/age/quote count; no Dhan requests). Operator must securely provide `BOTKING_AUDIT_PAIRING_KEY` on Oracle host, never paste secret into chat/GitHub. Run both scripts after provisioning their code, then append actual sanitized outputs; **NONE run on Oracle yet**.
- **New tests:** `tests/test_oracle_collector_runtime_readonly.py` commit `573b04af`, #1553 [43819619493](https://github.com/vaishnavi596/volume-king/actions/runs/43819619493) was in_progress when last checked. SOURCE ONLY, no Oracle stage or deploy.
- **Why this gate:** Current GitHub backend source collector defaults OFF and min60s, while App expects a recent /v2/snapshot. Actual production flag/version and real 9-route parity are unverified. Do not increase quote rate, enable collector, replace customized Oracle server.py, or sign a 'fully fixed' APK on guesswork. Historical v2.3.129 signed #644 is still a pre-server-patch candidate, not mobile acceptance. Read-only, no real orders. Full details and exact result journal in `docs/BOT_KING_WORK_LOG.md`.


## 2026-11-16 — REFRESH-4P-03 handoff: first single-flight module, source-only
- Latest completed baseline #1553 [43819619493](https://github.com/vaishnavi596/volume-king/actions/runs/43819619493) at `573b04af`: **902/902 PASS**. The last-eight rule continues to apply.
- New `src/refresh_coordinator.py` commit `916835a4`: four logical read-only lanes, same-key single-flight, bounded TTL/cache, failure-not-cached. New `tests/test_shared_lane_refresh_coordinator.py` commit `d5062e7a` adds fake-provider concurrency/cooldown/cache tests; #1554/#1555 **in_progress** when read. Do not assert latest CI PASS until current-HEAD #1555 exact result.
- Crucial: this is a **standalone prototype**, NOT integrated into `src/main.py`, `src/server_feed.py` or deployed Oracle. App network refresh intervals and Oracle Dhan request volume are NOT yet reduced. No release or mobile success inferred.
- Keep next batch focused: finish red CI backlog, then integrate only one proven cache consumer, audit actual Oracle deployed collector/routes/age with the two read-only scripts and safe pairing key, only then optimize rate. Production backup before any server edit; live orders OFF. Canonical exact entry in `docs/BOT_KING_WORK_LOG.md`.


## 2026-11-16 — REFRESH-4P-04: first real bounded client coordination, awaiting full CI
- Latest prior-green #1554 [43820879016](https://github.com/vaishnavi596/volume-king/actions/runs/43820879016) = 902/902 PASS; #1555 [43820945746](https://github.com/vaishnavi596/volume-king/actions/runs/43820945746) = 907/907 PASS. Last-eight Actions audit performed before edits.
- App source [a0adc6e2](https://github.com/vaishnavi596/volume-king/commit/a0adc6e295a2abe06a0c250548ca0faeb71a1405) integrates `LaneCoordinator` **only** into Dhan client `server_readiness()`, validated 10s read-only cache, no unsafe payload caching, reset on disconnect. Offline integration tests [1e403599](https://github.com/vaishnavi596/volume-king/commit/1e403599b9a573e43ba81bbda5c024fdf3234102). CI #1556 [43822238523](https://github.com/vaishnavi596/volume-king/actions/runs/43822238523) and #1557 [43822272318](https://github.com/vaishnavi596/volume-king/actions/runs/43822272318) **in_progress at initial check**; no green claim yet for newest HEAD.
- **No additional market data acceleration:** Oracle app/source Quote 60s, Options 60s, server Collector default disabled/min60s remain unchanged. New readiness cache is a limited real application of single-flight, not 4 complete lanes or production deployment.
- **Next:** current-HEAD CI logs, then Oracle only read-only 2-script grouped route+collector operator audit; compare customized deployed server.py and safe env/age/count, do not repeat previous nginx/TLS checks; stage backup/rollback before any Server refresh change. v2.3.129 Build #644 signed older code only, not installed proof. Production not modified, orders OFF. Full entry in Work Log.


## 2026-11-16 — REFRESH-4P-05 latest CI regression triage
- **#1556** [43822238523](https://github.com/vaishnavi596/volume-king/actions/runs/43822238523) ran 907, FAILED(errors=1); **#1557** [43822272318](https://github.com/vaishnavi596/volume-king/actions/runs/43822272318) ran 912, FAILED(errors=1). Exact same `test_b3_shared_assessment_readonly.test_readiness_execution_locked` error: legacy test mocked `_call` on disconnected `ServerDhanReadOnly()`, but new client correctly refuses disconnected readiness before dispatch.
- **Source runtime safety preserved.** Test-only fix [58604f47](https://github.com/vaishnavi596/volume-king/commit/58604f470ae6ca5bdb0d162e6904c180a4e4d3b9) makes disconnected check explicit, sets unit-test-only connection before valid mock, invalidates 10s readiness cache between bad-response checks. GitHub #1558 [43822768858](https://github.com/vaishnavi596/volume-king/actions/runs/43822768858) **in_progress** on first check; do not call PASS until full job complete.
- Oracle Production **not inspected/deployed**. Prepared route-AST and GET-only collector probes at `scripts/audit_oracle_app_routes_readonly.py` and `scripts/audit_oracle_collector_runtime_readonly.py`, use on Oracle only with authorized secure key injection and no secrets in reports. Collector enabled/age/routes remain unverified. Read-only Dhan API, no live orders. Signed v2.3.129 #644 older source.


## 2026-11-16 — REFRESH-4P-06 equity-snapshot micro-coalescing and CI checkpoint
- Previous exact CI #1558 [43822768858](https://github.com/vaishnavi596/volume-king/actions/runs/43822768858), job `133149427894`, **912/912 PASS** after test-only `58604f47`. Old #1556/#1557 errors are fixed at this checkpoint.
- App `src/server_feed.py` [089b11e5](https://github.com/vaishnavi596/volume-king/commit/089b11e5b7173da4eeef42295feea85d0a832111) coalesces **fully validated** GET `/v2/snapshot` results using existing `LaneCoordinator` for **2 seconds** during `equity_quotes_with_bootstrap`. It does not change 180s Dhan equity fallback, index/chain/candle provider pacing, signal eligibility or collector config. Disconnect resets cache. Test module `tests/test_dhan_equity_snapshot_singleflight.py` [12b12e0b](https://github.com/vaishnavi596/volume-king/commit/12b12e0bf2a489467225126591750ac4490996c6) covers copy/TTL/bad snapshot/reconnect/source safety.
- Latest post-source #1559 [43824672392](https://github.com/vaishnavi596/volume-king/actions/runs/43824672392), job `133155522489`, and post-test #1560 [43824712559](https://github.com/vaishnavi596/volume-king/actions/runs/43824712559), job `133155657708`, were **in_progress** when inspected; **no CI PASS** for this new app code yet. New Journal entry `REFRESH-4P-06` at `docs/BOT_KING_WORK_LOG.md`.
- Oracle Production is NOT modified or verified; backend source default collector disabled/min60s; core Android server contract source routes present only in repository. Operator source and GET-only collector audit scripts await secure Oracle execution, no credentials printed. Older signed APK 2.3.129 #644 excludes new source. Next: first inspect #1560 errors and clear if any, then live Oracle read-only audit before real upstream speed changes. No live orders.


## 2026-11-16 — REFRESH-4P-07 Oracle snapshot age-boundary checkpoint
- Previous #1560 [43824712559](https://github.com/vaishnavi596/volume-king/actions/runs/43824712559) **916/916 PASS**, #1559 **912/912 PASS**; past #1556/#1557 red readiness tests are fixed. Current batch changed source in `LaneCoordinator` [81c55e87](https://github.com/vaishnavi596/volume-king/commit/81c55e87e07560e6c00766b82044082c105042a3) and `src/server_feed.py` [02feb6c7](https://github.com/vaishnavi596/volume-king/commit/02feb6c74fbf86d4a3d220e7419ff522f29cc453) to reject locally cached Oracle equity snapshot reuse if its original `snapshot_age_seconds` plus elapsed monotonic time exceeds 120s. Existing 2s TTL and full validation remain. Tests [79a0b8f2](https://github.com/vaishnavi596/volume-king/commit/79a0b8f214e2a3bdd041533c05fa1fcb1896cfb1) cover near-expiry and missing source age.
- #1561/#1562/#1563 were all **in_progress** at first status inspection, **new source NOT CI-proven** yet. Check newest #1563 run [43825259848](https://github.com/vaishnavi596/volume-king/actions/runs/43825259848) exact job log, repair if red, then note full result in Work Log. No newly signed APK or deployed Oracle source.
- Oracle production still lacks verified collector enabled flag/current snapshot age and 9-route parity; use only grouped read-only AST + GET-only scripts with operator-secure pairing key, do not blindly edit/restart. Upstream quote cadence, index, derivatives, historical Dhan 429 limits unchanged, broker orders OFF.


## 2026-11-16 — urgent v2.3.130 live-market test candidate (after 4P-07)
- User seeks installing a new signed APK while market remains open until about 15:15 IST. Preflight examined latest-eight Actions. #1563 [43825259848](https://github.com/vaishnavi596/volume-king/actions/runs/43825259848) **918 tests / 2 errors**, same Python nested `math` NameError due to later local import in `equity_quotes_with_bootstrap`. Fixed source at `24c03cb9` by binding `import math` before closure; regression `39b34182`. #1564 and #1565 were in_progress at the initial check; no green claim.
- Version bumped to **2.3.130** on `pyproject.toml` commit `26455d17`, auto-triggering Signed Build APK **#645** [43825726713](https://github.com/vaishnavi596/volume-king/actions/runs/43825726713), initial state `in_progress`. This APK is candidate only; inspect completed job for offline-suite PASS and actual Android package/versionCode/pinned signer/artifact BEFORE giving install instructions. Do not invent artifact URL/ID, do not promise market-hours completion.
- This candidate bundles source changes after v2.3.129: Dhan shared 5m HIST continuity, Super Five 2s local-only recheck, four-lane policy, Oracle route source contracts, readiness 10s cache and validated equity snapshot 2s local coalescing + age <=120s. **Actual Oracle Production has not been updated or audited** and could still lack readiness/assessment routes/ingester. App-only changes do not increase Dhan upstream frequency, solve unknown Oracle collector status or prove phone live quote/candle. Read-only orders OFF, no Yahoo fallback. Journal detail: `docs/BOT_KING_WORK_LOG.md` entry `LIVE MARKET CANDIDATE 2.3.130`.


## 2026-11-16 — OWNER RELEASE RULE (permanent): AUDIT FIRST, APK LAST
- **No rushing to APK for market-hours opportunity.** Before any *future* BOT KING app build, consolidate all issues from app, GitHub backend, customized running Oracle and prior user device reports; fix grouped related changes, prove Oracle live route/schema/collector source and safe 429 pacing, close latest-eight CI and full offline tests on intended release SHA, then only advance versionName+versionCode and create Signed APK. Inspect phone result separately. Rule is codified at `docs/BOT_KING_RELEASE_GATE_POLICY.md` commit `d0bc841a`; all batch outcomes must go in `docs/BOT_KING_WORK_LOG.md`. This applies to new chats. The document itself does not programmatically block the existing workflow; don't assume CI enforces these production checks.
- Already-triggered **v2.3.130 Build #645** [43825726713](https://github.com/vaishnavi596/volume-king/actions/runs/43825726713) is allowed to complete as **DIAGNOSTIC CANDIDATE ONLY**, do not cancel, promote or trigger another rushed build. At last read #645 in_progress; #1565 green and #1564 green after `math` closure repair, Oracle production unknown. Check artifact/status later.
- **Next work, not another APK:** operator-run grouped read-only actual deployed-route + collector audit from `scripts/audit_oracle_app_routes_readonly.py` and `scripts/audit_oracle_collector_runtime_readonly.py` on Oracle. No credentials in logs; authenticated GET-only status if secure local pairing-key injection available. Record deployed source SHA, actual nine routes, collector enabled/age/count; compare to GitHub backend and make only targeted backup-first server changes. Never conflate API-source presence, Dhan authenticated status, and live collection speed. No new Dhan/order fanout; live orders OFF. Source collector default OFF/min60s has NOT been proven live setting.


## 2026-11-17 — CURRENT OWNER RULE: LAST THREE RELEVANT CHANGED FILES
- The newest instruction **supersedes** historical ten-/fifteen-file precheck rules: before a GitHub patch, commit or test-related change, examine the **previous three relevant changed files** and their CI/test outcomes. Inspect additional direct dependencies or failure causes when necessary; do not miss a known regression because it lies outside three. Confirm exact-HEAD full CI before APK.
- Canonical rule and server-first shortlist recorded in `docs/BOT_KING_WORK_LOG.md`, commit `71403129ec5e3f0fd835d417fe96e9c5757427dc`. Oracle production and app remain unchanged by this documentation update. Pending: HDFCBANK mapping-status 404, Option PCR/Max Pain + candle evidence into Assessment; News/Futures stay WAIT absent verified producer. No APK until remaining server/application gates pass.


## 2026-11-17 — PERMANENT OWNER RULE: CANONICAL JOURNAL / NO DUPLICATE FILES
- Mandatory **continuous journal**: record EVERY future work batch/chapter, GitHub code edit/add/delete, Oracle/Windows command result, audit/test/CI, failure, patch, server deployment and APK/mobile result in existing `docs/BOT_KING_WORK_LOG.md` (not only at chat end). Log actual outcomes and exact commit/run evidence with PASS/FAIL/PENDING; redact credentials. Latest rule commit: `6f4b34d53e836832b7e769516bc26d92c2339cea`.
- **Canonical file reuse / no duplicate GitHub files**: search/read existing matching-function files before creating one; update/add/delete within the existing canonical script/test/report/checklist/journal instead of generating a near-identical file. New file only for a truly distinct requirement with documented justification and regression/dependency checks; production backups/local staging are exempt. Keep history, append dated supersession rather than deleting audit evidence.
- Continue owner's **3 relevant prior changed files + CI precheck**, **संयुक्त टेस्ट + संयुक्त सुधार + एक अंतिम Full Regression**, Oracle backup/rollback and exact-head CI before signed APK. `ok` means continue. This HANDOFF is only a short rule pointer; all detailed reports belong in the Work Log.
