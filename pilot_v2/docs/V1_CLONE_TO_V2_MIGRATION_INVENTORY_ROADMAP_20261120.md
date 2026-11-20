# BOT KING — V1 Clone → V2 Integration Inventory, Dependency Plan and Acceptance Roadmap
Date: 2026-11-20 | Status: **SOURCE/RECORD REVIEW ONLY — NOT EXECUTED**
Owner control: Latest clear instruction wins. This document is a TASK PLAN, not permission to change the clone, server, secrets, or release app. Owner's phone acceptance is a mandatory gate.

## 0. Final implementation decision
- **Keep the full existing V1 clone as the sole V2 UI/functional shell**: six bottom tabs Home, Options, Settings, Scanner, Watchlist, Chart; original dark/gold appearance, card density, Dashboard/Super Five, Search, local Doctor, candle bars, Charts/WebView, PAPER safety, all original interactions. Do NOT transplant the existing V2 pilot's 3-tab `main.py` over the V1 shell.
- **Finish and owner-test clone-only defects before integrating V2**: Watchlist 3m Bullish/Bearish green/red bar and Super Five WAIT, plus startup, login, six screens, original Options/Chart/Scanner, screen navigation, and saved preferences. The recent clone patch is **not** verified by a real new APK/device outcome in the journal. Do not replace absent 3m candles with 5m or invent LIVE votes.
- Only after owner's acceptance: choose a separate permanent V2 package/version/signing identity, copy/apply the reviewed **V2 source modules/contracts** to an adapter layer inside the accepted V1 shell, then integrate secure Oracle transport and features in dependent batches. Do NOT bulk paste two main.py files or merge settings stores blindly.
- Preserve V1 production and its data. Oracle should be the Dhan token/secure shared transport, quota enforcement and session-auth authority, **not** owner of Watchlists, refresh, scanner filters or UI settings.
- Current exploratory clone intentionally retains original V1 Yahoo, Angel One and old server login: owner explicitly ordered **no removals before clone acceptance**. Their retirement is a **later distinct V2 migration decision/gate**, not work to be executed now. Until approved, don't enable extra broker credentials or orders in V2.
- Clone's temporary `2.3.131` is **not** V2 final version. The V2 pilot's `2.0.100`/package is **not** production identity. Final version, package and stable signer must be agreed and tested before final release.

## 1. Reviewed source baselines (no guesses about live operation)
| Basis | Git ref | Verified contents | Meaning |
|---|---|---|---|
| Original V1 | `fix/botking-joint-audit-70-15-20261115` | `src/main.py` 7,097 lines, full six-page shell, old Dhan/Angel/Yahoo paths, Watchlists, filters, paper logic; V1 `pyproject.toml` version 2.3.130 | Original preserved comparison baseline |
| Active V1 clone | `pilot/v1-untouched-clone-apk-20261120` | `src/main.py` 7,105 lines, SHA `40856f5677af06baafc4d6b22c4bbeacf7cfe2ad`; version 2.3.131; one two-issue Watchlist/Super Five patch `e6d5f07`; focused test `263038e`; APK workflow update `526f645` | **Modified clone, not byte-identical original**; phone acceptance still needed |
| Existing V2 pilot | `pilot/botking-v2-smart-gateway-20261118` | `pilot_v2/android_app/src/main.py` 1,565 lines, SHA `cbc1c3bb472811e208c02caa3d8d850e6f7388df` (three tabs), v2.0.100 offline app | Source contracts reusable, current UI **not** the release shell |
| V2 data/security work | same V2 ref | `pilot_v2/android_app/src/` policy/cache/Keystore modules and `pilot_v2/` isolated Oracle source, owner provisioning tools | Many offline source/CI gates, **not** proof live phone/Oracle E2E |
| V2 journal | `pilot_v2/docs/V2_MASTER_JOURNAL.md` | Combined offline CI #392: 645/645 PASS; V2 pilot APK #7 Build SUCCESS; owner phone showed Keystore unavailable and Oracle not connected; Oracle source stage Run 44554411187 had `activated=false` | Never call V2 LIVE, four phones, Keystore or Dhan evidence production PASS on those results |

