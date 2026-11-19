## VERIFIED CI #187–#191; ANDROID KEYSTORE SOURCE BOUNDARY HANDOFF — 2026-11-19
- Active V2-only GitHub branch `pilot/botking-v2-smart-gateway-20261118`; historical V1/old journals READ-ONLY. Latest exact executable [CI #191](https://github.com/vaishnavi596/volume-king/actions/runs/44466358494) at `1dcb348653a2065b6a30ed18d623c4342f030948`: **SUCCESS 413/413**, source security findings 0, UI source wiring 9/9. Prior #187 404/404, #188 407/407, #189 411/411, #190 413/413 all GREEN. Do not rerun historical passing runs.
- Real new source work: strict canonical P-256 ECDSA DER signer-output gate (reject bogus/non-minimal/out-of-range `r/s` before login POST), canonical P-256 public SPKI with actual curve-point validation and public-only export, `AndroidKeystoreLoginBinding` restricting sign operations to exact server challenge context + one named device + 32-byte nonce, signed-login→independently enrolled server verifier→`DeviceReaderSlot` integration including wrong-key denial, and owner-facing SHA-256 fingerprint of only the public DER.
- These source tests use synthetic keys and Fake HTTPS/TestClient. **NOT YET COMPLETE:** native Android Keystore API plugin, nonexportable private-key/hardware attestation on a real phone, approved Master/delegate public-key enrollment/possession on deployed Oracle, actual transport and Dhan observation provenance, Scanner live scheduling, rich WebView device acceptance and independently signed installed V2 APK. No real trading orders, no secrets, Yahoo/Angel fallback or Oracle production actions.
- Next execution gate: `V2_ANDROID_KEYSTORE_DEVICE_ACCEPTANCE.md`. First wire an independently reviewed native Keystore provider returning public SPKI and a sign callback without private export; then physically verify Master/Delegate enroll, revoke and expiry under pinned Android Flet; only after user-authorized preflight adapt read-only Oracle. The current source-only results are NOT Android production acceptance.

---

## 2026-11-19 VERIFIED CURRENT V2 RESUME — CI #186 401/401
- V2-only branch `pilot/botking-v2-smart-gateway-20261118`. Latest VERIFIED executable **b4b6eabd35493540658b7c4e15a8fd74c8a85a62**, [CI #186](https://github.com/vaishnavi596/volume-king/actions/runs/44464942720) SUCCESS **401/401 tests**, zero source security findings, UI source wiring 9/9. Prior #182 396/396; #183 398/398; #184 399/399; #185 400/400 all GREEN. Previous documentation status snapshots are historical.
- Master/Delegate V2 signed read-only source contract now covered end-to-end OFFLINE: P-256 master login (server independently verifies), Master-approved delegated key enrollment, delegated `quotes` scope with forbidden `indices`, revoke preventing further reads, session expiry 403 invalidation, cache last-good retention, no second network call when auth is revoked. App-owned single session holder rotates readers and prevents late/superseded sign-in from resurrecting a cleared session (generation guard). All signed keys in tests are ephemeral synthetic; no live Oracle or Android Keystore binding.
- Manual selected-only read-only refresh source gate is complete but **DORMANT** on real Android until non-exportable native Keystore signer, approved Oracle TLS origin and owner-provisioned public key are verified. No automatic live market polling, real Dhan proof, live five-filter options provenance, deployed V2 routes, signed V2 APK or actual phone acceptance. Do NOT mark app done or claim LIVE.
- NEXT REAL INTEGRATION DEPENDENCIES (NOT ALREADY IMPLEMENTED): (1) Android Keystore P-256 non-exportable key generation and signer callback compatible with `P256ChallengeVerifier.signed_message`; (2) independently authorized Master and Delegates enrollment + remote revoke; (3) real HTTPS Oracle gateway deployment preflight, official Dhan source/provenance and rate budget checks; (4) device-tested Android Flet 0.25.2 optional WebView/native fallback, chart/Scanner refresh; (5) separately approved signed V2 APK/versionCode/in-app version acceptance. Keep current guard: NO APK build or Oracle production changes until app-side review/owner-gated phase, live orders OFF, no Angel/Yahoo fallback, V1 and old journal READ-ONLY.
- Work rule: user's OK means continue to the NEXT CONCRETE safe V2 job. Always read latest V2 journal and exact SHA CI before source modification; batch coherent tests/code+notes; avoid rerunning already green CI.

---

## 2026-11-19 CURRENT RESUME — VERIFIED CI #184 AND NEXT APP-FIRST GATE
- Active repository `vaishnavi596/volume-king`; V2-only branch `pilot/botking-v2-smart-gateway-20261118`; old V1 sources and journals READ-ONLY.
- LAST verified executable code: **598daa1b3cae41a206b56ec9be57d1b15d164d66**, [CI #184](https://github.com/vaishnavi596/volume-king/actions/runs/44464399318) SUCCESS **399/399 offline Python tests**, security findings **0**, source UI wiring **9/9**. CI #182 was 396/396, CI #183 398/398. Intermediate errors are historical; do not rerun old green/failure SHAs.
- New app-only tested work since #173: in-memory read-only session 401/403 invalidation with no retry, sanitized Settings connection state, one-session-owner `DeviceReaderSlot`, P-256 challenge/login HTTPS client accepting ONLY external trusted signer callback, no arbitrary quote payload ingress, signed manual selected-only two-lane read-only request, joint offline P-256 auth→quotes/index cache→TTL expiry integration, coordinator stops after auth rejection without fake extra HTTP count. 429 remains cooldown, last-good retained. All are source/Mock HTTPS/TestClient results.
- **NOT COMPLETED:** Android Keystore real signer/public-key enrollment; connected Oracle TLS origin/provider entitlement, real Dhan feed, authenticated live candle/options/five-filter source, true Scanner market polling, actual Android/WebView on-phone validation, signed V2 APK. Native chart safe default; optional local WebView preview default OFF. No claim of verified LIVE market data, remote Master controls, device acceptance or shipping readiness.
- Next ACTION priority: app-side strict Keystore signer binding/provisioning contract and physical-device acceptance prerequisites, then *owner-authorized* integration preflight. No Oracle production changes, V1 changes, APK build, orders or secrets. Future coding session must read this current resume FIRST, then Master/Work latest entries and exact CI; `OK` means proceed to the next concrete job, explaining failures without stopping.

---

# BOT KING V2 — CURRENT CANONICAL STATUS & RESUME INDEX
**As of 2026-11-18 | Docs-only snapshot; supersedes earlier "current"/"pending" entries for CURRENT status only.** Historical entries remain unmodified in the append-only Master Journal and Work Log.

## 1. Exact checkpoint
| Field | Current verified state |
|---|---|
| Repository | `vaishnavi596/volume-king` |
| Active branch | `pilot/botking-v2-smart-gateway-20261118` |
| Scope of allowed writes | `pilot_v2/` only. V1 read-only |
| Last **verified executable** SHA | `eec4869aab3c734162199aabf83f6b10b1366061` |
| Last **verified executable** Actions | [V2 CI #96](https://github.com/vaishnavi596/volume-king/actions/runs/44426357518), run `44426357518`, **SUCCESS 274/274 Python offline tests**, no failing step |
| Pre-consolidation docs HEAD | `1cf6e0e15de12a5604ed10e80afb9586d9989c1a` (**docs-only**, after CI #86) |
| This documentation snapshot | Docs-only; the latest executable proof is #87, not this journal commit |
| Deployment/device/trading | **V2 not deployed; no V2 APK built/installed or phone acceptance; no real Dhan live data, Oracle production changes, token renewal or live orders** |

**Evidence hierarchy:** SOURCE COMMITTED ≠ CI PASS ≠ Android runtime/visual PASS ≠ authenticated Dhan LIVE verified. Pending at an earlier SHA can have a later verified PASS; use the newest exact-SHA evidence, preserving historical failures.

## 2. Actual app-first migration progress (not a full V1 copy)
| Category | Ported / wired in V2 | Still incomplete / not verified |
|---|---|---|
| V1 look-and-feel | Safe V1 dark/gold palette, compact index/Watchlist/health cards, header + bell/version, some readable typography, three bottom tabs | Exact V1 dashboard/screens, all fonts/padding, chart WebView and Android pixel/interaction acceptance |
| Dashboard indexes | NIFTY / BANKNIFTY / SENSEX independent 1m model and historical/cache-only labels | Real fresh prices, correct 1m signals, continuous data refresh |
| Watchlists | Five locally saved lists, globally ≤70 unique equities (indices separate), 3m row view, local group search, Chart button → 3m Scanner; invalid/removed roster guarded | Real authenticated quote/candle refresh, responsive full V1 controls/device check |
| Scanner & chart | V1 Scanner + chart indicator engines copied to active V2, historic 1m/3m/5m analyses, 15/35/70 local chart bar window, LineChart, native OHLC geometry, selected symbol/timeframe state, Help | V1 full rich chart controls/WebView parity, device rendering, verified LIVE data |
| Super Five | Explicit WAIT for live ranking, historical-only shortlist, safe candidate → 3m chart and Help | Actual verified five-engine live ranking / partial-refresh behavior |
| Options | Selected verified-expiry offline roster, CE/PE strict seven-strike cache, trusted listed spot→ATM±3 normalizer, invalid/replay last-good retention, Help | Actual authenticated Dhan chain, complete expiry/OI/PCR/max pain refresh, equity/options coverage, device check |
| Filters/analysis | Five evidence-gated slots plus sixth blank, HIST/WAIT guards; technical historical indicator summary separately labeled | Full V1 signal panels, truly sourced News/Futures/Options/OI/Candle inputs, bullish/bearish percentages and AI parity |
| Settings/Help Doctor | Device-owned Smart Data preferences, local topic Help, safe Error Doctor cause/next action, contextual Help icons | V1 complete functionality, actual data-only manual refresh/market loop, master authorization UI |
| FT1 login & FT2/FT3 infrastructure | Isolated mock/offline P-256/session/revocation, shared-cache/quote-budget contracts & rate-lane tests | Deployed trusted master + up to 3 delegated session enforcement, token/OAuth read-only gateway, live provider validation |
| Paper/alerts | Old V1 requirements inventoried, live orders intentionally OFF | Safe non-executing paper/alerts/screens migration and regressions |

**Six V1 staging Git blobs match source exactly:** `analysis_quality.py`, `candle_retention.py`, `chart_indicators.py`, `dhan_three_minute.py`, `five_engine.py`, `scanner_engine.py` in `pilot_v2/v1_clean_staging/`; only Chart Indicators & Scanner Engine are also present in active V2 `android_app/src/` at earlier audit. This does not prove other modules are wired into app. See [Migration Manifest](V2_V1_CLEAN_MIGRATION_MANIFEST.md), [Function Graph](V2_V1_FUNCTION_DEPENDENCY_MAP.md), [Source Parity Audit](V2_V1_SOURCE_PARITY_AUDIT_20261118.md).

## 3. CI trail / resolved errors
| CI | Source commit | Result | Meaning |
|---|---|---|---|
| #71 | `cc722add` | 231/231 PASS | Earlier listed ATM adapter baseline |
| #73–#77 | `d569cf2` through `b30bac2` | FAIL | **One** `OptionEvidenceError` NameError; later fixed, failures retained |
| [#78](https://github.com/vaishnavi596/volume-king/actions/runs/44362040001) | `d1f0560c` | 237/237 PASS | Missing exception import correction |
| [#79](https://github.com/vaishnavi596/volume-king/actions/runs/44362597344) | `431a93d0` | 238/238 PASS | Local Help Doctor UI |
| [#80](https://github.com/vaishnavi596/volume-king/actions/runs/44363192734) | `db9e36a6` | 239/239 PASS | V1 dark/gold Dashboard/Watchlist cards |
| [#81](https://github.com/vaishnavi596/volume-king/actions/runs/44363552011) | `eb83b3d5` | 240/240 PASS | Context Help routing |
| [#82](https://github.com/vaishnavi596/volume-king/actions/runs/44364272154) | `cc70f97f` | 241/241 PASS | Scanner/Options visual Help |
| [#83](https://github.com/vaishnavi596/volume-king/actions/runs/44364734475) | `51a8c574` | 243/244 FAIL | One stale Watchlist source-string assertion, code feature remains |
| [#84](https://github.com/vaishnavi596/volume-king/actions/runs/44365018806) | `09bc354e` | 244/244 PASS | Corrected assertion / Watchlist search |
| [#85](https://github.com/vaishnavi596/volume-king/actions/runs/44365732818) | `ad917cb5` | 245/245 PASS | Historical Super Five to chart |
| [#86](https://github.com/vaishnavi596/volume-king/actions/runs/44366294149) | `8739cb9a` | 246/246 PASS | Watchlist → Scanner 3m button |
| [#87](https://github.com/vaishnavi596/volume-king/actions/runs/44368036631) | `51da2bef` | 249/249 PASS | Local Scanner 15/35/70 bar history window |\n| [#88](https://github.com/vaishnavi596/volume-king/actions/runs/44370132223) | `c8d06b6a` | 253/253 PASS | Shared five-factor screen context |\n| [#89](https://github.com/vaishnavi596/volume-king/actions/runs/44370643743) | `ea4233d8` | **255/255 PASS** | Dashboard independent index → 1m Scanner |

## 4. OWNER rules (authoritative)
- V2 equals V1 **real screens, behaviors, engines** but no old server settings, Angel One, Yahoo, legacy credentials/auth/order paths. Copy only audited UI and local functions to V2; **do not import V1 `src/main.py`** (mixed providers) or old server modules.
- **App-first** product/design/state/filters and smart scheduling. Oracle integration/deploy **LAST** after app functional/CI and planned device build acceptance; server only owns authenticated read-only Dhan token/technical cache/rate-limit transport.
- **70 distinct selected equities total across five lists**, no duplicate; 3 independent indexes. Dhan demand proportional to selection (5 means fetch 5, not 70), shared cache/serialization. Market automatic polling only 09:10–15:45 IST; outside hours freeze except explicit *data-only* manual refresh. Watchlist 3m; index & default Scanner 1m; selected Scanner timeframe permitted 1m/3m/5m. Five actual filters, sixth intentionally empty and excluded from scoring.
- Offline unverified market inputs = **HIST or WAIT**, never fabricate live, bullish/bearish percentages, OI/news/futures votes or orders. Keep last good on incomplete response.
- Target **1 Master + up to 3 delegated devices** (4 total) per latest owner rule; some older prototype code/docs still assume max 3 **including Master**. **OPEN MISMATCH**, do not silently mark corrected or deploy.
- Old V1/production/Oracle/keys/APK unchanged without separate authorized approval; no live orders. New V2 package/version signing/install acceptance pending.
- User `ok` means continue doing real safe work, not just report. Before each V2 code change inspect previous actual commit/files and exact applicable CI; failed CI must be diagnosed/fixed before another unrelated patch. Combine 2–4 related files/tests and journal updates in one atomic commit, verify the same source SHA. Do not build APK early.
- Each live action records source SHA, changed files, test count, CI run/FAIL/PASS/PENDING, Dhan/Oracle/order/APK/device facts and next. The **Work Log & Master Journal preserve history**; do not overwrite failures or call a docs-only SHA an executable PASS.

## 5. Exact next batch (app-first)
1. **FT2 V1 parity inventory / actionable gap list:** read original V1 source *read-only* and current V2 Flet main. Group remaining visual/functional screens (Dashboard panels, actual Scanner chart controls, Super Five live gates, Options selected expiry/update, Paper non-executing, alerts, Settings, Help Doctor) by imports/callbacks, and mark `PORTED / WIRED / CI TESTED / DEVICE VERIFIED` separately. No old provider/system config.
2. **Next safe implementation:** pick coherent 2–4 V2-only UI/local function files + regression; preferably connect remaining selected-symbol chart navigation/option UI controls, then test exact SHA; avoid cosmetic-only pseudo parity.
3. **Then FT1/FT3 app integration:** master login/first bootstrap and Dhan-only read-only evidence/cache/smart refresh UI contracts. Offline tests cannot establish actual Dhan entitlements, expiry token, authenticated transport, 1–4 phones.
4. **Later FT4:** full exact-SHA regression, distinct V2 Android metadata/signing and real phone visual/functional acceptance; only then staged, backup-and-rollback Oracle production integration under explicit approval.

## 6. New chat resume / source of truth
**Read order:** (1) [this current status](V2_CURRENT_CANONICAL_STATUS_20261118.md), (2) [General Framework](V2_GENERAL_FRAMEWORK_RULES.md), (3) [Handoff](V2_HANDOFF.md), (4) [Live Status & Schedule](V2_LIVE_STATUS_AND_SCHEDULE.md), (5) latest actual branch HEAD/Actions, (6) Master Journal + Work Log only for needed history and failures. This snapshot is authoritative *as of the checkpoint above*, but must be checked against newer HEAD/CI each turn. Repo General records = these `pilot_v2/docs/` files; do not claim an actual GitHub Discussions → General post was created.


## V2-FT2-SCANNER-CHART-WINDOW-CI87-VERIFIED-20261118
- Exact [V2 Pilot CI #87](https://github.com/vaishnavi596/volume-king/actions/runs/44368036631), run `44368036631`, source SHA `51da2bef55e6b59d5ab47dffba7d513ed32a6e96`: **SUCCESS 249/249 Python offline tests OK**, no failing step.
- App source: `pilot_v2/android_app/src/main.py`, new `chart_window.py`; test `pilot_v2/tests/test_chart_window.py`. Scanner chart display selects 15/35/70 cached completed historical bars, 35 default; changing dropdown uses local window only, never refreshes quote/candle data, does not change timeframe or produce a LIVE claim.
- Safeguards: strict window choice type/range; completed history, invalid new data retains last-good; five filter+blank sixth, symbol/timeframe, 70 equities and 3 indices unchanged.
- Limit: source CI not Android Flet rendering or authenticated Dhan/Oracle provider integration. No V1, Oracle, Dhan API, orders, APK.
- NEXT: V1→V2 functional parity inventory and grouped local app control wiring, then exact code SHA CI; Oracle production last.


## V2-MIGRATION-SHARED-FIVE-CONTEXT-CI88-AND-INDEX-CHART-BATCH-20261118
- **Verified CI #88:** Run `44370132223` at source SHA `c8d06b6af35bf8e5d8f335c7455b50c2a55f0b26`, completed SUCCESS: **253/253 Python offline tests OK**, job SUCCESS. The shared source-gated five-filter context now feeds Dashboard 1m, Watchlist 3m and Scanner/Super Five historical coverage independently per symbol/timeframe; sixth blank, no synthetic percentage or LIVE.
- **New V2-only app batch:** Dashboard's three independent Index cards now have `1m Chart` buttons. `open_index_chart` accepts only NIFTY/BANKNIFTY/SENSEX and uses existing `scanner_state.choose` / local Scanner persistence; no server request, no legacy provider or auto refresh. Added `tests/test_index_chart_routing.py` for 1m selection, invalid symbol denial, actual UI callback and bottom navigation unchanged.
- **New batch CI:** PENDING until exact source commit SHA / GitHub Actions job log is checked. Offline tests do not constitute Android visual runtime or Dhan live verification.
- **Open migration blockers:** See `V2_REMAINING_FUNCTIONAL_GATES_20261118.md`; full V1 feature parity, actual five-source feed, Super Five scoring, News/Futures/Options, smart data manual/auto refresh, Master+3 delegated auth, nonexecuting Paper/alerts, Android build/phone tests and Oracle last remain open.
- **Boundary:** Only `pilot_v2/` code/docs; no V1 branch/files, old server settings, Angel One/Yahoo, Oracle production, Dhan calls/OAuth, orders or APK.


## V2-FT2-THREE-DASHBOARD-ANALYSIS-SLOTS-20261118
- **PRECHECK:** CI #88 run `44370132223` at source `c8d06b6af35bf8e5d8f335c7455b50c2a55f0b26` **253/253 SUCCESS** after shared five-factor source-view migration. CI #89 run `44370643743` at source `ea4233d8c0d2c27a015fb0ba76515bbba45e0ac9` **255/255 SUCCESS**, validating NIFTY/BANKNIFTY/SENSEX Dashboard 1m chart buttons. Last code SHA reviewed before patch.
- **Actual V1 parity:** Original V1 `src/main.py` `dashboard_index_analysis()` has three independent dropdown analysis slots. V2 now has isolated `android_app/src/local_analysis_slots.py` plus three visible Dashboard slots. Picks are independently validated against three indexes and up-to-70 currently selected equities, persist only to V2 client local storage, and show current shared quote/1m candle/five-factor WAIT/HIST context. Selected row can open existing 1m Scanner chart without new data calls.
- **Tests:** New `tests/test_dashboard_analysis_slots.py` exercises independent choices, local serialization, rejection of unauthorized/removed equities, fail-closed invalid save, stale selection reconciliation, 3 actual Flet slot controls and forbidden legacy provider paths. New exact-source CI **PENDING**, no Android UI/device evidence.
- **Limit:** Fully ported V1 Dashboard fonts/chart/alerts/Paper and true verified five-source signals remain incomplete; trusted Dhan transport, Smart Data refresh, Master+3 delegated login, V2 APK and Oracle integration have NOT been performed.
- **Write safety:** `pilot_v2/` only, no V1/Angel One/Yahoo/old server settings, no token/OAuth, live orders, Dhan calls, Oracle production or APK. After exact run verify CI and then move to next safe V1 functional parity dependency.


## V2-FT2-THREE-DASHBOARD-ANALYSIS-CI90-VERIFIED-20261118
- Exact [V2 Pilot CI #90](https://github.com/vaishnavi596/volume-king/actions/runs/44371437426), run `44371437426` at source commit `1bbf63cd45e0ef64c9021ffdf2b41ec948f3af81`: COMPLETED SUCCESS, `pilot-contract` job SUCCESS, **259/259 Python offline tests OK**, no failing step (1.315s). Previous CI #89 `ea4233d8` 255/255 PASS and #88 `c8d06b6a` 253/253 PASS.
- V1 three independent `dashboard_index_analysis` slots migrated to isolated V2 `local_analysis_slots.py` + real Flet Dashboard dropdowns. Validate selected equity/index against current Watchlists/INDEXES, keep source-gated 1m quote/candle/five-filter context, local device-only save and removed-symbol recovery, selected analysis → existing 1m Scanner chart. No V1 mixed provider module, server settings or data fetch.
- Unit tests `test_dashboard_analysis_slots.py` include independent selection, save fail-closed, removed symbol, illegal slot and Flet source UI control wiring. **Still NOT Android visual/interaction, exact V1 pixel/feature parity, real Dhan/Oracle transport or live trading proof.**
- Remaining gates maintained in `V2_REMAINING_FUNCTIONAL_GATES_20261118.md`: full V1 remaining panels, safe nonexecuting Paper/alerts, News/Futures/Options/AI evidence, Smart Data refreshing, Master + 3 delegates, device/Android package and Oracle LAST. No real Dhan/Oracle requests, OAuth, orders, APK or V1 mutation.


## V2-FT2-LOCAL-PREFERENCE-BACKUP-RESTORE-MIGRATION-20261118
- **PRECHECK:** Last prior executable commit `1bbf63cd45e0ef64c9021ffdf2b41ec948f3af81`, GitHub CI #90 `44371437426` **259/259 PASS**. Last HEAD `49b0745be0d329e45b0453d0121595e7c497fc6c` docs-only. Reviewed V1 Settings local backup/restore UI requirements and V2 Watchlists/Scanner/Smart Data/Analysis Slots saved schemas.
- **REAL V2 LOCAL SOURCE:** New `android_app/src/local_settings_backup.py` exports/validates a strict JSON allowlist of ONLY V2 local Watchlists, Scanner, Smart Data and Dashboard Analysis preferences, max 16,384 chars; rejects broker/provider/server/credential/extra fields and restores all schema sections only after complete parsing. V2 Settings includes Prepare/Copy-manually text, explicit confirmation, and Restore controls. Post-restore incompatible stale symbol caches removed; persistent save result accurately reported.
- **TEST:** New `tests/test_local_settings_backup.py` validates roundtrip, no secrets/provider/server settings, malformed injection/duplicate/removed symbols refusal, actual Flet button callbacks, three bottom tabs and no Angel/Yahoo call. Exact new executable CI **PENDING** until Actions result is inspected.
- **LIMITATIONS:** This is a local preference backup, not full V1 mixed settings backup; real Android clipboard/visual not tested, and saving to device can fail and be reported session-only. No export of broker token, Oracle URL, live order settings or trading position. Remaining original V1 screens/engines, real Dhan, paper-safe/alerts, Master+3 delegated, final Android APK and Oracle LAST are still open. Do not call migration complete.
- **SAFETY:** V2-only branch and files; NO V1, Oracle production, Dhan requests/OAuth, live orders, server settings, Angel One, Yahoo or APK.


## V2-CI91-LOCAL-BACKUP-SOURCE-ASSERTION-CORRECTION-20261118
- **REAL FAIL:** [V2 CI #91](https://github.com/vaishnavi596/volume-king/actions/runs/44372461992) source SHA `74ea3c107118da66fdccd480796db935353dedcd`, 263 tests, **262 PASS, 1 FAIL** in `test_local_settings_backup.LocalSettingsBackupTests.test_real_settings_wiring_and_three_bottom_tabs`: test asserted a single-line string `export_local_backup(state, scanner[0], smart[0], analysis_slots[0])`, but actual correct source splits function and arguments across two lines. No failure of the strict local backup import/round-trip/credential rejection tests.
- **FIX:** Update only the old brittle source-text assertion to independently verify function-call and exact argument sequence across line break; no change to app Backup/Restore semantics or security validation. All other source tests preserved; corrected source exact CI **PENDING** until Actions result verified. CI #91 remains historical FAILURE, do not claim PASS for it.
- **Boundaries:** V2-only test/journal; no old V1, Oracle production, Dhan provider, tokens, live orders or APK. NEXT inspect exact corrective CI and continue only after green.


## V2-FT2-LOCAL-PREFERENCE-RESTORE-CI92-VERIFIED-20261118
- Exact [V2 Pilot CI #92](https://github.com/vaishnavi596/volume-king/actions/runs/44372838093), run `44372838093` at corrective source SHA `2e35e6a4b6182acdab589360e28981e05aa856ae`: COMPLETED SUCCESS, pilot-contract job SUCCESS, **263/263 offline tests OK**. The former CI #91 at `74ea3c10` remains historical FAIL 262/263 due to brittle single-line source-string assertion; corrected exact call/arguments check in #92; app behavior unchanged.
- V2 Settings local-only backup/restore is now source+CI verified: strict Watchlists/Scanner/Smart Data/three Analysis Slots schema, no server/proxy/provider/token/trading settings, explicit confirmation before applying a completely parsed payload, stale removed cache pruning, clear save failure. This does NOT establish actual Android rendering or device persistence runtime.
- V2 migration remains PARTIAL: real Dhan/Oracle authenticated read-only transport, Smart Data polling, full V1 fonts/click paths/alerts/nonexecuting Paper, current Master+3 delegated login and News/Futures/Option/AI source-gated five-filter Super Five scoring are not end-to-end; APK and Oracle rollout require separate gates.
- Next source batch must inspect this exact CI #92 and last changed files before modification; preserve V1/read-only, no live orders and Oracle LAST.


## V2-FT2-V1-PURE-PAPER-RISK-ENGINE-MIGRATION-20261118
- **Owner goal:** Finish remaining safe V1 feature transfers without V1 server settings or execution paths. Previous executable `2e35e6a4b6182acdab589360e28981e05aa856ae`, CI #92 run `44372838093` SUCCESS 263/263; previous HEAD `1c45b793ddb71fa99addff2491d93a295e11944c` docs-only.
- **READ-ONLY V1 AUDIT:** `src/paper_engine.py` blob `ae046b0170ddc66829402978d5e21b34889814fc` imports only Python `math` and `datetime` and defines deterministic manual mark/risk calculations. No request, server, broker, order API or trade authorization. This exact original blob is safely copied to V2 `pilot_v2/android_app/src/paper_engine.py`, WITHOUT importing V1 main or paper UI/old credentials.
- **V2 SOURCE:** `paper_preview.py` wraps pure V1 `levels`/`risk_check` with positive finite manual inputs and quantity cap; displays PAPER ONLY stop, target and planned-risk result, never a trade/order. V2 Settings gains local BUY/SELL directional *calculation preview* (NOT an order action), entry, quantity, stop/target, paper capital/risk caps, button and safe error text. No live market price bound; manual figure only.
- **REGRESSION:** `test_paper_preview.py` positive BUY/SELL results, invalid/overrisk inputs, original pure V1 engine import security and actual Settings callback/no order calls. Exact new source CI PENDING until verified; device rendering/Paper bot full V1 parity NOT claimed.
- **Still open:** V1 full Paper Bots 1–5 ledger/alerts and their UI, complete V1 screens/fonts, genuine five-filter News/Futures/Options/Super Five, Smart Data polling, Master+3 delegates, real Dhan/Oracle transport and Android APK. No Oracle, Dhan, live orders or V1 edits.


## V2-FT2-PURE-PAPER-MANUAL-PREVIEW-CI93-VERIFIED-20261118
- Exact [V2 Pilot CI #93](https://github.com/vaishnavi596/volume-king/actions/runs/44373958095), run `44373958095`, executable source `29fd2645d3cc5783175fdf5bac33d81a51e24131`: **COMPLETED SUCCESS, 267/267 Python offline tests OK** (0.928s), job SUCCESS, no failing test.
- V1 pure `paper_engine.py` Git blob `ae046b0170ddc66829402978d5e21b34889814fc` copied unchanged into V2; safe manual-only `paper_preview.py` calls original deterministic levels/risk_check, no order/broker/network. V2 Settings paper side/manual entry/quantity/capital/risk inputs and `Calculate paper risk (no orders)` button display hypothetical stop/target/planned loss; NOT a trade or real broker fill.
- Prior V2 source CI #92 263/263 PASS (local-only preference backup/restore), #90 259/259 PASS (three Dashboard analysis slots), #89 255/255 PASS (independent index → Scanner), #88 253/253 PASS (shared five filters). Historical #91 FAIL is fixed by #92; do not erase original failure.
- **Still NOT full V1→V2 feature migration:** V1 five Paper Bot slots/ledger/protection simulation, alerts, full fonts/layout/rich chart, live source-based 5 factors (News/Futures/Options/OI/Candle), genuine Super Five, CE/PE/OI/PCR/max-pain real Dhan, 70-symbol smart refresh and four-device master auth, signed V2 Android and Oracle integration remain separate unclosed gates. No real Dhan market calls or production actions performed.
- **Future action:** Finish only further V2-safe app modules/function graph, exact-source CI, then Android visual acceptance, Oracle production last with explicit approval. No old V1/server settings, Angel/Yahoo, credentials or live orders.


## V2-FT2-FIVE-LOCAL-PAPER-PLANNING-SLOTS-20261119
- **Precheck:** Latest source CI #93 at `29fd2645d3cc5783175fdf5bac33d81a51e24131`, [run 44373958095](https://github.com/vaishnavi596/volume-king/actions/runs/44373958095), SUCCESS **267/267 offline tests**. Last HEAD `74bfabce2dc83fffb9b45204ed4bc6a37a23a89f` docs-only, reviewed. V1 `src/paper_bot_slots.py` Git blob `d7681c3e0614af8e0377baabebf876c2e319d8bc` contains local ledger but legacy migration and broker-like BUY/SELL event labels. Did NOT copy this module unchanged.
- **New source:** V2-only `local_paper_slots.py` implements FIVE independent `Bot 1..Bot 5` user-owned manual risk-plan slots, schema-validated and rejecting trade/order/credential/unknown fields. Stored data is purely `paper_preview.py` calculation of manual stop/target/planned risk, not paper positions or trade fills. V2 Settings has selected slot dropdown, 5 summaries, Save risk preview and Clear preview buttons; all local app storage, no server/broker access.
- **New test:** `test_local_paper_slots.py` checks independent slot isolation/roundtrip, invalid slot and foreign settings rejection, no broker calls, actual UI button callbacks, three bottom tabs; new exact-source CI PENDING until observed.
- **Safety/limitations:** NO V1 files or old server settings, Angel/Yahoo, Oracle/Dhan calls, token/OAuth, real/paper-order execution or APK. Five V1 full Paper Bot ledger/automation and alerts remain NOT MIGRATED; Android visual/runtime untested. Next exact GitHub Actions review and update canonical journals only on observed result.


## V2-FT2-FIVE-LOCAL-PAPER-PLANS-CI94-VERIFIED-20261119
- Exact [V2 Pilot CI #94](https://github.com/vaishnavi596/volume-king/actions/runs/44423433609), run `44423433609`, source SHA `27039f8dfb496f8355ef56f17f9a53efb84bfc8a`, **COMPLETED SUCCESS, 270/270 Python offline tests OK** (2.203s), job SUCCESS. Previous #93 267/267 PASS remains established.
- New `local_paper_slots.py` adds five isolated manual-paper **risk-plan** slots and strict local-state validation, explicit Settings UI controls for selection/preview save/clear, and `test_local_paper_slots.py` validates independence, bad storage/credentials/unknown fields, UI wiring and no provider/trade execution. This is NOT five simulated order bots or their fills/ledger.
- **Open acceptance:** Full V1 five Paper Bot journal/automated simulation remains unported. Other pending screens/alerts, real verified five filters/Options/News/Futures, smart data schedules, Master+3 secure devices, signed V2 APK/Android acceptance and Oracle/Dhan live integration last. Only `pilot_v2/` written, no V1/server/provider/secret changes, real orders or APK.
- Next: app-only alerts/diagnostic local display or safe manual Paper ledger audit, exact source regression first; no unrelated patch on failed CI.


## V2-FT2-PAPER-PREVIEW-STALE-INPUT-GUARD-20261119
- **Precheck:** Previous executable #94 run `44423433609`, source SHA `27039f8dfb496f8355ef56f17f9a53efb84bfc8a`, SUCCESS **270/270**. HEAD `57fe90eeeeaae8d07f5a0f5a5d04857060375d99` docs-only. During five local paper-planning slot review, identified risk: changing manual side/entry/quantity/stop/target/risk fields after calculation must not permit saving the old preview for new inputs.
- **FIX:** V2 Flet Settings now invalidates `paper_last_preview` on both side and any numeric paper input change, and Save remains fail-closed unless a newly calculated preview exists. UI local calculation only: no broker, no order, no network or V1 server settings.
- **TEST:** `test_local_paper_slots.py` now asserts stale-preview invalidation for both control callback categories and the save precondition. New exact CI PENDING; verify before claiming PASS.
- **SAFETY:** Only V2 code/tests/docs. No Oracle, Dhan requests, OAuth, V1 changes, APK or live order.


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
