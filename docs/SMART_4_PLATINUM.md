# SMART 4.0 PLATINUM — स्थायी विकास और Smart Doctor मानक
स्वीकृति: 25 नवंबर 2026। B1–B6 और भविष्य के सभी BOT KING V3 फीचर/सुधार पर लागू। SMART 3.0 के source safety, dependency closure, no competing CI push और no real orders नियम कायम हैं। यह नीति है; स्वचालित enforcement और नया runtime Doctor अभी लागू नहीं माने जाएंगे।

## 1. संयुक्त कार्य चक्र
P01 Reverse audit: exact branch HEAD, पिछला CI/raw log, canonical journal, मौजूदा source/tests/Doctor और उपलब्ध owner evidence पढ़ें।
P02 Feature registry: immutable feature ID, requirement, owner, planned/implemented/verified/blocked/retired status, dependencies, expected outputs, affected files/functions/screens, tests, evidence और next action। पुराने, वर्तमान, प्रस्तावित सभी features शामिल; planned feature को runtime error न कहें। कोई silent removal नहीं।
P03 Full link map: Dhan→Oracle→transport→adapter→cache→analysis→filters/engines→vote→all affected UI→Doctor; background/recovery/persistence/security भी जहां लागू। प्रत्येक applicable link का contract, failure mode और acceptance दर्ज करें।
P04 Zero skip: missing link/test/diagnostic या evidence gate explicitly OPEN/BLOCKED, कभी silently defer नहीं।
P05 Zero duplicate: stable IDs, reuse existing shared modules and exact verified evidence; changed dependency invalidates only affected proof. Duplicate commit/test count progress नहीं।
P06 Maximum safe joint work: dependency-related source, wiring, Doctor, tests और Hindi journal साथ; independent safe work combine, conflicting changes अलग। Server deployment/credentials/orders बिना अनुमति नहीं।
P07 Doctor-first: implementation से पहले observable checkpoints, expected values, error taxonomy, safe recovery और tests design करें।
P08 Doctor-together: नया/बदला feature बिना actual runtime diagnostic wiring और positive/negative test के complete नहीं। Existing feature coverage audit and backfill mandatory, not claim blanket coverage.
P09 Root cause: stable code, component/stage, file/module/function, build/commit, optional actual traceback line, expected/observed, source, symbol/timeframe/expiry/generation, observed time and data age, duration/queue/retry, affected dependency, redacted evidence, actionable next step. Distinguish observed root cause from suspected cause; unavailable fields unknown, never fabricate. Use bounded redacted telemetry; never expose credentials, tokens, personal/order payload.
P10 Pre-commit: reverse impact search including structural assertions and real runtime fixtures; syntax/import/contract checks, success/failure/stale/wrong-source/timeout/disconnect/cancel/recovery where applicable; record NOT RUN honestly.
P11 Fast CI: fail-fast targeted tests then necessary exact-SHA joint full gate, no redundant workflows, no new competing source push during existing gate. No bypass of required tests; docs-only policy update permitted only when non-conflicting.
P12 Recovery/security: retain last-good HIST separately, no fake LIVE/independent votes, bounded retries and cache, UI responsiveness, provider rate limits; no extra provider traffic from Doctor; no real orders.
P13 Auto next: OK = verify previous workflow and perform next safe work before reporting. If gate running, non-conflicting read-only preparation; if external blocker, exact action/owner/proof once, no repeated OK. No claim of autonomous work outside active sessions.
P14 Progress: fixed original 32 acceptance rows; four equally weighted applicable checkpoints per row (code, integration, tests, real acceptance), 128 baseline checkpoints. Each checkpoint requires a unique evidence link and status; N/A must be justified and explicit, never award automatic credit. Progress = verified checkpoint count / applicable count * 100, remaining complement, delta percentage points; report baseline coverage, per B1–B6, prior/current/delta and blocked vs verification pending. New scope separately versioned; regression may reopen a checkpoint and reduce progress. Prior 54% was provisional estimate, not certified; no invented baseline count until reconciled. CI test count not percent of work. Original 32 rows preserved; no double-counting same checkpoint.
P15 Final closure: feature only CLOSED when every applicable checkpoint passed and required owner/server/phone evidence observed; docs-only policy is not runtime implementation. B6 requires B1–B5 closure, full security/regression, signed APK and real phone/paper acceptance.