Existing `pilot_v2/tools/one_click_migration_gate.py` is **pilot-specific**: checks `pilot_v2/android_app/src/main.py` and bans old V1 imports; its check cannot be applied unchanged to the V1-shell clone until adapter isolation and a new clone-specific manifest are specified.

## 2. Feature-by-feature migration inventory
Legend: **KEEP** = clone's original UI/function; **ADAPT** = use audited V2 module/interface through adapter; **GAP** = live/operator/device proof or implementation missing; **LATER** = after phone clone signoff; no feature receives PASS merely for source presence.

| ID | Feature / owner requirement | Clone current | Reviewed V2 source | Transfer strategy and expected gate |
|---|---|---|---|---|
| UI01 | V1 dark-gold header, six tabs, six page structures, fonts, compact cards | KEEP existing `src/main.py` | `v1_visual_style.py` is only partial presentation; V2 pilot has 3 tabs | Do not overwrite clone chrome; screenshot parity on phone |
| UI02 | Dashboard + three independent indices / analysis slots | KEEP | `dashboard_parity.py`, `local_analysis_slots.py` | Adapter for source-safe data only; preserve V1 selections; 1m index evidence gate |
| UI03 | Watchlist search, add/remove, 5 lists, global max 70 distinct stocks | KEEP; clone has `normalize_watchlists`, 70 cap | `app_state.py`, `watchlist_search.py`, `watchlist_parity.py` | Select ONE canonical preference/selection store; migration backup, dedup tests, no reinitialization |
| UI04 | Watchlist 3m candle green/red bar | CURRENT CLONE DEFECT; code patch is unverified | `candle_history.py`, `historical_three_minute_fallback.py`, `evidence_inbox.py` | First fix+phone test current clone; later V2 authenticated completed Dhan 1m→3m evidence adapter, HIST/WAIT gating |
| UI05 | Super Five ranked five signals + historical context | CURRENT CLONE WAIT defect; source patch historical label | `shared_filter_context.py`, `historical_shortlist`, `filter_evidence.py` | Never turn historical vote into actionable LIVE or suppress legitimate HIST; preserve ranking screen |
| UI06 | Scanner selection, scanner compact/native/TradingView charts | KEEP V1 | `scanner_state.py`, `legacy_technical_bridge.py`, `local_webview_chart.py` | Retain working V1 WebView with sandbox/security review, avoid V2 offline HTML replacing it; separately validate owner timeframe choices |
| UI07 | Chart candlesticks/line, 1m/5m etc, indicator controls | KEEP | `candle_option_views.py`, `chart_style.py`, `chart_window.py`, `chart_visibility.py` | Preserve mounted UI; validate phone WebView/Flutter rendering and completed OHLC |
| UI08 | Options, expiry, CE/PE, ATM, OI, PCR and max pain | KEEP presentation and PAPER screens | `option_evidence.py`, `option_filter_gate.py`, `app_evidence_batch.py` | Valid expiry/source/revisions; real Dhan entitlement and source observation required; no fabricated values |
| UI09 | V1 Help Doctor/error history, language and alerts UI | KEEP | `local_help_doctor.py`, `local_notices.py` | Use sanitized local V2 diagnoses without losing V1 help content; alert delivery must remain unavailable until proven |
| UI10 | PAPER-only trade planning, 5 slots, SL/Target, risk, ledger | KEEP (no broker orders) | `local_paper_slots.py`, `local_paper_ledger.py`, `paper_preview.py` | Diff behaviors; preserve user records via explicit safe migration, do not copy V2 planner if it strips V1 paper functionality |
| UI11 | Five analysis filters + blank sixth visual slot | V1 shows T/C/N/F/O evidence chips and blank 6 | V2 `filter_evidence.py` uses **five DIFFERENT named domain filters**: oi_support, oi_resistance, max_pain, pcr, candle_trend; 6th blank | **NON-TRIVIAL SCHEMA MISMATCH**: keep V1 visual evidence chips separate from V2 five decision-filter inputs; define evidence provenance/mapping and score semantics before implementation |
| DATA01 | Dhan only V2 provider, no Angel/Yahoo / old server-owned settings | Original clone intentionally has legacy imports/handlers | V2 `one_click_migration_gate.py` bans `ServerAngelFeed`, `get_yahoo`, and legacy transport imports | **LATER** after V1 clone signoff: isolate V1 presentation vs transport, explicitly remove/bypass old broker network, credential fields, old server URLs/saved prefs; preserve UX and phone data; owner confirms scope |
| DATA02 | App-owned refresh Smart Data and selection intent | V1 has older polling, shared batches, caching | `smart_data.py`, `refresh_intent.py`, `app_state.py` | Single demand owner in app; dynamic 0–70 equities, 3 indices independent; do not fire dual V1+V2 poll loops |
| DATA03 | 1m Dashboard/Super Five, 3m Watchlist, scanner timeframes | V1 scanner has its own selections; 3m local fallback | V2 `refresh_intent.py` 1m/3m; **`scanner_state.py` allows 1m,3m,5m,15m,30m**, not previously requested selectable 1m/2m/5m | **DISCREPANCY / OWNER DECISION** before changing scanner options. Never invent 2m provider source; demonstrate valid aggregation first |
| DATA04 | Authenticated quote lanes + last-good persistence | V1 `server_feed.py`/old cache | `feed_inbox.py`, `quote_view.py`, `secure_https_reader.py` | Translate payload schemas into original V1 card models; independent revision and source/timestamp checks; 429/cooldown |
| DATA05 | Validated 1m/3m/5m candles, atomic options/filter evidence | V1 derived 3m from 1m and 5m scan, missing price-vs-candle parity | `candle_history.py`, `evidence_inbox.py`, `app_evidence_batch.py`, `app_signed_evidence_delivery.py` | Source-stamped authenticated evidence only; per-screen/timeframe/expiry cache isolation, completed bar gate, atomic revert on invalid payload |
| DATA06 | News/futures/options lanes / last-three-move signal | V1 UI/chips, some partial integration | V2 lane source and tests described in journal, but producer coverage is incomplete | Audit exact per-lane provider origin, schema, freshness and last-3-moves policy; show WAIT/HIST if missing, never score blanks |
| SEC01 | V2 Master Login, 1 master + 3 delegates (4 devices) | V1 uses URL/Server Access Key login | `app_p256_login.py`, `app_device_reader_slot.py`, `app_keystore_login_binding.py` | Security adapter must replace legacy auth **later**, not transplant password fields or auto-enroll; real device+server auth proof |
| SEC02 | Android Keystore nonexportable P-256, public SPKI, challenge signatures | No original Android P256 path | `app_native_keystore.py`, `app_p256_public_key.py`, `app_p256_signature.py` | JNI/pyjnius packaging, nonexportable key, native ABI and actual phone sign verification. Pilot handset showed unavailable: **OPEN BLOCKER** |
| SEC03 | Master approve/revoke/delegate, scope, no cross-device leakage | Old client only | V2 server device sessions/provisioning, `provision_oracle_master.py`; `secure_https_reader.py` | Map actual policy to 1 master+3 delegates; current journal records earlier policy cap at **3 total**: explicit correction and concurrency tests required |
| SEC04 | Encrypted local backup / safe on-device preferences | V1 `PreferenceWriter`, backup JSON, old server keys | `local_settings_backup.py`, private backup source/tests in journal | Unified versioned conversion, no pairing/token export, transactional restore, rollback |
| SERVER01 | Oracle one shared Dhan→pipe→devices with TLS, read-only and revocation | V1 server pairing remains in clone | `pilot_v2/oracle_runtime_factory.py`, `oracle_secure_entrypoint.py`, `oracle_evidence_lane.py` | Keep private gateway distinct from V1 production, provider quota/shared cache only, no product settings server-authority |
| SERVER02 | Token expiry/renewal | V1 existing server Dhan flow | Journal has contradictory observations `oauth_consent` and `renewal_supported=false` vs owner expected auto-renew | **Verify with actual authorized Dhan policy/probe**; don't alter functioning V1 renewal, invent 24h auto-renew or expose token |
| SERVER03 | Real option expiry + completed 3m source over protected loopback | V1 backend endpoints reported | `oracle_dhan_expiry_transport.py`, `oracle_dhan_cached_candles.py`, opt-in Oracle evidence sources | Offline mock/contract work; runtime opt-ins default OFF; require live Dhan source, entitlement, 429 and TLS service approval |
| RELEASE01 | Independent upgradable V2 APK, user-controlled install | Clone separate test build workflow v2.3.131, outcome unverified | V2 pilot APK 2.0.100 #7 signed with **temporary non-upgrade-safe** signer | Define final separate package, versionCode/name and stable persistent signing key, verify artifact with aapt/apksigner and install side-by-side; preserve user data |

