# BOT KING V2 — Fast-Track Joint Execution Audit
Date: 2026-11-18
Status: audited proposal, NOT a production deployment or an approved release.

## Grounded baseline
- Pilot branch: `pilot/botking-v2-smart-gateway-20261118`, current pre-audit head `b45731646a295e0084b95fac3b30e36d8079d488`.
- Verified V2 Pilot Contract Tests **#16 SUCCESS**, run `44298167518`, exact source SHA `b457316`. Immediately preceding commit changed two new executable/test files and four docs files; no default prior-ten-commit scan.
- V2 CI `.github/workflows/v2-pilot-contract.yml` currently runs compileall and **all pilot_v2/tests** with pinned cryptography on every push that changes `pilot_v2/**`, including docs-only changes. Thus docs-only commits launch redundant full pilot tests.
- Legacy `.github/workflows/build.yml` is tied to root `pyproject.toml`, legacy Flet app, existing signing and a different package. The V2 `pilot_identity.json` is metadata only. Separate V2 package/APK build does NOT yet exist.
- Master Journal header historically still pointed to V2 #1 / 577f07d even after successful #16, while append-only latest work records #16. New-chat handoff must always prefer current GitHub SHA and exact CI evidence over old headers.
- All current V2 source proofs are isolated offline tests. No live Oracle V2 API, real Dhan market collector, Android Keystore production implementation, V2 signed APK or mobile acceptance has been demonstrated.

## Observed waste and immediate corrections
1. **Too-small pushes**: Several safety contracts were added one module and one test at a time, each launching a full workflow. Batch closely related changes (typically 2–4 implementation files plus tests, documentation) into ONE atomic commit when safety permits; do NOT merge changes that cannot be tested/reviewed coherently.
2. **Docs trigger test CI**: Change V2-only workflow path filtering to exclude `pilot_v2/docs/**`, `pilot_v2/README.md` and other docs-only paths, while retaining source, tests, workflow and configuration triggers. Documentation remains inside the same code commit as a completed batch; standalone docs-only fixes need not burn a full regression run. Implement with an explicit, tested workflow-path patch; don't declare done until actual GitHub behavior verified.
3. **Manual repetitive checking**: Only inspect the immediately preceding V2 commit's changed files and exact relevant CI. PASS -> proceed; FAIL -> fix same failure and re-verify; pending -> check that run. Broaden history only when there is a concrete security/dependency reason.
4. **Stale journal banner**: Keep a single compact `CURRENT STATUS` at top (branch/HEAD/last successful *source* CI/current partial gate/next blocker), append detailed historical evidence below, and do not accumulate contradictory LATEST banners.
5. **Serial server then Android work**: Freeze the API schema and mock it now; develop Android navigation/login/data rendering against a test fixture *while* implementing Oracle-side auth/collector behind OFF feature flag. Final actual server and device acceptance remains gated and cannot be parallelized with unverified critical dependencies.
6. **No early heavy APK builds**: Validate static Android V2 identity and local UI tests first. Run the expensive signed APK pipeline only after independent package ID, signing/certificate and full regression are green; optionally one pilot smoke APK after secure mock integration (clearly marked not live) rather than a full release claim.

## Fast-Track work packets (execute in this order, in fewer GitHub pushes)
| Packet | Grouped work | One main joint gate |
|---|---|---|
| FT-1: Security close-out | Dynamic *current-generation* public key lookup integrated into durable challenge+session layer, revoke/rekey denies old key, secure enrollment and master recovery design; fix workflow path and journal banner as part of same tested batch. | P-256 rotation, replay, 3-phone revocation, multi-worker and fail-closed offline suite |
| FT-2: Gateway + Android contract | Versioned /v2-pilot read-only API with off-by-default mount, typed JSON schema, auth/delegated feed guards and synthetic fixture; create separate V2 Flet app shell/independent Android ID and matching client mock. | Server API contract + client contract single combined offline suite |
| FT-3: Broker/data lanes | One trusted collector using production-observed Dhan capability and entitlement evidence, shared 0/5/51/70 equity union plus three indexes, 429 cooldown, revision/cache last-good, 1m/3m/5m historical lanes and options/assessment source gates. | 2/3-device shared fanout, provider pacing, disconnect and stale-data no-fabricated-live tests |
| FT-4: Deployment and APK | Read-only Oracle inventory first, staging with backup/preflight and explicit owner-approved production actions, rollback, smoke health/auth tests, separate signed Android V2 package and version 2.0.100 (or higher), one-phone install alongside legacy. | Exact SHA deployed and signed APK metadata/version/cert + device acceptance; legacy untouched until proven safe |

## Server task audit and low-movement execution
- Before server changes: **one read-only preflight report** for actual service source hashes/systemd/nginx/auth routes, OAuth token source/expiry/renewal capability, broker rate-limit/WS entitlement, provider market maps, data cache health; redact secrets. GitHub/backend files are NOT proof of Oracle production state.
- Use **one staging transaction/backup and rollback script** to validate files, permissions, syntax, test suite, change manifest and exact SHA. No Dhan token copying and no switching off old service.
- Use **one guarded deployment action** only when explicitly authorized for production and all gates pass. Separate pre-/post-health and protected-data smoke evidence from local test success.
- Avoid repeated manual server shell copy/paste; a small number of verified scripts are better, but exact CLI interactions depend on what the actual Oracle runtime preflight finds. Do not promise a precise number of clicks or guaranteed time savings.
- Android and server code can be implemented concurrently against the *same* frozen API contract; actual live integration and release require green auth/provider/rollback gates.

## Critical release blockages
- Current public-key verification uses a static trusted-key map in some paths; rotating SQLite key does NOT automatically invalidate that old map. Close this before HTTP login.
- Durable SQLite challenge/session stores are suitable for a vetted *single host local filesystem*, not an unreviewed network FS or multi-host deployment.
- Android P-256 native Keystore/biometric proof is not yet wired. OAuth-consent Dhan tokens may require owner reauthorization: previously renewal_supported=false; never bypass.
- Five filters require actual source evidence, sixth stays blank, read-only trades OFF.
- No live Oracle endpoint and V2 signed/installed APK yet; never mark V2 finished based on offline tests.

## Working rule
Each packet: inspect only previous commit+CI -> implement 2–4 coherent changes+targeted tests locally -> one source/tests/Journal/Handoff commit -> one full V2 CI -> fix failures before next packet. Short meaningful status updates; owner should not be asked for routine developer micro-approvals. Journal fields: exact SHA, CI run, source PASS/FAIL, Oracle deployed yes/no, Dhan requests yes/no, APK yes/no, NEXT exact blocker.
