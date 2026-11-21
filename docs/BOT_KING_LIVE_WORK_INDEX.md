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
- **S1 CI results:** failed [Full #44861408348](https://github.com/vaishnavi596/volume-king/actions/runs/44861408348) and [APK #44861726366](https://github.com/vaishnavi596/volume-king/actions/runs/44861726366) each had 2 stale test assertions of 1438. Corrected related tests at `9feedad3` and `58af5d8c`; verified [Full Regression #44862631496](https://github.com/vaishnavi596/volume-king/actions/runs/44862631496) **1438/1438 PASS** at SHA `4483a4f`. New isolated S1 [APK run #44862873176](https://github.com/vaishnavi596/volume-king/actions/runs/44862873176) at `a2925581`, **SUCCESS (all 1438 tests, signed manifest and artifact verified)**. BuildCode 139, versionName 2.3.138, separate `com.botking.sudhar1` app identity; artifact and phone/Help Doctor acceptance pending.

## SUDHAR 1 S1 — PHONE RESULT 21 NOV 2026 (overrides older source-only gate)

**Phone S1 = FAIL/PARTIAL, not accepted.** Uploaded Help Doctor/Watchlist screenshots of Android v2.3.138 show SENSEX `dhan_index_ltp_batch` response incomplete, SENSEX 1m candle `FeedError`, coverage 53/54 with one SENSEX failure, selected Watchlist bootstrapped only 49/51 HIST, RELIANCE historical B86/S14 and cached Oracle Assessment WAIT, quote timestamp unavailable / NOT VERIFIED LIVE. Do not confuse rendered price with validated live data; no SENSEX source quote fabricated.

Four-gate SUDHAR 1 audit isolated Android source issue: Login Watchlist historical bootstrap previously ran only once per generation, so two missed symbols could never retry. Clone-only Android/test fix commits `0e3665b3`/`52b07b0d` now allow max 3 serialized attempts, >=180s apart and only missing histories, retaining last-good and provider cooldown. This does NOT resolve external SENSEX incomplete quote/candle source or Oracle assessment not-configured status. **Full offline CI for fix [run #44866295899](https://github.com/vaishnavi596/volume-king/actions/runs/44866295899), source `f6a5ec30`: SUCCESS (source-only); no follow-up APK/phone confirmation.** Next inspect exact CI/log, then only if green one staged test APK; separately verify safe read-only redacted Oracle `market_diagnostic` for SENSEX. Main Work Log + Day-2 journal contain the full phone evidence and impact matrix.

## SUDHAR 1 — DYNAMIC SYMBOL/CANDLE CAPACITY RESEARCH (2026-11-21)

Official Dhan Market Quote supports up to 1000 instruments per request at 1 quote request/sec. Current Clone batches **selected equities separately from 3 indices**, Quote poll cadence >=60s, Oracle pacing >=1.05s and Quote cache 20s/complete-index 60s, Android Watchlist visible tick every 2s. **51-equity cold 1m historical bootstrap has 51×1.5s=76.5s minimum deliberate sleeps before network, plus per-symbol latency/cooldown; real cold total and Android render p50/p95 not measured.** 3m Watchlist candle derives from completed 1m and 5m uses independent provider history; no 1–2-second guaranteed 54/70 fresh candle delivery. Compare 10/35/54 total (51 equity+3 indices) and 70 equities+3 indices on device. Full research and assumptions in [Day-2 Journal](BOT_KING_CLONE_DAY_2_SPEED_CAPACITY_JOURNAL_20261121.md) and [Work Log](BOT_KING_WORK_LOG.md). S1 phone 49/51 HIST + SENSEX failure remains unverified/recovery open.

## 3. CURRENT WORK / VERIFIED S1 RELEASE GATE

**S1 SOURCE + FULL OFFLINE TESTS PASS; SIGNED DIAGNOSTIC APK BUILT; PHONE TEST PENDING.**
- Earlier two Actions failures had the same **two stale source-string assertions**, corrected in `tests/test_clone_b3_combined_scanner_pacing.py` and `tests/test_watchlist_refresh_regression.py`, preserving two-cache clear and all three generation-scoped 3m Assessment gates. Prior red runs [#44861408348](https://github.com/vaishnavi596/volume-king/actions/runs/44861408348) and [#44861726366](https://github.com/vaishnavi596/volume-king/actions/runs/44861726366) remain historical FAIL.
- **Full regression:** [Actions #44862631496](https://github.com/vaishnavi596/volume-king/actions/runs/44862631496) **SUCCESS** at `4483a4f`.
- **Signed S1 phone-test APK:** [Actions #44862873176](https://github.com/vaishnavi596/volume-king/actions/runs/44862873176) **SUCCESS** at `a2925581`: **1438 tests PASS** within APK gate, buildCode 139, versionName 2.3.138, **separate package** `com.botking.sudhar1.bot_king_v1_pure_clone`, label `BOT KING SUDHAR 1 S1 TEST`, artifact `BOT-KING-SUDHAR-1-S1-DIAGNOSTIC-B139-APK` (ID 14690089703), APK SHA256 `2cabb504aed38be778e5cc68a4f690fc0f48787cf08bddae0cc4aa1b7c082712`. Full evidence in [Work Log](BOT_KING_WORK_LOG.md).
- The redundant S1 build [#44863738181](https://github.com/vaishnavi596/volume-king/actions/runs/44863738181) also **SUCCESS** with 1438 tests PASS; SHA `8de48fa3`, artifact `14691316708`, APK SHA256 `5eed2b37e8a826887ce843e139aff737a1cb00c679ab7172894d9525c90504f2`. **Use the earlier run #44862873176 for phone baseline** (its APK hash is listed above); don't mix the two APK artifacts or trigger another build.
- **Phone installation/Help Doctor 3m candles, actual live Dhan quotes, performance/CPU/RAM and Oracle deployed service checks remain PENDING**; no production/V1 change. S2 queue integration is not yet deployed.

## 4. NEXT SAFE ACTIONS — in order, no unnecessary repeated builds

1. Use the **already successful** [S1 test APK artifact](https://github.com/vaishnavi596/volume-king/actions/runs/44862873176) for phone installation (separate package). Verify checksum if downloaded; test Watchlist quote-only repaint, 3m bullish/bearish and five filters, Search/Scanner/Dashboard/Super Five, Options, Chart, and capture Help Doctor screenshot/timing. Any failure belongs to S1 joint repair.
2. Inspect the redundant run #44863738181 and record terminal result; **do not trigger a third duplicate**. Preserve exact source SHA/artifact identity for each variant.
3. Only after S1 phone evidence is reconciled, begin **S2** bounded phone Data Stock/Smart Apply Queue with impact mapping, CPU/RAM/frame budget, 5/20/40/70 equities and 1–4 devices. Source-only prototype is not production-wired.
4. Oracle-only fixes if separately verified, backup/gate; old V1 untouched and live broker orders OFF.

## 5. JOURNAL ROUTING / ARCHIVE HYGIENE

| Record | Purpose |
|---|---|
| [AGENTS.md](../AGENTS.md) | Permanent SUDHAR 1 and release/segment laws |
| [Main Work Log](BOT_KING_WORK_LOG.md) | **Single append-only chronological evidence ledger**, including old FAIL/PASS/rollback |
| [Day-2 task journal](BOT_KING_CLONE_DAY_2_SPEED_CAPACITY_JOURNAL_20261121.md) | Detailed app/pipe/cache capacity and S1/S2 impact matrix |
| [Clone B2/B3 Journal](CLONE_B2_SSK_GATEWAY_IMPLEMENTATION_20261120.md) | Prior gateway and original B3 evidence |
| [Documentation Index](README.md) | Topic routing; do not create duplicate journals |

**Historical index preservation:** The previous long Live Index (old V2/FT-1 “CURRENT” headings and all old snapshots) remains fully recoverable in [Git history at 542468d](https://github.com/vaishnavi596/volume-king/blob/542468d888d9badc97f520941b56f8236163ea1b/docs/BOT_KING_LIVE_WORK_INDEX.md). It was trimmed from this **current** view, not rewritten as false current status. For a detail absent from canonical Work Log, read that archived revision. Source-only journal cleanup ≠ CI PASS/APK/phone proof.
