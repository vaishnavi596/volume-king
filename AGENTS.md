# BOT KING — Permanent Working Rules (cross-chat)

**Applies to:** BOT KING development on `vaishnavi596/volume-king`. On every new chat, read this file, `BOT_KING_HANDOFF.md`, `docs/BOT_KING_WORK_LOG.md`, `docs/BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md`, and the work-result tracker before new edits. Check the actual current branch/HEAD; historical snapshots may be stale.

## Meaning of "OK" and work continuity
- User's **"OK", "ok", "ओके" means continue to the next safe work item**, not stop after giving a status report. Proceed with available GitHub tools and evidence; do not repeatedly ask permission for routine read-only audits, tests, and reversible source changes already authorized.
- Report briefly what was actually completed and what is still blocked; continue into the next related job **within the active turn** when feasible. Never claim work continues after the turn or in the background without a real scheduled automation/CI job.
- Stop for required authorization when credentials, destructive actions, production deployment/restart, live order execution, or user phone actions are involved. Do not promise impossible unattended work.

## Fast, consolidated audit → repair → test loop
1. **Before each edit batch:** review latest **10 commits and 10 CI runs**, compare recent changes and errors, inspect target files and existing tests. Distinguish current failures from older historical failures and cancelled superseded runs.
2. **Consolidated test intake:** collect outstanding test evidence in the T01–T16 matrix. Group root causes across bootstrap, LTP/index, Watchlist 3m/candle retention, scanner/Super Five, five evidence engines, option chain, Oracle/Dhan throttling, lifecycle and release. Identify missing coverage, unintended regressions and opportunities for improvement.
3. **Work concurrently where independent:** allow CI jobs, read-only audits, and tests on disjoint components to overlap. **Never edit the same file concurrently** or run competing broker-history lanes; serialize shared-cache, provider, and production changes. Avoid uncontrolled CI run storms; monitor and reuse results rather than deleting history.
4. **Batch coherent repairs:** aim for 2–4 closely related changes at a time with targeted tests, rather than dozens of speculative commits. Apply fixes only after diagnosing causes; if a test fails, inspect exact job/step/log, repair, rerun affected tests, then run final joint regression. Do not patch tests merely to hide real failures.
5. **Evidence ladder:** distinguish `source reviewed`, `offline tested`, `CI PASS at exact SHA`, `Oracle production verified`, `APK built/signed`, and `phone/live market verified`. Never infer a later gate from an earlier one. Record PASS/FAIL/PENDING/BLOCKED, commit SHA, run ID, and outstanding issue.
6. **Continuous improvement:** check missing cases, performance, mobile-data budget, security, false signals, UI readability, and risk of regressions as part of each grouped audit. Aim to improve signal reliability and correctness; **never promise a win-rate or accuracy percentage without a defined backtest and out-of-sample evidence**.
7. **Journal every batch:** append to `docs/BOT_KING_WORK_LOG.md`; update matrix/tracker/handoff with actual evidence, unresolved problems, rollback notes, and next actionable task. Keep historical failures and fixes, do not retroactively relabel PENDING as PASS.
8. **Release gate:** no new signed APK until required source tests and final joint regression PASS on release SHA, critical integration checks are verified or explicitly identified as blocked, and versionCode/versionName/UI version bumped. Then build APK, verify artifact/signature, and ask user to test on phone in live market. Mobile validation remains a separate gate.

## Non-negotiable app constraints
- Dhan-only read-only market-data mode; no silent Yahoo/Angel fallback and **no live orders**. Protect secrets, authentication, and broker limits.
- Poll during 09:10–15:45 IST only, apart from explicit after-hours manual data refresh; no full-page refresh/countdown. Shared throttling/cooldowns, cache reuse, last-good quote/candle/votes retained on partial errors, correct stale/unverified labels.
- Watchlist candle 3m, dashboard indices 1m, scanner selected interval/default 1m; keep Super Five/other timeframe semantics explicit. Never relabel 5m as 3m or flood 51 equities with simultaneous 1m requests.
- Five existing evidence engines and five assessment filters must not be silently replaced by **deferred 17-filter research**. WAIT is valid when source evidence is missing; never fabricate bullish/bearish percentages or verified-live status.
- Oracle production edits require backup, preflight, safe restart, health/auth/API postflight and rollback. Phone tests and production deployment must not be claimed without actual access and outputs.

## Restart checklist for a new chat
1. Read these rules and latest handoff/journal/matrix; get current GitHub branch, last 10 commits, last 10 runs.
2. Continue the **next unblocked** test/repair from the matrix; if CI is running, perform independent safe audit rather than stopping.
3. Work through grouped fixes, validate and journal. Say concisely what changed, links to commits/runs, and which gates remain.

## Parallel test-and-fix pipeline (continuous integration)
- A test run is immutable evidence for its own commit SHA. A completed PASS can be recorded immediately, while unrelated tests continue. A FAIL can enter the repair queue immediately after exact failed step/log/root-cause review; do not wait for all other tests to finish unless changes share code or caches.
- Keep three logical lanes: **Test lane** (GitHub CI on pinned SHAs), **Analysis lane** (read-only failures, coverage, risk, history), and **Fix lane** (one controlled writer for the shared branch). Independent CI/audit can overlap; never let multiple writers race on the same file or launch uncontrolled broker requests.
- Prioritize failures by blocker/security/data correctness, then missing coverage, then UI polish. Group failures with the same root cause into 2–4 related changes. Each fix requires a regression test and a new run on its resulting SHA. A previous PASS does not certify a later SHA.
- Maintain a live queue in the consolidated test matrix with **test ID, source SHA, run ID, status, failing step, owner action, fix SHA, retest run, and final gate**. Mark old running results as superseded only after verifying, never delete evidence. Limit CI fanout; use workflow concurrency behavior and resource caps, and avoid changing the release SHA while final joint regression is running.
- After all critical issues are repaired, freeze the release candidate SHA, run the full joint regression, verify integration gates and only then build a signed APK. Real-phone live-market verification remains separate. No autonomous post-turn work is implied unless an actual scheduled automation exists.

## Incremental checkpoints INSIDE a still-running CI job (owner's 5–10 minute OK cadence)
- On each user `OK` while a workflow is running, inspect its **job and step statuses**, not only the final run conclusion. A completed setup/syntax/unit-test step is already usable evidence for that step, but **not** proof that the overall test suite passed.
- If runner exposes intermediate logs or test artifacts, inspect already-emitted failures and completed test cases at 25/50/75% or any available checkpoint. If an actionable failure is proven, patch the relevant source and add regression coverage **on a new SHA**, without cancelling or altering the original in-progress job. Start/reuse CI for new SHA and compare; avoid run storms.
- GitHub Actions does **not guarantee a numerical percent complete** or streaming logs for an unfinished step. Never invent 25%, counts or pass rates. If a single long-running test step provides no partial logs/artifacts, report that precise limitation and use the time for independent code/coverage audit; do not fabricate a fix.
- Record checkpoint time, run/job/step IDs, completed steps, accessible failures, fix SHA, retest run and unavailable evidence in journal/matrix. Every 5–10 minute check requires an actual user turn or configured automation; no autonomous polling after chat ends.