### Important conflicts to resolve at implementation gate — no silent interpretation
A. **V1 five evidence chips T/C/N/F/O vs V2 five decision filters** are not interchangeable. Show both where user expects them; sixth blank.
B. **Scanner requested 1m/2m/5m vs V2 source timeframes (1m/3m/5m/15m/30m)**. Source mismatch needs explicit owner selection and validated 2m source if desired.
C. **Four phones desired vs previously reported three-device enrollment cap**. Do not claim four-phone Master policy works until source policy and server actual auth agree.
D. **Legacy V1 ACS login vs V2 P256 Keystore Master Login**: keep ACS for clone acceptance; later choose safe migration to owner-approved Keystore; no silent credential reuse.
E. **Old V1 Yahoo/Angel and legacy server controls**: preserve through current clone approval; later removal only by explicit V2 migration authorization.
F. **Dhan token renewal** cannot be promised as an automatic renewal while actual policy remains disputed.
G. **V2 pilot UI three tabs vs V1 six tabs**: keep V1 shell; migrate modular logic only.
H. **Old source code non-live tests versus real market data and Flet phone execution**: avoid marking any device/live gate PASS from CI alone.

## 3. Work packages / dependency sequence / go-no-go
| Batch | Scope (review and fix together) | Concrete deliverables | Prerequisite / acceptance |
|---|---|---|---|
| **B0 — Clone closure** | Watchlist 3m bar + Super Five WAIT + all original screens/login/Chart/WebView/Options. Single combined fix if evidence warrants. | Clone-only error log, focused regression, verified Android APK metadata/signature, user handset PASS/FAIL checklist | No V2 module migration until **OWNER PHONE PASS**; no fake LIVE to force green/red |
| **B1 — Immutable baseline + diff manifest** | Freeze accepted clone commit, compare V1 source, list all V2 source files/protocol dependencies and hazardous legacy state | Saved exact SHAs, import graph, file-by-file ADOPT/WRAP/IGNORE list, rollback point; owner confirms naming/removal scope | B0 PASS, original V1 untouched |
| **B2 — App-owned storage/UI adapters** | Reuse existing six-tab V1 UI; integrate selected LocalWatchlists, SmartData, local Backup/Doctor/Notice, paper safety by dependency injection | One preference-store owner, migration converter, no duplicate controls/callbacks, 0/5/70 unique roster tests, config backup/restore | B1 file manifest; no direct Oracle/token persistence |
| **B3 — Trusted data/evidence bridge** | Remove duplicate old poll paths only when equivalent source proven; wire quote inbox/Oracle reader, complete candles 1m/3m/5m, options/expiry, filters, Super Five, scanner | Typed adapter V2→V1 view models, independent lanes/revision/timeframe/expiry, five filters + blank, 1m/3m charts, 429/cooldown tests, last-good/HIST | B2 stable; missing source WAIT; no broker orders |
| **B4 — Master/4-device security** | Keystore JNI real phone, owner public SPKI review, P256 challenge/login, delegates, scope, revoke, clear-on-signout | 1 Master + 3 authorized delegates, exact fingerprint, negative auth tests and independent phone keys; no raw private key or bearer leak | B3 read-only adapter; protected Oracle staging; owner approves actual enrollment |
| **B5 — Oracle secure activation** | Read-only Dhan server bridge, private owner enrollment, token policy check, TLS/auth and rollback; no V1 downtime | Preflight→private staging manifest→backup→separate systemd/TLS activation→real protected endpoint and Dhan source checks; V1 health before/after | B4 native auth proof and owner-authorized Oracle operation; defaults fail closed |
| **B6 — Joint regression and final V2 release** | One exact-SHA combined integration gate, 4-phone sessions, screens/timeframes, 0–70 symbols, paper-only protection, signing/version identity | Source test log, APK binary signer & package evidence, side-by-side installs, live read-only quote/3m/option/5-filter evidence, owner device acceptance | B0–B5 PASS; no claims of 100% bug-free guarantee |