## 2. Platinum Doctor architecture contract
- Central feature inventory covers existing, changed and planned features; a shared diagnostic registry links each applicable runtime probe to stable feature ID and stage. Audit orphan features, orphan probes, missing mandatory fields and missing tests. Planned features are PLANNED, not runtime PASS or failure.
- Default compact active-only report: FAIL, BLOCKED, UNVERIFIED, TESTING, STALE, DEGRADED; healthy observed checks hidden with count. Separate coverage summary for planned and unobserved features. PASS only from measured evidence matching exact identity; never infer from source existence.
- One diagnostic envelope for Smart Active and Master Doctor; use existing cache and bounded telemetry, no additional provider request, no heavy synchronous full scan. Deduplicate identical fault identity, correlate downstream effects to upstream root while keeping affected feature IDs; retain first/last observation and count.
- Root cause location must be actual module/function and real trace line if captured; no fictional line number. Report user-safe sanitized error type/code and actual evidence, distinguish cause certainty. Stable error IDs not reused for unrelated failures.
- Performance: actual cache hit/miss, queue wait, worker time, request latency and age when measured; pending/unmeasured not zero. Protect UI/CPU/RAM and rate limit. Doctor must be read-only, generation-aware and bounded; no credentials or order execution.
- CI enforcement implementation OPEN: registry schema/coverage validator, feature-to-probe/test coverage gate, shared runtime envelope, stage error adapters and compact report, exact baseline progress validator. Backfill existing features incrementally by dependency groups. Each needs own positive/negative tests, CI and applicable phone/server evidence. Do not create seventh batch: track under relevant B1–B6 IDs, cross-cutting Doctor work mapped once.
- Joint work sequence: J1 B1+B2 source/performance, J2 B3+B4 filters/engines/voting, J3 B5 background/recovery, J4 B6 final acceptance. Parallel only when dependencies permit; no bypass of unresolved dependent gates.

## 3. Self-Healing and supervision (owner approved)
- Diagnosis remains read-only. A separate allowlisted recovery controller may perform only bounded, reversible local actions on exact generation; no arbitrary code edits, credential changes, server changes, trading logic or orders. No cancellation of in-flight provider work or clearing busy flags without actual ownership proof.
- Record detection, eligibility, attempted/skipped action, reason, actual exception type and code location when captured, generation, time, retry budget, before/after evidence, retest result, rollback applicability, escalation and actions not performed. Redact secrets. Reports available to supervisor in both Doctors; explicit retention/loss scope. Persistent bounded journal/export, per-action controls and rollback tests remain OPEN until implemented.
- First allowlisted action: existing Super Five cache-only observer retry with 15/30/300s cooldown, escalation after three failures, exact-generation reset, bounded 40-event session report; success only after guarded local publication, not UI/LIVE certification. No destructive action requiring rollback in this step. All other proposed actions require separate validation; no blanket auto-heal claim.

- Dashboard supervision: first mounted compact Repair Board, measured stage progress (not chance of success or project completion), actual session counters, scope, cooldown, escalation and selectable logs. UI updates only local section; no cooldown override. Manual repair action requires separate allowlisted validated scheduling, no duplicate worker.

- ONE SYSTEM / ONE DOCTOR UI: merge existing health, active errors, history, recovery and full audits into the Platinum Settings panel; keep dashboard compact repair board. Preserve old probes, history, retry controls and tests before removing standalone panels. UI consolidation does not imply a single runtime error registry or deduplicated compute until separately verified.


## SMART 4.0 — संयुक्त 5×20 Audit Set (25 नवंबर 2026)
Owner directive: सारे पुराने/नए अधूरे काम एक ही set में; 20-20 audit scope, zero skip, zero duplicate. ये पांच समान audit windows हैं, वास्तविक completion percentages नहीं। मूल 32 IDs और 128 checkpoints अपरिवर्तित; हर ID एक बार primary mapping में, dependencies cross-reference only.

| Audit window | Primary IDs | Features | Checkpoints |
|---|---|---:|---:|
| A01 Data/connection/freshness | B1.01–05, B2.04 | 6 | 24 |
| A02 Performance/cache/capacity | B2.01–03, B2.05–07 | 6 | 24 |
| A03 Six boxes/filter/voting | B3.01–05, B4.01–05 | 10 | 40 |
| A04 Background/recovery/Doctor | B5.01–05 | 5 | 20 |
| A05 Final/security/APK/acceptance | B6.01–05 | 5 | 20 |
| Total | B1–B6 | 32 | 128 |

