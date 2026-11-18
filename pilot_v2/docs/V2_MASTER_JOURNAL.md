# BOT KING V2 — CANONICAL MASTER JOURNAL
**Owner lookup:** "बोट किंग इंप्रूव वर्जन का जर्नल देखो", "BOT KING IMPROVED V2 JOURNAL".

For current category status and next work order FIRST read [V2_LIVE_STATUS_AND_SCHEDULE.md](V2_LIVE_STATUS_AND_SCHEDULE.md). This is the **single authoritative V2 continuity ledger**, alongside `V2_HANDOFF.md` (short current orientation) and `V2_WORK_LOG.md` (append-only detailed commands/tests). Old BOT KING `docs/BOT_KING_WORK_LOG.md` is preserved and is not the current V2 work queue.

## Current status — 2026-11-18
| Field | State / evidence |
|---|---|
| Working branch | `pilot/botking-v2-smart-gateway-20261118` |
| New independent source root | `pilot_v2/` |
| Last verified V2 source commit | `d8fe238d95d9f9fbf51453005f7a82589d0c98ec` (last source CI #23) |
| Last V2 CI | **#23 SUCCESS**, run `44302676179`, exact SHA `d8fe238` |
| New V2 application version/package | Planned **2.0.100** / `com.botking.bot_king_v2`, metadata ONLY |
| V2 gateway | API prefix `/v2-pilot`, **feature flag OFF**, NOT served on Oracle |
| Master device feature | Offline durable sessions + P-256 key enrollment/rotation prototypes; dynamic current-key login binding NOT DONE |
| Current legacy / installed app | Preserve existing working app and server; no V2 cutover |
| Server / Dhan API / orders | **No production edits, market-data calls or trades** |
| APK / mobile | **No V2 APK, no device PASS** |

## Workstream tracker
| Item | Scope | Status | Gate to close |
|---|---|---|---|
| V2-001 | Separate branch/folder, reserved identity, demand/cache + master control pure domain contract | **CODE + CI PASS** | 577f07d / CI #1 |
| V2-002 | Verified 2-gateway auth: Dhan token lifecycle and revocable Android sessions; master proof | **PARTIAL — offline durable sessions/key rotation CI #16 PASS** | Dynamic current-key binding, native Keystore, secure owner bootstrap/recovery, Oracle OAuth evidence missing |
| V2-003 | Shared broker quote collector, WebSocket/REST, 1–3 devices, 0/5/51/70 demand, 3 indexes | **PARTIAL — offline shared cache and SQLite rate gate CI PASS** | Real authenticated broker collector, entitlement/transport, revision/API integration pending |
| V2-004 | Shared candles/option-chain/assessment feeds, five evidence-gated engines, blank sixth | **PENDING** | Rate limits, expiry/422, historical cache, no synthetic live |
| V2-005 | V2 actual Android app, separate package + secure native login and signed APK workflow | **PENDING** | Full CI, APK metadata/signing and alongside-legacy install |
| V2-006 | Staged Oracle rollout, backup and restore, exact deployed SHA, live read-only + device acceptance | **PENDING** | Rollback and no legacy interruption |

## User's three added V2 requirements (2026-11-18)
1. **One, two or three phones**: capacity is 3 enrolled devices **including one master**; avoid issuing independent Dhan requests just because more phones are connected.
2. **Owner-controlled Master Admin**: owner alone manages delegated read-only device access to specific feed categories, login access disable/revoke and enrollment. No delegated main Dhan login, token or master rights. Actual auth MUST be enforced server-side; pure policy code is not authorization.
3. **Completely separate GitHub folder and separate Journal**: `pilot_v2/` is the only new-work code root and `pilot_v2/docs/` owns V2 journal/handoff. Legacy remains frozen, archived in Git history, NOT deleted or stopped.

## Mandatory journal writing convention
Each implementation batch append to `pilot_v2/docs/V2_WORK_LOG.md`:
- WHY (user request/root bug), exact source SHA, modified file paths;
- WHAT was implemented and what was *not*;
- targeted tests (pass/fail), full CI exact run ID and outcome (record update once confirmed), Oracle deployed? Dhan requests? APK? device?;
- open blockers and **NEXT EXACT ACTION** with no guesswork.
Maintain this Master Journal's table and `V2_HANDOFF.md` current status in the **same atomic commit** as related edits. Keep historical FAILs, do not rewrite outcomes. No empty/duplicated test runs to create apparent progress.

## Resume protocol for a new chat
Read `V2_HANDOFF.md` → this Journal → `V2_WORK_LOG.md` → current GitHub HEAD & latest 10 workflow runs, then immediately pick V2-002 at the first red gate and work forward. **"ok" = continue**, not ask user to restate their instructions. If a result is not yet confirmed mark PENDING rather than PASS.

## Non-negotiable
Do not build V2 by bumping legacy `pyproject.toml` or overwrite the old app's package/signing. Do not shut down old server when V2 work starts. Never print tokens, bypass Dhan consent, run unauthorized orders, or call an unverified quote LIVE. Owner authentication/revocation and protected per-feed entitlement are part of V2, not a UI-only toggle.

## Latest batch V2-002A — 2026-11-18
- Scope: `pilot_v2/device_sessions.py` and `pilot_v2/tests/test_device_sessions.py`, pure server-side opaque session interface with mock verification, expiry, per-feed access and immediate secondary revocation. No deployed HTTP endpoint, keystore bridge or token persistence. CI needs exact commit verification.
- Next: CI then V2-002B provider-backed cryptographic proof and Dhan reauth status; preserve three-device limit and old app.

## CI correction V2-002A-CI3
- V2 CI #3 at `7c2c437`: **FAILURE**, 10 tests / 1 ERROR on malformed dict fake master proof raising raw TypeError in the mocked verifier. Fix now in `device_sessions.py` and targeted defensive regression. New CI exact SHA pending, do not erase failure.

### V2-OWNER-STANDING-WORKFLOW-20261118 — continuing instructions
Owner wants ordinary V2 GitHub code+test+journal work to proceed without repeated approvals; new-chat phrase “BOT KING V2 का काम जारी रखो” means fetch HEAD and resume earliest unclosed V2 gate. Approval does not cover privileged production, Dhan consent, paid subscriptions, other users' enrollment, live trades, or decommissioning legacy. No background work across chat closure. **Last V2 CI #4** run `44282538921`, `a020de855` SUCCESS; previous #3 failure retained in Work Log. Next V2-002B.

## Latest V2-002B-P256-TOKEN-STATUS (2026-11-18)
- New isolated real P-256 server-side verifier, 256-bit single-use challenge, replay/expiry and source-gated Dhan token status. A registered public key from trusted enrollment is a prerequisite. No HTTP/auth endpoint or production rollout; test with pinned cryptography and mocked device private keys. New V2 CI pending. Next verified provisioning/shared-store/token readiness gate.

## V2-002C-MASTER-ENROLLMENT (2026-11-18)
- Last proven CI #6 `44283251098` SUCCESS at `fa79f41`. Proposed V2-002C pure staged enrollment allows verified master session to approve a specific P-256 key and restricted feeds, then demands challenge signature BEFORE delegated device grant. No HTTP server or trusted persistent key-store. Source+tests+Handoff+Master+Work Log in one commit; new CI pending. Next atomic secure state backing and Oracle read-only auth readiness.

## V2-003A-SHARED-READ-ONLY-DELIVERY (2026-11-18)
- V2-002C CI #7 `44287980740` verified SUCCESS. New isolated shared read-only quote delivery prototype reuses one RevisionCache across up to three authenticated sessions and returns only each device's requested equity symbols or permitted indexes. No HTTP/WS/provider fanout or production integration; exact new CI pending. Next V2-003B union dedup and rate-safe collector, while real server-side durable auth remains open.

## V2-003B-GLOBAL-UNION-DEDUPE (2026-11-18)
- Confirmed V2 #8 `44288336050` successful. Added pure combined active-equity union across three devices, global 70 limit, index separation and removal of disabled-device subscription demand. Offline tests plus code and journals in one atomic batch, new exact SHA CI pending. Next V2-003C bounded collector, durable multi-worker auth and Oracle read-only inventory.

## V2-003C-QUOTE-BUDGET-429 — 2026-11-18
- Previous V2 CI #9 `44288636298` exact `9aa16e1` SUCCESS. Added isolated lease-based quote request planning with single active request, 1s global floor, per-symbol 60s attempt gap, explicit 429 cooldown and <=70+3 work envelope. **Offline contract only**, not actual Dhan API or multi-worker persisted state. New CI pending. Next close provider-safe persistent orchestration and auth/Oracle capability gates. See V2 Work Log for exact path and tests.

## V2-003D-SQLITE-SHARED-LEASE (2026-11-18)
- V2 #10 full pilot contract CI SUCCESS on `fa408433`. Added SQLite transactional durable provider lease state that persists cooldown, pending work and attempt timestamps across two test instances/restarts, with six synthetic tests; no Oracle deployment/Dhan API request. CI for this commit pending. Remaining gates: secure per-device server session store, authenticated upstream collector and broker entitlement.

## V2-004A-DURABLE-DEVICE-SESSION (2026-11-18)
- Prior V2 CI #11 run `44290644644` SUCCESS at `126e18db6f`. New separate `pilot_v2/durable_device_sessions.py` single-host SQLite transaction-backed persistent device grants and hashed opaque sessions across worker instances, with synthetic master/revoke/expiry tests. New CI pending, NOT production login; user authorization and P-256 proof must be cryptographically bound before endpoints, and Dhan token gate remains unverified.

## V2-004B-CRYPTO-DURABLE-LOGIN-COMPOSITION — 2026-11-18
- Confirmed V2 #12 run `44295202170` SUCCESS at `e81e0f4`. Added real cryptographic proof -> SQLite durable session composition with synthetic P-256 signing, master revocation and per-feed denial tests. CI pending. No HTTP or production auth. Important open gate: shared atomic nonce across workers and trusted enrolled-key lifecycle. Read-only Oracle token readiness not yet inspected.

## V2-004C-ATOMIC-CHALLENGE — 2026-11-18
- Confirmed V2 CI #13 at `97f0ee2` SUCCESS. Added SQLite transactional single-use hashed P-256 challenge persistence and verified login composition across independent worker instances; source/tests/journals one commit, new CI pending. Real HTTP, trusted key registration and actual Oracle Dhan entitlement/renewal status are NOT verified.

## Standing workflow rule — latest committed batch only (owner change, 2026-11-18)
Before any NEW V2 code/test patch or commit, inspect **only the immediately preceding V2 commit**: its exact changed files, its exact SHA's relevant CI run(s), and any failure logs. If its CI is PASS, proceed; if FAIL, correct that same failure and verify the corrective CI before unrelated changes. If pending or absent, clearly say so and check only that batch's result. Check the files ACTUALLY changed in that commit (whether 1, 2, 3, or more), **never an automatic ten-commit/ten-file sweep**. If the head is docs-only, inspect that latest commit and the most recent applicable source CI; do not claim docs CI proves code. Allow broader history inspection only for a concrete dependency, regression, or safety reason, not as an automatic rule. Keep V2 source, targeted tests, Master Journal, Work Log and Handoff in one atomic commit where safe. No repeated approval for ordinary code/test work.
- Status at this rule change: head `5b736217009fb0da83fe433839fed8dfe668d444`, V2 CI #14 `44296710626` **SUCCESS**. V2-004D owner-approved durable key registration/rotation is still pending; do not claim it has been applied.

## V2-004D-DURABLE-KEY-LIFECYCLE (2026-11-18)
- Previous docs-only `767f792` CI #15 SUCCESS (latest applicable source CI #14 PASS). New isolated `durable_device_keys.py` and tests add Master session-validated P-256 key registration and rotation, proof of possession before grant, single-host atomic key/grant/session update and old session revocation. Exact new CI pending. Not production-ready: login verifier static trusted key map must be switched to server-side dynamic key lookup and validated against current generation. Owner-controlled initial master enrollment needs trusted ceremony, not public API. Proceed to wire dynamic key registry before HTTP. No Oracle calls, APK, old app changes.

## V2-FAST-TRACK-JOINT-EXECUTION-AUDIT-20261118
- Audit document `pilot_v2/docs/V2_FAST_TRACK_AUDIT.md` defines four combined packets, bottlenecks, test/commit cadence, server preflight/stage/build guardrails, and security reasons not to skip auth/release checks. Pre-audit V2 code SHA `b457316`, CI #16 `44298167518` PASS. This entry updates documentation/current status only and does NOT implement optimized workflow filtering or new server/app code. Next implement FT-1 in one tested source batch.

## FT-1-FASTER-CI-CURRENT-KEY-20261118
- Immediately preceding audit commit `24c3183ff864cc4e03ae57208b3398d5870f2df6` changed five V2 docs; exact CI #17 `44298940057` SUCCESS. Implemented two FT-1 improvements in a single source/test/docs/workflow commit: (1) V2 workflow excludes docs-only changes from full regression, while combined source+docs still triggers; (2) `DurableP256ChallengeVerifier` accepts trusted key resolver to read current delegated P-256 public key, instead of static cached delegated keys. Added synthetic cross-worker rotation/login tests. CI exact source SHA pending; **not** production ready because verification→session issuance race, bootstrap, multi-host and native Android proof still need security hardening. Next FT-1 race closure and API mock integration.

## FT-1-ATOMIC-LOGIN-ROTATION-20261118
- Previous source commit `19746fb2ed35649e1f9b831e742110f55ec748e6` exact pilot CI #18 `44299581660` SUCCESS. Added `atomic_verified_login.py` and tests: single SQLite writer transaction verifies current trusted master/delegated P-256 key, consumes nonce and creates hashed session; key rotation/disable uses the same transaction lock, closing the verify-to-issue race on supported local single-host DB. Source+tests+docs in one mixed commit, CI pending. Real endpoints/native app/provider validation remain separate gates.

## FT-1-ATOMIC-LOGIN-CI19-TEST-CORRECTION
- CI #19 on `57e8d18` FAILED one test out of 74; old master test session was legitimately invalidated by new login. Corrected test to use newest master bearer. New CI pending; never bypass token rotation just to make test pass.

## FT-2-API-MOCK-MOBILE-20261118
- Previous commit `ad5b84ef9e9551bbfe61ca2fd2a84aa6848a8c79` CI #20 PASS. New `api_contract.py` + `mobile_contract_mock.py` + tests implement one versioned, default-off read-only schema. Code/tests/docs single commit, CI pending; not a deployed server or built mobile.

## FT-2-HTTP-OFF-V2-FLET-SHELL (2026-11-18)
- Previous source `b705ff0` CI #21 PASS. New `http_gateway.py` exposes only authorized GET quotes/indices when explicitly enabled with durable session and server-only provider; default is no routes. New independent `pilot_v2/android_app` 2.0.100 offline Flet shell and tests. Full new CI pending. No Oracle production, Dhan requests, live orders or APK.

## FT2-ORACLE-PREFLIGHT-APK-GATE-20261118
- Previous V2 #22 run `44302157577` exact `33c45eef` SUCCESS. New `oracle_preflight.py` emits read-only source SHA/systemd limited metadata (never credentials or provider request), `android_build_gate.py` validates distinct V2 package metadata and blocks misleading build assumptions, plus offline tests and operator guide. This is not a production Oracle audit result, only tooling; new CI pending. Next operator-produced preflight evidence and signed V2 workflow once secure app/data paths are ready.

## V2-CATEGORY-CONTINUITY-20261118: canonical live category register
- Previous latest V2 source commit `d8fe238d95d9f9fbf51453005f7a82589d0c98ec` and its 8 changed files reviewed; exact source CI #23 `44302676179` SUCCESS. Created 12-category live status table, complete stage summaries, S1–S5 next work schedule, latest-only CI check rule and test evidence logging format in `V2_LIVE_STATUS_AND_SCHEDULE.md`. Refreshed old header from stale #1 to verified #23. DOCS ONLY: no Oracle server changed, Dhan request, signed APK or Android install. Follow this register in new chats.

## S1-DHAN-CAPABILITY-FAIL-CLOSED-20261118
- Previous commit `98b099fb49274e3030d02734c05a192077a28f96` docs-only (five V2 files), no source CI expected; preceding source `d8fe238d95d9f9fbf51453005f7a82589d0c98ec` #23 `44302676179` PASS. Added pure readiness matrix for Dhan token, verified Oracle runtime, equity/index quote route separation and 0/5/51/70 demand. Synthetic evidence flags never imply actual broker capability; exact new CI pending. No Oracle/Dhan/Android changes.

## S1-READINESS-DURABLE-LEASE-INTEGRATION
- Previous source `6154f460c5c3b8c9714537b7eaf4b190927d1197` exact CI #24 run `44304560985` PASS. Added synthetic-only staged collector scheduler integrating explicit capability/token gate with one durable SQLite quote lease, independent equity and index lanes, shared 429 cooldown across mock workers. New source CI pending; no Oracle data, broker calls or signed APK. Actual operator Oracle preflight remains S1 external gate.

## V2-OWNER-SAME-FLET-BRANCH-FINISH-ACTIVE-BATCH-20261118 — Owner correction / locked work order
- Product name: **BOT KING Version 2**. Existing implementation uses **Flet** under `pilot_v2/`. Stay on current `pilot/botking-v2-smart-gateway-20261118` branch and existing V2 journals; **do not open a new branch, create parallel project, add speculative design, or silently modify existing agreed architecture/rules**.
- **Do existing work first:** Finish the current S1 synthetic readiness/shared lease gate already coded, using its exact source CI #25 run 44304920157 **SUCCESS** on SHA `86b39da86f53c1ef32497d36d82a67835fda2343`. A green synthetic CI closes only that offline subgate: actual Oracle capability remains unverified and is scheduled **after V2 APK**, per owner app-first release ordering; it must not stall independent offline Flet app work.
- **Next app work:** Continue the existing Flet V2 app/contract/UI pieces in the established S2/S3 scopes, then one consolidated exact-SHA regression and a separately signed V2 APK candidate; **only after APK** do needed Oracle Gateway/server changes against app demand, with guarded backup/deploy and separate mobile acceptance. Preserve old BOT KING untouched.
- **Do not start ad-hoc 4-phone edits:** User clarified desired support for 1–4 mobile devices, shared Dhan→Oracle and Oracle→V2 logical pipes, master Smart Settings/Control. Current isolated device policy/tests still cap at three enrolled phones, including master; **difference is a deferred compatibility item** for the existing combined multi-device acceptance batch, not a reason to interrupt current S1/app completion. Never claim four phones currently work.
- Every actual source/test/CI/APK/Oracle action must be recorded in existing V2 Work Log + Master Journal + current status, with exact evidence; no background completion claims. This entry is a documentation-only alignment, not a new feature or an Oracle/Dhan request. No production/server/API/order/APK change.


## V2-OWNER-APP-CONTROL-ORACLE-TRANSPORT-ONLY-20261118 — OWNER FINAL ARCHITECTURE CORRECTION (supersedes earlier server-owned-settings proposals)
- **Why:** Owner explicitly rejects Version 1's Oracle-server-owned app settings/data-management model for BOT KING Version 2. Preserve the existing Flet V2 branch and completed code/tests; no new branch, no separate concept, no unrelated feature additions.
- **ONLY intended logical pipeline:** Dhan market data → ONE shared logical upstream pipe into existing Oracle host → ONE shared logical transport to BOT KING Version 2 clients. Target 1–4 authorized mobile devices, reusing shared transport without four independent Dhan feeds; this is a TARGET, not proof current policy already supports four devices.
- **APP OWNS ALL PRODUCT SETTINGS AND INTELLIGENCE:** saved 5 Watchlists, global 70 unique stocks, owner Smart Settings/Smart Control, per-device display/permissions and requested data, refresh timing (09:10–15:45 IST auto, outside market manual only), frame selection, Scanner, Super Five, 3 independent index cards, Options views, five evidence-gated filters and empty sixth. Flet client owns choices and screen logic, last-good display and filter logic; no server-hosted app settings or server-chosen watchlist/scan/scoring rules. Shared data delivery can be cache-backed as a transport optimization but is NOT configuration authority.
- **ORACLE MINIMAL JOB:** Maintain existing Dhan authenticated connection, token expiry/renewal where actually supported, and necessary secure read-only transport (authentication, TLS, safe broker 429 pacing, ephemeral shared queue/cache to avoid duplicated upstream calls). Do not turn Oracle into a product settings engine or a new server-controlled multi-lane preference manager. Server may be required to enforce transport security, provider quota and device authentication; these technical necessities are not app product settings.
- **RENEWAL EVIDENCE LIMIT:** Owner reports legacy token auto-renews; existing prior probe found `token_source=oauth_consent` and `renewal_supported=false`. These conflict as to what is automatically renewable. Preserve functioning legacy renewal untouched; verify actual current Dhan renewal mechanism during post-APK Oracle phase without secrets or unsupported consent bypass. Do not promise unassisted 24-hour token renewal as already proven.
- **Work order:** complete existing Flet BOT KING V2 code/data contract and screens using APP-OWNED settings → one consolidated test gate at exact SHA → versioned separately signed V2 APK candidate → only thereafter necessary Oracle transport/gateway adaptation and real device validation. Batch any design-mismatch repairs together; do not interleave speculative redesign. Existing offline S1 synthetic readiness/lease CI #25 `44304920157` completed SUCCESS at `86b39da86f53c1ef32497d36d82a67835fda2343`. No Oracle deployment, Dhan network call, order or APK proof inferred.
- **Observed gap in existing V2 prototype:** `gateway_contract.py` currently creates client-demand models; `shared_quote_gateway.py` stores server-side `_selections` and computes union demand; this must be interpreted as bounded routing/cache state, never as owner settings. Device policy still currently caps at 3 including master; 4-client goal belongs to existing bundled mobile/device acceptance work, not a spontaneous new feature/branch.
- **Result:** Owner instruction is formally added to CURRENT canonical V2 docs; this is documentation alignment only. No code/API/Oracle/service/Dhan/APK/order changes. **Next:** Finish Flet app under this strict app-owned controls design and group necessary contract corrections in existing batch, test and journal actual evidence.


## V2-OWNER-AUTH-FREEZE-FINAL-JOINT-AUDIT-20261118 — Preserve existing Dhan login and batch all discovered defects at the final pre-build gate
- **OWNER RULE:** Dhan API token expiry, consent and renewal follow the broker's actual policy. The pre-existing BOT KING login/renewal implementation may already handle the permitted workflow, whether app-side initiation or Oracle-side broker credential operations. **DO NOT edit, move, rewrite, reconfigure, or test live renewal speculatively** in V2, and do not introduce a fresh token lifecycle architecture. Reuse existing authenticated flow exactly as proven until a concrete integration defect is demonstrated. Historical `oauth_consent`/`renewal_supported=false` probe prevents any unverified claim of automatic 24h consent renewal; it does NOT justify altering working code.
- **CONTINUE EXISTING FLET V2 BUILD PATH** on the current branch, preserving the final owner rule that product settings, controls, watchlists, scanning, timeframe choices and Smart Data logic belong to BOT KING Version 2; Oracle remains minimal necessary authenticated Dhan transport/renewal support, not a server-side app settings controller.
- **DEFERRED DEFECT REGISTER — collect, do not opportunistically patch:** For each observed error or questionable mismatch, append a unique ID, impacted Flet V2 file/screen, reproducible evidence and test, severity (critical/security/release blocker vs deferrable), expected vs actual behavior, dependency/risk, and proposed smallest correction. Distinguish verified defect from hypothesis; do not transform a passing module into a new design. Keep this as one section in existing V2 documents, not an independent branch/project/file.
- **ONE FINAL JOINT GATE BEFORE APK:** When V2 existing functional scope is completed, review the whole app once across login/auth (read-only assessment of existing implementation), saved watchlists/70 distinct symbols, Smart Settings/Control/1–4 device target, index/quotes/candles/timeframes, Scanner/Super Five, five source-gated filters and blank sixth, Options/UI cache and 429 safety, offline/after-hours recovery, Android identity/build metadata. Convert verified defects into one bounded coordinated batch of related source fixes and focused tests; run one consolidated full exact-SHA CI gate. If safety-critical issue cannot be grouped safely, it still must block an unsafe APK rather than be ignored. No repeated micro-edit/test cycles for mere speculation.
- **RESULT:** This is a journal/priority rule update ONLY. Latest V2 code CI #25 / 44304920157 on `86b39da86f53c1ef32497d36d82a67835fda2343` was SUCCESS; subsequent commits were docs-only. No V2 code changed, no Oracle deploy/restart, no Dhan market/renewal requests, no live orders, no APK built. **NEXT:** finish the existing Flet app batch while logging defects; prepare one final combined audit/repair/test batch, then signed APK and post-build Oracle transport adjustments only as necessary.


## V2-SMART-FAST-TRACK-CI-EFFICIENCY-RULE-20261118 — Owner requires existing fast GitHub method, no repeated 2-minute manual cycles
- **WHY:** Owner observes previous V2 work/CI often 15–17 seconds but repetitive assistant-side activities may take ~2–2.5 minutes; follow the existing V2 Fast-Track system rather than adding any new branch, process, or different app concept.
- **MEASURED GITHUB FACTS:** Workflow `.github/workflows/v2-pilot-contract.yml` already scopes `pilot_v2/**`, excludes docs-only `pilot_v2/docs/**` and `pilot_v2/README.md`, runs compileall and all pilot_v2/tests with pinned offline dependencies. Observed CI #23 (44302676179) start 12:18:32Z, updated 12:18:49Z = **17s**; #24 (44304560985) start 12:30:23Z, updated 12:30:38Z = **15s**; #25 (44304920157) start 12:32:34Z, updated 12:32:52Z = **18s**, all SUCCESS. Across the latest 15 observed V2 runs, a failed #19 was corrected and later #20 SUCCESS; do not rewrite failed evidence. These are workflow elapsed timings, NOT the elapsed time for all tool calls, authoring, network latency, safety review or release testing. There is no verified guarantee that whole development turns will finish in 15–17s.
- **LOCKED SMART EXECUTION RULE (reuse, not redesign):** (1) inspect only immediately previous commit and changed files plus exact applicable CI by default; broaden only on demonstrated dependency/failure. (2) Freeze one existing app-first scope and defer unrelated bugs to the final joint defect register; avoid repeated full journal/large-source rereads when unchanged. (3) Author 2–4 coherent source repairs with associated targeted tests and existing V2 journal/handoff in ONE atomic tree+commit, not multiple commits for source/test/docs; for a documentation correction make ONE docs-only commit. (4) Run targeted offline test locally when possible, then one relevant V2 workflow on the exact source SHA; don't rerun successful full suite without input change. (5) Existing path filter must preserve docs-only CI skip, but code/test/security/CI and final signed APK release gates remain mandatory. (6) Fetch CI result once when available, inspect failing job logs only if FAIL, make one cause-specific correction then retest. (7) Maintain only the existing V2 status/Master/Work Log/Handoff, succinctly record WHY/CHANGE/TEST/SHA/STATUS/NEXT and never introduce new duplicate registries or branches. (8) Use parallel independent read-only file/CI retrieval where safe; serialize dependent GitHub ref writes.
- **APP MODEL UNCHANGED:** Flet BOT KING Version 2 owns all settings/Smart Control/refresh/watchlists/filters. Existing Dhan token renewal and Oracle secure shared transport preserved. No new Oracle product settings, live orders, speculative 4-device implementation or additional features introduced in this optimization.
- **RESULT/GATE:** Workflow configuration was already optimized; there is no evidence-based reason to modify it in this batch. Journal/rules documentation only; no source code/test edits, no new CI dispatched, no Dhan/Oracle calls, no server restart, no signed APK. NEXT: apply this method to the next existing Flet V2 app batch and quantify actual source CI results, preserving one final combined pre-APK audit/repair/test stage.


## V2-S3-FLET-LOCAL-SCREENS-WATCHLIST-20261118 — Existing Flet mobile shell becomes app-owned offline screens
- **WHY:** Last V2 code CI #25 run 44304920157 SUCCESS at 86b39da; newest branch head before change 7fb566a docs-only. The V2 Flet main.py was one static placeholder, with no three-screen navigation and no actual user-controlled local Watchlist. Owner orders finish existing app before Oracle, without changing Dhan login/renewal or adding a new branch.
- **SOURCE:** `pilot_v2/android_app/src/main.py` renders bottom Dashboard/Watchlist/Settings, three independent index WAIT rows, five evidence-gated WAIT filters plus empty sixth, and an offline 3m Watchlist. `pilot_v2/android_app/src/app_state.py` owns 5 in-memory lists and validates up to 70 unique equities across lists, rejects duplicate/index/invalid symbols and exposes the existing `watchlists` payload shape. Only in-memory app-owned settings; **no persistence, Dhan request, Oracle call, token edit or fake quotes**. `pilot_v2/tests/test_flet_app_state.py` adds synthetic 0/5/51/70, duplicate, capacity, invalid and removal tests without importing Flet runtime.
- **SCOPE LIMIT:** This is a real offline Flet app scaffold + state module, NOT a live/data-connected app, verified Flet UI execution, installed APK or phone pass. UI runtime/API compatibility needs final joint pre-build audit; app-local persistence, Scanner/Super Five, verified filters, login/device enrollment, network client and signing remain open existing scope. Keep deferred defects list for one final grouped repair; no live order calls.
- **GATE:** V2 full isolated test workflow on exact new source SHA must complete SUCCESS before further source edits. No Oracle production change, no service restart, no broker or order requests, no APK.

## V2-S3-FLET-DEVICE-LOCAL-WATCHLIST-PERSISTENCE-20261118 — app-only saved Watchlists (no Oracle settings)
- **WHY / previous gate:** Existing Flet 3-screen app + 70-symbol state commit 302ed996 exact V2 CI #26 run 44308072988 completed SUCCESS. Watchlists were memory-only and were lost across app restarts. Owner requires all settings remain in V2 app, Dhan renewal untouched, final grouped audit later.
- **SOURCE:** `pilot_v2/android_app/src/app_state.py` adds schema-v1 primitive device-local snapshot and strict validated restore (reject corrupt, unsupported-schema, duplicate, 71st and index symbol). `pilot_v2/android_app/src/main.py` uses Flet `page.client_storage` for local save/restore on add/remove, without sending product settings to Oracle; storage failure is visibly signaled, and corrupt preexisting saved data is NOT overwritten on subsequent additions. No Dhan or login code touched. No live price, user tracking or order route.
- **TEST:** `pilot_v2/tests/test_flet_app_state.py` adds roundtrip/no-alias and corrupt-save fail-closed tests. Testing is isolated stdlib synthetic app-state; actual Flet client_storage integration and Android restart remain final acceptance gates. App screen catches known storage errors only. Run full exact SHA V2 Pilot Contract Tests; result PENDING until observed.
- **RELEASE DEFECT LIST:** Actual V2 hardware local-storage reload and Flet runtime widgets must be verified once at final joint prebuild gate. Old app untouched, Oracle service no change/restart, Dhan requests 0, token changes 0, trades 0, APK not built. NEXT: observe full exact CI; if PASS continue existing Flet functional screens and source-safe data contracts.

## V2-S3-DEVICE-PERSISTENCE-CI27-SUCCESS-20261118
- **EXACT TEST:** `BOT KING V2 Pilot Contract Tests` run #27, ID `44308423480`, completed **SUCCESS** on exact Flet device-local state code SHA `58ea34f9178b2370145f8d45a3214b56e436ee0a`. Previous #26 `44308072988` also SUCCESS on `302ed996`. https://github.com/vaishnavi596/volume-king/actions/runs/44308423480
- **RESULT:** Isolated source compile/tests PASS; actual Flet app UI/client_storage behavior, device persistence after restart, real gateway quotes, signing and installed APK still NOT verified. No Oracle host or Dhan token edits, market request, orders, or server restart.
- **NEXT:** Continue current Flet V2 app first, with existing Smart Fast-Track and deferred final joint bug-fix audit. Preserve app-owned settings, no speculative token renewal edit or server settings control.


## V2-S3-APP-OWNED-SMART-DATA-SETTINGS-20261118 — app-owned Smart Data settings, zero broker traffic
- **PREVIOUS GATE:** V2 offline Flet local Watchlist persistence source `58ea34f` exact CI #27 (44308423480) SUCCESS; previous `911a1cba` was docs-only result journal, no source CI. Inspected actual Flet main.py, app_state.py and current test instead of re-auditing legacy/Oracle.
- **SOURCE:** `pilot_v2/android_app/src/smart_data.py` defines fail-closed app-owned Smart Data settings with 180s default, selected-count 0/5/51/70 plus 3 independent indexes, 09:10–15:45 Asia/Kolkata window, and explicit confirmed-market-session gate (never invent holiday status). `pilot_v2/android_app/src/main.py` adds Settings local auto-refresh toggle + 180/300/600s selector stored in Flet client_storage, no Oracle product setting. Saved settings corruption does not overwrite old data. **No timers or Dhan requests**: actual provider synchronization/selected-interval enforcement is later existing app/server integration work, so do not mislabel these settings as live-enabled.
- **TEST:** New `pilot_v2/tests/test_flet_smart_data.py` synthetic demand scaling, open/close/holiday-unconfirmed boundary and strict storage schema/types. Full V2 workflow result PENDING until exact SHA checked.
- **RESULT/LIMITS:** Source + test + existing V2 journals in one atomic commit; Dhan login/renewal, Oracle server, provider requests, orders, APK untouched. Flet runtime and Android persistence must be verified in final joint gate. NEXT verify exact CI then proceed with current Flet screen/client integration, no new branch/features.


## V2-S3-FLET-SCANNER-LOCAL-SELECTION-20261118 — dashboard Scanner user selections without invented charts
- **PREVIOUS CI:** App-owned Smart Data code SHA `570470da2a97c239286e29ddc7e2beb50befcc8d` exact V2 CI #28 run `44309115013` **SUCCESS**. Inspected same Flet main, existing watchlist and app policy prior to changing code.
- **SOURCE:** `pilot_v2/android_app/src/scanner_state.py` adds validated app-local Scanner symbol/timeframe state (default NIFTY/1m, allow 1m/3m/5m and only 3 index or 0–70 selected equities); rejects deleted/unselected symbols and malformed saved state. `pilot_v2/android_app/src/main.py` places Scanner selectors below three Dashboard index WAIT cards, preserving bottom 3-tab navigation, and saves choices to phone's local client_storage. `pilot_v2/tests/test_flet_scanner_state.py` synthetic selected/deleted/corrupt/roundtrip tests. **No automatic Dhan history request, fake candles, generated signals or new gateway route**. Super Five remains clearly WAIT until verified history exists.
- **GATE:** Source/test/docs commit must receive exact full V2 CI. CI PENDING at journal author time; Flet runtime, actual phone persistence and chart refresh are final pre-build acceptance concerns, not synthetic green proofs.
- **INVARIANTS:** Dhan login/renewal frozen, Oracle no settings/deploy, existing Flet V2 branch only, last-good/source eligibility not misrepresented, 1–4 mobile target deferred to combined acceptance batch. No Oracle change, Dhan request, trading order or APK.


## V2-FAST-CI28-CI29-SUCCESS-20261118 — two exact-sha V2 app batches confirmed green
- **CI #28** https://github.com/vaishnavi596/volume-king/actions/runs/44309115013 completed SUCCESS on SHA `570470da2a97c239286e29ddc7e2beb50befcc8d` (app-local Smart Data settings, market-window/selection tests).
- **CI #29** https://github.com/vaishnavi596/volume-king/actions/runs/44309425851 completed SUCCESS on SHA `ed29dfd051d2b9e0d30705d215c004a22ee0097f` (app-local Scanner selected symbol/timeframe, stale roster and saved-state tests). Checked exact workflow run and completed successful compile/test job `134819385482`.
- **RESULT:** Both are synthetic offline GitHub test successes ONLY, not actual Flet widget/device, signed APK, authenticated live Dhan quote/candle or Oracle gateway validation. No Oracle service restart, production edit, Dhan request, token renewal edit, order call or APK. Completed two coherent app-first commits on ONE existing V2 branch, not another gateway concept.
- **NEXT in existing S3 functional scope:** integrate frozen validated read-only quote/candle payloads into Flet consumer state and show genuine last-good vs WAIT without token exposure, then complete remainder UI/candle/filter scope; keep errors for one joint final audit/repair batch, with exact-SHA regression before APK. No speculative server-side app settings or auth renewal edits.


## V2-S3-READONLY-DEVICE-QUOTE-CONSUMER-20261118 — Flet app local read-only quote consumer, offline and fail closed
- **PREVIOUS VERIFIED:** V2 app-local Scanner commit `ed29dfd051d2b9e0d30705d215c004a22ee0097f` exact CI #29 run `44309425851` **SUCCESS**. Current head `821c605e9855f4d5783157eb9d5061a001a3c0f7` docs-only result update. Inspected current `main.py`, `pilot_v2/api_contract.py` and `mobile_contract_mock.py`.
- **CODE:** `pilot_v2/android_app/src/quote_view.py` validates frozen version-1 Dhan-only read-only snapshot fully (required fields, schema, symbol roster, finite positive quotes, revision, no live_orders or fake verified claims) before mutating app-local per-symbol quote state. Empty/partial newer revisions retain last-good; older/invalid snapshots reject atomically; removed equities are hidden/evicted while three indexes remain separate. `pilot_v2/android_app/src/main.py` displays `WAIT` or `HIST (unverified)` using this local consumer on Dashboard, Scanner and Watchlist; there is **NO real gateway fetch, network subscription, source timestamp, injected synthetic price at runtime, chart or filter signal**. Existing app settings and renewal untouched.
- **TESTS:** `pilot_v2/tests/test_flet_quote_view.py` covers synthetic selected/index quotes, partial retention, older revision, foreign provider, 70-roster authorization, invalid/extra fields, and removed-symbol leak prevention. Commit includes current V2 Work Log/Master/Handoff/Status in one batch. **CI for new exact SHA PENDING** at creation.
- **OPEN:** Real authenticated client/feed transport, historical candles, five factor readiness, Flet widget and phone data rendering, secure storage and APK remain unresolved. Device quote cache is ephemeral; no Oracle product settings. No Oracle service change/restart, Dhan requests/token modifications, trades or APK. Next exact CI then existing app-first S3 candle/feed integration.


## V2-S3-READONLY-QUOTE-CI30-PASS-20261118
- **EXACT CI:** V2 Pilot Contract Tests #30, run `44309995541`, completed **SUCCESS** on `3e00adfb45d1dbadcd6a322b3609e5c67c8897d1`; compileall and isolated full pilot suite job `134821347942` SUCCESS. https://github.com/vaishnavi596/volume-king/actions/runs/44309995541
- **IMPLEMENTED:** Device-local V2 read-only quote schema guard and atomic last-good retention, WAIT/HIST rendering for three independent Dashboard indexes and selected Watchlist/Scanner symbol; no actual data network producer, no actual timestamps or verified-live claims.
- **LIMITS:** Offline source/CI PASS only. No real Flet device run, market data connection, candle chart, source-gated filters, signed APK, Oracle deploy/service restart, Dhan token change, broker request or order. Existing app-owned settings and frozen token renewal untouched.
- **NEXT:** Existing app-first S3 stage: reconcile candles/timeframe feed contract and five-filter WAIT displays against trusted input, keeping all defects in final joint audit list. Inspect this last batch/CI before next source change. Do not change app model or create another branch.