**Effort minimization rule:** one coherent test/patch per dependent batch; reuse already proven source contract tests; never rerun identical PASS merely for narration. Diagnose failing exact file/CI, correct with one consolidated commit, update the journal. Exclude unrelated CI runs.

## 4. B0 owner phone-acceptance checklist
- [ ] V1 original app and cloned APK separately launch; original not uninstalled or overwritten.
- [ ] V1-style header, dark-gold palette and all six tab labels/screens present.
- [ ] Same authorized Server Access Key + permitted server endpoint can connect in **clone**, without copying private SSH keys into an app field.
- [ ] Watchlist each list/search/add/remove/scroll opens reliably; LTP and candle source labels distinguish price from OHLC.
- [ ] Verified completed 3m candle + eligible votes renders Bullish/Bearish green/red; missing data explicitly WAIT/HIST with reason, not an invented bar.
- [ ] Super Five uses supported candidate selection; historical results labeled NOT LIVE and live winners require independently verified provider/session freshness.
- [ ] Scanner choice/filter and Chart/WebView load; no blank screen/Android startup exception.
- [ ] Options/CE-PE/expiry UI and PAPER functions preserved, with trading execution disabled.
- [ ] Settings, local Help Doctor, version label, preference backup work without losing original app data.
- [ ] Record device build/run number, exact SHA, screen screenshots and PASS/FAIL before owner authorizes any V2 transfer.