P01–P15 हर window पर लागू। Existing scoped PASS evidence reuse; missing/blocked/unverified explicitly retain. Dependencies first; current active A03/B4.05 may continue existing read-only audit without claiming A01/A02 closure. No new production patch until related source/Doctor/tests reviewed. Source review found scanner_historical_final_vote reads shared_history before unsupported frame guard; actual impact and all affected tests/Doctor require review; not yet fixed. B3 #536 exact 44d1561, 1984/1984 PASS remains last gate. Registry VERIFIED={} remains unreconciled, no invented progress. A05 closure requires all applicable B1–B5 evidence, signed APK, physical phone/paper observation; no real orders. This is policy/ledger grouping only, not runtime implementation or completed audit of all windows.


### SMART 4.0 — 4×25 remaining-work execution frame (25 नवंबर 2026)
R1=B1+B2 (data/performance), R2=B3+B4 (engines/voting), R3=B5 (Doctor/recovery/background), R4=B6 (final acceptance). Supersedes 5×20 as execution grouping only; original 32 IDs/128 checkpoints and P01–P15 preserved. Four equal planning windows are not equal effort or certified progress. Prior 54/46 provisional; 56/44 not evidenced. Each applicable original checkpoint needs exact evidence; no duplicated credit. R2/B4.05 already active; dependent R1 evidence must still close before final acceptance.


## SMART 4.0 P16 — Dependency-first remaining work order (owner correction, 26 Nov 2026 IST)
This is the authoritative execution order, superseding any conflicting earlier sequence, not a new feature scope. Keep 4×25 R1–R4 and original 32 IDs/128 checkpoints. Do not interpret numerical ID order as dependency order. Preserve prior verified scoped evidence; re-open only when affected. Before every change, list prerequisite, evidence, blocker, dependent work and next eligible task. Work on prerequisite first, never treat downstream symptom as independent completion. Doctor, tests, security and journal accompany every changed link; B3.05/B5.05 and B1.05/B2.07 are cross-cutting work, not deferred end-stage tasks.

| Order | Primary work IDs (each appears once) | Exit evidence / dependency |
|---|---|---|
| R1.1 | B1.02, B1.03, B1.01, B1.04, B1.05 | Oracle/provider identity, authenticated transport, exact exchange timestamp, HIST/LIVE/disconnect and Doctor; reconcile actual deployment before dependent LIVE claims. |
| R1.2 | B2.03, B2.01, B2.02, B2.04, B2.05, B2.06, B2.07 | Exact cache identity and bounded worker ownership, local calculation, independent scheduling, refresh/retry, capacity then resource and bottleneck measurement. Offline tests may proceed while actual market/device observations are pending. |
| R2.1 | B3.01, B3.02, B3.03, B4.01, B4.02 | T/C and independent O/N/F publisher/source evidence before dependent live quorum. Missing broker trade-side or validated news impact is a source blocker, not license to fabricate direction. Context-only stays non-voting. |
| R2.2 | B3.04, B4.03, B4.04, B4.05, B3.05 | T+C+O contract, five-engine composition, six-box/M contract and then final cross-screen parity. M remains inert until separately validated. Doctor wiring is concurrent with all these changes; B3.05 here is audit closure only. Preserve previous B4.05 offline PASS as scoped evidence, not final acceptance. |
| R3 | B5.04, B5.03, B5.01, B5.02, B5.05 | Persist/restart/session identity, reconnect and bounded recovery, background continuity, alerts based on eligible evidence, final Doctor audit. Doctor changes throughout. |
| R4 | B6.02, B6.03, B6.04, B6.05, B6.01 | Full preflight regression/security, signed candidate APK, physical phone HIST/LIVE acceptance, paper observation/no real orders, final reconciliation of B1–B5 evidence and release. B6.01 is final signoff, not prerequisite to building a test APK. |

Execution vs acceptance: internal source/test gate precedes dependent implementation. Real market, server and device evidence that can only be obtained after a candidate build is a separately tracked acceptance gate, never a circular blocker preventing the test build. Candidate APK is not production acceptance. Where external access, provider capability or market session blocks a required proof, record specific missing evidence and responsible party once; continue independent prerequisite work or explicitly scoped offline work only, do not silently bypass a dependency or repeat completed work. No extra provider calls from Doctor, no unauthorized server/credential/order changes. A running CI allows non-conflicting policy-only updates and read-only preparation, no competing source push. Next eligible execution: reconcile current #539 evidence, then R1.1 source/transport/session prerequisite audit, before remaining engine acceptance. This policy changes sequencing only; no automated scheduler/enforcement or feature completion claimed.


## SMART-4 4X MEGA BATCH (26 Nov 2026, owner approved)
Audit fourfold broader related surfaces before each joint commit. Aim for 4–12 evidenced repairs where safe, not an artificial quota. Keep P01–P16, exact-head CI, no duplicate work, and explicit external blockers. Never weaken source, voting, security or acceptance gates to increase batch size.
