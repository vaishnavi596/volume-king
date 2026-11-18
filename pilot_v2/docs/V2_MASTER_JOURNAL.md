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