## 5. External gates and what remains unproven
1. **Current clone APK**: Workflow exists; reviewed journal lacks verified latest successful artifact and post-fix real phone screenshot/diagnostic. Treat B0 OPEN.
2. **V2 pilot Keystore**: Device previously reported "Android Keystore unavailable · device not enrolled"; source JNI/classes exist, but real signing not accepted.
3. **Oracle source**: Verified staging manifests explicitly say `activated=false`, V1 healthy. Protected V2 service and authenticated live Dhan-to-phone delivery NOT accepted.
4. **Five active filters**: V2 app validator expects genuine Dhan source evidence; absence is WAIT. Do not turn context-only news/futures/PCR into a vote.
5. **4-device target**: Four-way live authorization and duplicate-control tests not demonstrated. 
6. **Token**: Broker policy and renewal are unresolved; never change or claim hands-free renewal based on assumption.

## 6. Explicit exclusions for THIS planning request
No source edits, code merges, APK/CI runs, Oracle SSH/deploy/restart, Dhan calls, credential entry, broker orders, package/version/signing changes, or destruction/overwriting of original V1. Deliverables are **this reviewed list, phased tasks, acceptance tests and V2 journal entry only**.

## 7. Source-to-plan traceability
- Clone: `src/main.py`, `pyproject.toml`, `.github/workflows/v1-exact-clone-apk.yml`, `tests/test_v1_clone_watch_superfive.py` at clone branch.
- V2 UI: `pilot_v2/android_app/src/main.py`, `pilot_v2/android_app/pyproject.toml`, `pilot_v2/pilot_identity.json`.
- V2 client: `app_state.py`, `smart_data.py`, `refresh_intent.py`, `feed_inbox.py`, `evidence_inbox.py`, `candle_history.py`, `filter_evidence.py`, `option_evidence.py`, `app_device_reader_slot.py`, `app_native_keystore.py`, `app_p256_login.py`, `app_keystore_login_binding.py`, `app_signed_evidence_delivery.py`, `local_settings_backup.py`, `local_help_doctor.py`, `scanner_state.py`, `v1_visual_style.py`.
- V2 backend contracts and rollout evidence: `pilot_v2/oracle_secure_entrypoint.py`, `oracle_runtime_factory.py`, `oracle_evidence_lane.py`, `oracle_dhan_expiry_transport.py`, `oracle_dhan_cached_candles.py`, `pilot_v2/tools/provision_oracle_master.py`, `pilot_v2/tools/one_click_migration_gate.py`, `pilot_v2/android_build_gate.py`, and the dated V2 Master Journal entries.
- V2 journal is historical evidence: a previously passing CI/source stage does not prove a new clone branch commit or future Android runtime.
