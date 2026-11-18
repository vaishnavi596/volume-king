# BOT KING V2 — CANONICAL MASTER JOURNAL
**Owner lookup:** "बोट किंग इंप्रूव वर्जन का जर्नल देखो", "BOT KING IMPROVED V2 JOURNAL".

This is the **single authoritative V2 continuity ledger**, alongside `V2_HANDOFF.md` (short current orientation) and `V2_WORK_LOG.md` (append-only detailed commands/tests). Old BOT KING `docs/BOT_KING_WORK_LOG.md` is preserved and is not the current V2 work queue.

## Current status — 2026-11-18
| Field | State / evidence |
|---|---|
| Working branch | `pilot/botking-v2-smart-gateway-20261118` |
| New independent source root | `pilot_v2/` |
| Last verified V2 source commit | `577f07d9d9d45d50b3836bc12b5c3c334bd28375` (V2-001) |
| Last V2 CI | **#1 SUCCESS**, run `44281428941`, exact source commit `577f07d` |
| New V2 application version/package | Planned **2.0.100** / `com.botking.bot_king_v2`, metadata ONLY |
| V2 gateway | API prefix `/v2-pilot`, **feature flag OFF**, NOT served on Oracle |
| Master device feature | Pure offline rules implemented, no authenticated network implementation |
| Current legacy / installed app | Preserve existing working app and server; no V2 cutover |
| Server / Dhan API / orders | **No production edits, market-data calls or trades** |
| APK / mobile | **No V2 APK, no device PASS** |

## Workstream tracker
| Item | Scope | Status | Gate to close |
|---|---|---|---|
| V2-001 | Separate branch/folder, reserved identity, demand/cache + master control pure domain contract | **CODE + CI PASS** | 577f07d / CI #1 |
| V2-002 | Verified 2-gateway auth: Dhan token-type/expiry/renewal support; independent revocable Android sessions; master proof | **PARTIAL — V2-002A CI #4 PASS, V2-002B P-256 proof + token status CI pending** | Trusted device enrollment, shared durable sessions, Android Keystore + Oracle OAuth evidence missing |
| V2-003 | Shared broker quote collector, safe WebSocket/REST, up to 3 devices, 0/5/51/70 demand, 3 indexes | **PENDING** | Synthetic 429/disconnect/fairness, no duplicate upstream |
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
