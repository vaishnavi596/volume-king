# BOT KING — LIVE WORK INDEX (नए चैट में सबसे पहले पढ़ें)

**As of:** 2026-11-21 IST · **Repo:** `vaishnavi596/volume-king` · **Active Clone branch:** `pilot/v1-pure-original-clone-phone-20261120`
**Owner codeword:** **SUDHAR 1 (सुधार 1)**. New-chat phrase: **“SUDHAR 1 का नियम और पिछला लॉगबुक पढ़कर उसी हिसाब से आगे बढ़ें।”**

## 1. THREE PERMANENT RULES — mandatory before moving

1. **SUDHAR 1 / BK-4G data+pipe+capacity+impact:** Before a functional patch, verify (a) Dhan SOURCE/data/timestamp/timeframe/freshness, (b) secured two-way Oracle PIPE/schema/cache/rate-limit, (c) mobile bounded DATA STOCK/CACHE/QUEUE, CPU/RAM and actual receive→compute→apply→render ability, (d) direct and indirect downstream IMPACT matrix on all candles, five filters + inert sixth, signals, Watchlist/Scanner/Dashboard/Super Five/Options/Charts/Doctor/paper-bot.
2. **JOINT REPAIR / STEPWISE TEST APK:** Fix upstream and *all actually affected consumers in one coherent segment*, leave verified unaffected code alone; focused tests + one exact-head full offline CI. When phone evidence is needed, **one separate labeled diagnostic Test APK per completed segment** (after green tests), then Help Doctor screenshot/trace + actual phone acceptance. If downstream fails, repair in same segment or HOLD/ROLLBACK; do not proceed after a source-only PASS.
3. **CANONICAL LOGBOOK:** Before work read current HEAD/CI and relevant journal; after every audit, code/test/workflow change, failed/passed test, Oracle action, APK/device result, write timestamp, SHA/run ID, dependencies, evidence, PASS/FAIL/PENDING, issue and next step to [main chronological Work Log](BOT_KING_WORK_LOG.md). Update this brief Live Index and [Day-2 task journal](BOT_KING_CLONE_DAY_2_SPEED_CAPACITY_JOURNAL_20261121.md) only with their own roles. No duplicated full reports; never erase actual historical failures.

**Detailed source of truth:** [AGENTS.md](../AGENTS.md). Keep single-market-source Dhan, secured Oracle technical bridge, settings and filters app-owned, V1 and retired V2 separate, max 70 unique equities and 4 phones, live broker orders OFF. No arbitrary 10-old-commit review; inspect latest directly relevant changed files and dependencies.

## 2. PREVIOUS WORK — exact evidence, not extrapolated runtime proof

- Historic Clone B2/B3: authorized SSK login/gateway, Dhan read-only data/candle/options adapters, index/timeframe fixes and existing offline tests. See [B2/B3 Journal](CLONE_B2_SSK_GATEWAY_IMPLEMENTATION_20261120.md), [handoff](../BOT_KING_HANDOFF.md), [Main Log](BOT_KING_WORK_LOG.md). Earlier offline full regression reported **1424 PASS on an older source/CI SHA only**; it is not proof of latest S1 CI, current Oracle runtime or Phone APK.
- Day-2 SUDHAR 1 audit: Dhan→Oracle→mobile source contracts inspected; Watchlist 2s local UI tick and bounded app-side queue limitations recorded. Prototype `src/clone_day2_apply_queue.py` is isolated and **not wired to production UI**. Dhan/Oracle ingress live latency and Android CPU/render p95 remain unmeasured.
- **S1 scoped app source:** Watchlist quote-only updates skip rebuilding unchanged five-filter chips, assessment and 3m candle UI; new Search/Membership rows invalidate mounted-cell signatures. Relevant commits `24b659be`, `0e9a17fa`; tests supplemented at `8f9b16fd`, `9aa12fde`. No broker or server behavior changed by this patch.
- **S1 CI/APK request:** Existing full regression workflow trigger SHA `40585979`. Existing gated phone-test workflow edited at `1f159b992c0b18338cf2cdc01b8a516f86897073`, diagnostic **buildCode 139**, versionName **2.3.138**, artifact name `BOT-KING-SUDHAR-1-S1-DIAGNOSTIC-B139-APK`. This is workflow/source configuration, **not verified build**.

