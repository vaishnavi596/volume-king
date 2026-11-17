# BOT KING — Documentation & Journal Category Index

**Canonical entry point:** This index groups BOT KING reports by purpose, not by date. As-of 2026-11-18. Use the newest evidence in the active journal over historical checkpoints. This index is a navigation/consolidation pass, **not permission to delete historical CI, rollback, auth or test evidence**.

## Workflow: where new evidence must go

| New work / topic | Primary record | Other required evidence |
|---|---|---|
| AI / Smart Engine / memory / research | [AI & Market Intelligence](#ai--market-intelligence) + [Work Log](BOT_KING_WORK_LOG.md) | CI/test matrix for code; no claim of real online/Dhan access until connected |
| Five filters, assessment, Option Chain, futures/news, scalp research | [Filters & Market Evidence](#filters--market-evidence) + [Work Log](BOT_KING_WORK_LOG.md) | [Test Matrix](BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md) |
| Commands, Oracle, server/deploy, Dhan limits | [Commands & Oracle](#commands--oracle-server) + [Work Log](BOT_KING_WORK_LOG.md) | deployment evidence, hashes, backup, safe output |
| Watchlist, Scanner, Super Five, Dashboard, login, UX | [Android & UI](#android--ui) + [Work Log](BOT_KING_WORK_LOG.md) | source/CI vs device outcomes separately |
| CI, regressions, APK, release gate | [Release & Tests](#release--tests) + [Test Matrix](BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md) | exact commit / CI run / release proof |
| Prior incomplete/superseded investigations | [Historical audit library](#historical-audit-library) | cite the exact prior result rather than rerunning it |

**Permanent rules:** [AGENTS.md](../AGENTS.md) and [handoff](../BOT_KING_HANDOFF.md). **Single canonical chronological ledger:** [BOT_KING_WORK_LOG.md](BOT_KING_WORK_LOG.md). **Current tasks/results:** [BOT_KING_WORK_RESULT_TRACKER.md](BOT_KING_WORK_RESULT_TRACKER.md). **T01–T16 tests:** [BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md](BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md). Don't create another general journal.

## Core — ACTIVE (keep)

- [BOT_KING_WORK_LOG.md](BOT_KING_WORK_LOG.md) — append-only dated evidence; historical failures retained.
- [BOT_KING_WORK_RESULT_TRACKER.md](BOT_KING_WORK_RESULT_TRACKER.md) — work status / next step, separate source, Oracle, CI, APK, phone.
- [BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md](BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md) — tests and open integration gates.
- [BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md](BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md) — main product requirement backlog (may contain superseded as-of checkpoints).
- [BOT_KING_RELEASE_GATE_POLICY.md](BOT_KING_RELEASE_GATE_POLICY.md) — must-pass release, safety and signing controls.
- [BOT_KING_EVIDENCE_AND_COMMAND_RUNBOOK_20261116.md](BOT_KING_EVIDENCE_AND_COMMAND_RUNBOOK_20261116.md) — validated historic operator commands and evidence boundaries; check current SHA before reuse.
- [BOT-KING-SIX-BATCH-WORK-REGISTER.md](BOT-KING-SIX-BATCH-WORK-REGISTER.md) — cross-batch work register. Review alongside current status; no duplicate task creation.

## AI & Market Intelligence

**ACTIVE — new feature source:** `src/five_engine.py`, `src/market_memory.py`, `src/market_research_planner.py`; tests `tests/test_market_memory.py`, `tests/test_market_research_planner.py`. Current status: memory source/offline tested; planning future optional Dhan/online research only, *not running an autonomous browser or live Dhan 1–2 year fetch*. See newest [Work Log](BOT_KING_WORK_LOG.md).

**REFERENCE / design to reuse:**
- [B1_FIVE_ENGINE_SHARED_DHAN_AUDIT_20261115.md](B1_FIVE_ENGINE_SHARED_DHAN_AUDIT_20261115.md)
- [BOT_KING_BATCH_4_FOUR_ENGINE_DESIGN.md](BOT_KING_BATCH_4_FOUR_ENGINE_DESIGN.md)
- [BOT_KING_DEFERRED_PIPELINE_20261117.md](BOT_KING_DEFERRED_PIPELINE_20261117.md)

**Policy:** Five current visual assessment filters, separate independent evidence engines, sixth visual slot blank. A historical pattern or internet article must not become a verified Dhan signal or win probability. Build a tested, rate-budgeted coordinator before fetching long periods.

## Filters & Market Evidence

**ACTIVE / REFERENCE:**
- [FILTER_REFRESH_TRACKER_20261115.md](FILTER_REFRESH_TRACKER_20261115.md)
- [B2_DHAN_OPTIONS_AUTO_REFRESH_MULTI_UNDERLYING_20261115.md](B2_DHAN_OPTIONS_AUTO_REFRESH_MULTI_UNDERLYING_20261115.md)
- [BOT_KING_54_SYMBOL_ALL_FIXES_RELEASE_GATE_20261116.md](BOT_KING_54_SYMBOL_ALL_FIXES_RELEASE_GATE_20261116.md)
- [ORACLE_FILTER_AUDIT_02_OPERATOR_GATE_20261116.md](ORACLE_FILTER_AUDIT_02_OPERATOR_GATE_20261116.md) — historical gate; latest Oracle 13/13 HTTP contract and newer cache-only probes are in Work Log.
- [BOT_KING_BATCH4_BENCHMARK_20261114.md](BOT_KING_BATCH4_BENCHMARK_20261114.md)

**Current truth:** Oracle selector-qualified NIFTY 1m and HDFCBANK 3m Assessment were HTTP200 but cache empty. HDFCBANK underlying is mapping-only; real equity expiry/chain entitlement unverified. New intraday bridge is GitHub source+CI only. Do not claim all five filters work or sixth is active.

## Commands & Oracle Server

**ACTIVE / REFERENCE:**
- [BOT_KING_EVIDENCE_AND_COMMAND_RUNBOOK_20261116.md](BOT_KING_EVIDENCE_AND_COMMAND_RUNBOOK_20261116.md)
- [BOT_KING_B3_ORACLE_PARITY_RUNBOOK.md](BOT_KING_B3_ORACLE_PARITY_RUNBOOK.md)
- [BOT_KING_ORACLE_APP_CONTRACT_20261115.md](BOT_KING_ORACLE_APP_CONTRACT_20261115.md)
- [ORACLE_READONLY_DEPENDENCY_GATE.md](ORACLE_READONLY_DEPENDENCY_GATE.md)
- [BOT_KING_REFRESH_DEMAND_INVENTORY_20261116.md](BOT_KING_REFRESH_DEMAND_INVENTORY_20261116.md)
- [server-gateway.md](server-gateway.md)

**Code/scripts:** `scripts/audit_oracle_*readonly.py`, `scripts/stage_oracle_intraday_assessment_bridge_20261118.py`, `scripts/check_127_oracle_readonly.py` (warning: includes broker-dependent POST and must not be casually treated as GET-only), rollback/deploy scripts. Older exact-SHA-pinned deploy scripts are **historical**; must never execute if production SHA has changed.

**Safety:** Oracle deployed source differs from GitHub backend. No secret in GitHub/chat, no unattended deployment, no broker fanout/orders, backup before approved prod edits.

## Android & UI

**ACTIVE / REFERENCE:**
- [botking-mobile-audit-batches-20261115.md](botking-mobile-audit-batches-20261115.md)
- [BOT_KING_2_3_127_JOINT_REPAIR_PROGRAMME_20261116.md](BOT_KING_2_3_127_JOINT_REPAIR_PROGRAMME_20261116.md) — historical version programme; do not infer current APK from filename.
- [A2_CHART_FILTER_OPTIONS_REPORT_20261115.md](A2_CHART_FILTER_OPTIONS_REPORT_20261115.md)
- [A3_DASHBOARD_NATIVE_15_SLOTS_DHAN_AUDIT_20261115.md](A3_DASHBOARD_NATIVE_15_SLOTS_DHAN_AUDIT_20261115.md)
- [BOT-KING-226-ANDROID-KEYSTORE-INTEGRATION.md](BOT-KING-226-ANDROID-KEYSTORE-INTEGRATION.md)
- [BOT-KING-226-DEVICE-ENROLLMENT.md](BOT-KING-226-DEVICE-ENROLLMENT.md)
- [FLET_SECURE_STORAGE_COMPATIBILITY.md](FLET_SECURE_STORAGE_COMPATIBILITY.md)

**Keep recent owner decisions:** index Dashboard 1m, Watchlist candles 3m, Scanner selected timeframe, one phone test, five existing filters plus one blank UI row.

## Release & Tests

**ACTIVE / REFERENCE:**
- [BOT_KING_RELEASE_GATE_POLICY.md](BOT_KING_RELEASE_GATE_POLICY.md)
- [BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md](BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md)
- [BOT_KING_54_SYMBOL_ALL_FIXES_RELEASE_GATE_20261116.md](BOT_KING_54_SYMBOL_ALL_FIXES_RELEASE_GATE_20261116.md)
- [BOT_KING_CI_EIGHT_RUN_PREFLIGHT_20261116.md](BOT_KING_CI_EIGHT_RUN_PREFLIGHT_20261116.md)
- [secure-login-release-gate.md](secure-login-release-gate.md)
- [BOT_KING_BATCH_1_2_3_RELEASE_GATE.md](BOT_KING_BATCH_1_2_3_RELEASE_GATE.md)

**CI status at index creation:** #1840 on planner test SHA `84ec7dfe` SUCCESS, #1838 memory tests SUCCESS, #1836 Oracle bridge generator tests SUCCESS. All are SOURCE/CI, no new APK or on-phone acceptance.

## Historical audit library

These older files are **ARCHIVE CANDIDATES**, not proven safe deletions. They contain historical tests/design/incident details and may still be referenced by handoffs; retain until all inbound references, unique CI hashes, rollback commands and findings have been migrated to canonical category sections.

- [B3_GITHUB_FULL_AUDIT_20261115.md](B3_GITHUB_FULL_AUDIT_20261115.md)
- [B3_JOINT_BATCH_PLAN_20261115.md](B3_JOINT_BATCH_PLAN_20261115.md)
- [B4_PAPER_ORDER_BOT_AUDIT_20261115.md](B4_PAPER_ORDER_BOT_AUDIT_20261115.md)
- [BOT_KING_JOINT_BATCH_GAP_AUDIT_20261116.md](BOT_KING_JOINT_BATCH_GAP_AUDIT_20261116.md)
- [BOT_KING_NEW_CHAT_HANDOFF_20261117.md](BOT_KING_NEW_CHAT_HANDOFF_20261117.md) — older but still useful historical transitions.
- [BOT_KING_PREVIOUS_TWO_CHATS_STEP_BY_STEP_20261114_15.md](BOT_KING_PREVIOUS_TWO_CHATS_STEP_BY_STEP_20261114_15.md)
- [BOT_KING_PROJECT_AUDIT_AND_RELEASE_PLAN.md](BOT_KING_PROJECT_AUDIT_AND_RELEASE_PLAN.md)
- [DHAN_ORACLE_YAHOO_PREBUILD_AUDIT_2026_11_06.md](DHAN_ORACLE_YAHOO_PREBUILD_AUDIT_2026_11_06.md)
- [PREBUILD_UI_AUDIT_2026_11_06.md](PREBUILD_UI_AUDIT_2026_11_06.md)
- [T_UNIFIED_TRADING_JOINT_RELEASE_20261115.md](T_UNIFIED_TRADING_JOINT_RELEASE_20261115.md)
- [audit-v1.8.0.md](audit-v1.8.0.md)
- [audit-v1.9.0.md](audit-v1.9.0.md)
- [audit-v2.0.1.md](audit-v2.0.1.md)
- [BOT-KING-226-MASTER-ROADMAP.md](BOT-KING-226-MASTER-ROADMAP.md)

**Deletion gate:** No permanent removal solely based on age or a subjective 60% usefulness estimate. For each candidate verify no inbound links/source references, preserve unique troubleshooting/CI/test/deployment/rollback provenance in the Work Log or category index, confirm no CI/build dependency, commit an audited deletion manifest and check final CI. Prefer Git history + archive index for superseded prose; remove only explicitly proven redundant text, not security/safety evidence.

## Documentation housekeeping register

| Stage | Status | Meaning |
|---|---|---|
| Inventory 44 docs / 24 scripts | **DONE** | Name/size and current source baseline inspected |
| Category navigation index | **DONE** | One entry point for new chat and category-specific evidence |
| Category routing rule in AGENTS / Handoff | PENDING | Link index at startup, keep one chronological journal |
| Reference/dependency + unique-provenance scan | PENDING | Required before deletion or physical moves |
| Controlled archive/delete batch | NOT STARTED | No deletions without demonstrable non-dependency |
| Current Oracle/app/APK release work | OPEN | Independent of documentation housekeeping |

