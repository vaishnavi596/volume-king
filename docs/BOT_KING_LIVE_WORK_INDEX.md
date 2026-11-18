# BOT KING — LIVE WORK INDEX (नया चैट शुरू करने के लिए)

**Updated (IST):** 2026-11-18 (after #1853 failure triage) · **Branch:** `fix/botking-joint-audit-70-15-20261115` · **Purpose:** 2-minute current/previous/next handoff. This is a *navigation/status pointer*, **not** a replacement for the append-only evidence journal or category index.

## Read this first in every new chat

1. This file: **what happened last, what is live, what is next**.
2. [Category Index](README.md): find files by AI / Filters / Commands-Oracle / Android / CI-Release / Archives.
3. [Permanent Rules](../AGENTS.md) and [Handoff](../BOT_KING_HANDOFF.md): operational safety, OK = advance work, source vs deployment proof.
4. [Work Log](BOT_KING_WORK_LOG.md) and [Test Matrix](BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md): only if exact SHA, command, failed test or regression details are required.
5. [Work Result Tracker](BOT_KING_WORK_RESULT_TRACKER.md): wider workstream history, not automatically latest.

**Rule:** Verify GitHub branch HEAD and recent relevant CI every new session. This index is an as-of snapshot and is not proof of changes made after its date.

## 1. Previous work / पिछले चैट में क्या हुआ

| Date / topic | What actually happened | Evidence & boundary |
|---|---|---|
| 18 Nov — documentation cleanup | Inventoried original 44 `docs/` files and 24 scripts; created [Category Index](README.md), tagged single Work Log policy. Audited 14 historical archive candidates; full repo reference scan. Removed only two superseded historical Markdown reports A3 and A2 after preserving exact original Git-history links and important findings in category index | A3 deletion [`fe730700`](https://github.com/vaishnavi596/volume-king/commit/fe730700eab3179838eb841e4bca3bf57d42456c), A2 [`54761833`](https://github.com/vaishnavi596/volume-king/commit/547618333953abf8a799c84841cecc822e386086). Post-prune [#1846](https://github.com/vaishnavi596/volume-king/actions/runs/44163895968) **1220/1220 offline PASS**, 0 broken relative links. At close: 43 docs including Category Index. |
| 18 Nov — T09 first Oracle bridge candidate | GitHub SHA-locked staged publisher; Oracle operator staged `/tmp/botking-t09-candidate-2sv4fdqt/server.py` from source SHA256 `c9ee8a8d1baa8ebea8efc41d3ee4c6b42aea48f4add65ab79b9518a9fcb27bac`; candidate SHA256 `53f8b74522ad9c61bfee7059a4735e961dcaec298deb7a4bbdaf7fc9965d0a6e`. Static review PASS, four wrapped responses; no production change | **HOLD — DO NOT DEPLOY.** Real Oracle source audits exposed missing metadata and wrong lexical binding; static PASS did **not** certify runtime. No Dhan calls, orders or restart |
| 18 Nov — T09 root causes proved | Canonical candle publisher sends `bars,observed_at,interval,freshness,signal_eligible`; original stager sent only `bars`. Canonical uses route-local relative/absolute fallback imports `assessment_state.publish`, `assessment_scope.current_scope`; staged helper resolves these as globals. Canonical freshness literal `historical_unverified`, eligibility literal `False`, observation from cached `entry.get("observed_at")` | Actual operator AST/symtable reports: `BOT_KING_T09_BINDING_AND_PAYLOAD_REVIEW`, `T09_CANONICAL_IMPORT_METADATA`, `BOT_KING_T09_FINAL_BINDING`; recorded in Work Log. Potential NameError hidden by broad catch, **not proof it happened live** |
| 18 Nov — T09 safety guard committed | Old GitHub staging generator now rejects missing canonical payload fields and route-local import mismatch, with synthetic regression tests | [Payload gate `e080146f`](https://github.com/vaishnavi596/volume-king/commit/e080146ff3c310ded0a1917896fb1b7711a0ccd4), [binding gate `8cfc6c44`](https://github.com/vaishnavi596/volume-king/commit/8cfc6c4450aa95d58992d2d497a1423090f6684d), tests [`473936eb`](https://github.com/vaishnavi596/volume-king/commit/473936ebe4b27e7d43e9e5cc9c36e62be58c4dfc). CI #1850/#1851 and #1852 SUCCESS; **#1853 FAILED** on one fixture newline-escape assertion (not Oracle runtime). Corrective test commit [`86e7fcea`](https://github.com/vaishnavi596/volume-king/commit/86e7fceaf5a025ff3dffed0fcec190e56b09080c); CI of correction pending verification |
| 18 Nov — market research (previous workstream) | `src/market_memory.py`, `src/market_research_planner.py` and synthetic tests created to support bounded historical reasoning and on-demand lookup *planning* | CI #1838 and #1840 SUCCESS; no autonomous real long-period Dhan/online fetching wired or verified |

## 2. Current work / अभी कहाँ हैं

**ACTIVE PRIORITY — T09 Oracle Dhan intraday -> Assessment candle cache integration.**

- **Current disposition:** `HOLD` for **old staged candidate**, not approved for production. Existing Dhan endpoint may respond successfully while Assessment publishing silently fails if route-local imports are absent or metadata is incomplete.
- **Verified:** Original `cached_candles` quality guard and publisher have existing five-key payload; source/version pinned; operator has completed static source and binding audits. GitHub pure offline safeguards; no real deployed integration success.
- **Not verified:** Valid normalized 1m/3m/5m rows including completed bars from actual Oracle payload; legitimate historical `observed_at` for `dhan_intraday` (not present in six-field response); Assessment state publish/read key parity by authenticated in-process test; correct guarded local imports in a replacement; effect on six UI slots (five present, sixth blank).
- **Boundary:** `production_changed=false`, no confirmed Oracle deployment, no Dhan requests or orders from these audits, no signed APK, no device acceptance.
- **Current GitHub CI baseline:** #1851 SUCCESS; [#1852](https://github.com/vaishnavi596/volume-king/actions/runs/44214301891) SUCCESS; [#1853](https://github.com/vaishnavi596/volume-king/actions/runs/44214329322) **FAILED** (1 test fixture error out of 1228), fixed at `86e7fcea`, **new CI not yet confirmed**. **Verify final exact outcomes before coding.**

## 3. Next actions / आगे क्या करें — in order

| Priority | Next safe action | Gate / definition of done |
|---|---|---|
| **P0 / now** | Check last relevant T09 CI #1852/#1853 and exact HEAD; diagnose if failures | Exact run/commit terminal outcome recorded in Work Log, no phantom PASS |
| **P0 / next** | Resolve real Oracle `observed_at` from history cache, canonical normalization/bar quality, assessment `publish/read` key; use one compact *read-only, sanitized* audit. Do not invent timestamp or live eligibility | Compatible source contract known for all four route branches and cached 1m/3m/5m |
| **P0 / next** | Build **new isolated** SHA-locked T09 candidate (never reuse bad `/tmp` candidate) with canonical imports, five-field payload, proper freshness/age policy; add focused synthetic and protected in-process regressions | Exact SHA, no hidden errors, no extra Dhan fanout, compare safe diff; no production mutation |
| **P0 / gated** | Only after tests/backup/explicit operator approval: authorized Oracle deployment and protected HTTP/data health checks | Distinguish live route/collector proof from GitHub CI. No live order routes |
| **P1** | Verify all five existing Assessment evidence/filter results, independently gated News/Futures/Options, equity expiry/chain entitlement, 51+3 refresh and 70-equity mapping | Unverified sources => WAIT. Sixth visual slot intentionally blank |
| **P2** | Android Watchlist/Scanner/Super Five candle consistency, refresh cadence, versionName/versionCode + signed APK after release regression; one-phone validation | Source CI ≠ APK ≠ mobile PASS. No premature build |

**No repeated audit without reason:** if a prior pass is complete for exact SHA/environment, reuse its evidence. Prefer 2–4 coherent changes and one final regression run. Before new edits inspect 3 directly relevant changed files plus associated CI (latest `AGENTS.md` rule).

## 4. Quick category routing / किस जगह रिकॉर्ड करें

| Work category | Write evidence to | Find detail |
|---|---|---|
| AI / historical research | Single tagged `[AI]` entry in [Work Log](BOT_KING_WORK_LOG.md) | [Category Index](README.md), tests/source |
| Five filters / Dhan assessment | `[FILTER]` in Work Log | [Test Matrix](BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md) |
| Oracle commands / server | `[COMMAND/ORACLE]` in Work Log | [Command Runbook](BOT_KING_EVIDENCE_AND_COMMAND_RUNBOOK_20261116.md), source SHA |
| Android / Watchlist / Scanner | `[ANDROID]` in Work Log | [Repair Programme](BOT_KING_2_3_127_JOINT_REPAIR_PROGRAMME_20261116.md), tracker |
| Tests / CI / APK | `[CI/RELEASE]` in Work Log | [Test Matrix](BOT_KING_CONSOLIDATED_TEST_MATRIX_20261117.md), exact GitHub Actions |
| Index / archive hygiene | `[DOCS]` in Work Log | [Category Index](README.md) |

## 5. Updating this Live Index — mandatory minimal protocol

After any **material** milestone (new successful/failed CI, code repair, operator audit, deployment gate, APK/mobile evidence, actual hold/next action):

1. Update **only** the `Previous work`, `Current work`, `Next actions`, and exact CI as-of lines affected. Move completed work into a short dated row; never erase unresolved blockers or claim pending work complete.
2. Append a full evidence-based entry in the **one canonical** [Work Log](BOT_KING_WORK_LOG.md), exact SHA/run IDs, no secrets. Keep this index **short** (roughly 1–3 screens) by consolidating old resolved rows into Category Index / Handoff rather than growing a second 100KB journal.
3. Verify links and status; preserve historical Git commits and prior failures. A new chat reads **this first** before opening lengthy journals.
4. If operator report is pasted in chat but not yet independently validated in repo/CI, label it **OPERATOR-REPORTED** and say what remains unverified. Never invent asynchronous work.

**New chat first prompt (optional):** “BOT KING जारी रखें। पहले `docs/BOT_KING_LIVE_WORK_INDEX.md`, `AGENTS.md` और latest CI पढ़ें; फिर P0 का अगला सुरक्षित काम करके journal तथा index अपडेट करें।”