## 3. CURRENT WORK / BLOCKER — do not silently advance

**S1 = CODE PATCHED; focused/full test on S1 exact SHA = UNKNOWN; CI push-run ID = UNKNOWN; APK artifact = UNKNOWN; phone/Help Doctor = NOT TESTED.**
- GitHub connector commit-associated workflow query filters PR runs and may return no push runs. Empty check status is **not** PASS, FAIL or evidence no workflow started. A real Actions push-run ID/job/terminal result must be verified before declaring S1 tests/build successful or sharing an APK.
- The S1 changes are not proof Watchlist opens rapidly on actual phone. The full mobile capacity and downstream timeframes/filters remain pending. No current Oracle or original V1 runtime deployment was made in this S1 batch.
- Last logged continuation: [Day-2 Journal](BOT_KING_CLONE_DAY_2_SPEED_CAPACITY_JOURNAL_20261121.md); all tasks, code commits, CI visibility blockers and current user rules have chronological entries in [Main Work Log](BOT_KING_WORK_LOG.md).

## 4. NEXT SAFE ACTIONS — in order, no repeated micro-approval

1. Verify actual GitHub Actions full-regression and gated diagnostic S1 build push-runs on source HEAD or pinpoint why no run is available; inspect failed assertion/log and repair all impacted consumers together if red. **No new repeated workflow merely to guess status.**
2. Once exact-head tests PASS, verify signed APK artifact, SHA256, separate app identity/manifest. Install S1 diagnostic APK on phone; inspect 3m candles, five filters, Price-only delta behavior, Search, Scanner, Dashboard, Super Five, Options, Charts and Help Doctor. Record segment-specific screenshot plus safe timings/errors.
3. Close S1 as PHONE PASS only after actual evidence; otherwise fix/rollback inside S1. Then S2: wire bounded Data Stock/Smart Apply Queue with per-control dirty updates and CPU/RAM/frame budget, plus joint regression 5/20/40/70 equities and 1–4 phones. Treat 20–25s bootstrap as a test target, not a promise.
4. If a real server fault is proved, apply backed-up Oracle-only fix and regression without touching V1. Nothing in current source audit proves Dhan/Oracle processing is universally fast or all filters work.

## 5. JOURNAL ROUTING / ARCHIVE HYGIENE

| Record | Purpose |
|---|---|
| [AGENTS.md](../AGENTS.md) | Permanent SUDHAR 1 and release/segment laws |
| [Main Work Log](BOT_KING_WORK_LOG.md) | **Single append-only chronological evidence ledger**, including old FAIL/PASS/rollback |
| [Day-2 task journal](BOT_KING_CLONE_DAY_2_SPEED_CAPACITY_JOURNAL_20261121.md) | Detailed app/pipe/cache capacity and S1/S2 impact matrix |
| [Clone B2/B3 Journal](CLONE_B2_SSK_GATEWAY_IMPLEMENTATION_20261120.md) | Prior gateway and original B3 evidence |
| [Documentation Index](README.md) | Topic routing; do not create duplicate journals |

**Historical index preservation:** The previous long Live Index (old V2/FT-1 “CURRENT” headings and all old snapshots) remains fully recoverable in [Git history at 542468d](https://github.com/vaishnavi596/volume-king/blob/542468d888d9badc97f520941b56f8236163ea1b/docs/BOT_KING_LIVE_WORK_INDEX.md). It was trimmed from this **current** view, not rewritten as false current status. For a detail absent from canonical Work Log, read that archived revision. Source-only journal cleanup ≠ CI PASS/APK/phone proof.
