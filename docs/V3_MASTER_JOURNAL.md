# BOT KING V3 — MASTER JOURNAL & NEXT-CHAT HANDOFF
**Last audited:** 2026-11-21 IST
**Canonical ACTIVE branch:** `pilot/v1-pure-original-clone-phone-20261120`
**App identity:** BOT KING Clone, now called **BOT KING V3** by owner. Git branch retains historic Clone/B3 name; do not confuse it with superseded independent `pilot/botking-v2-smart-gateway-20261118` or V1.
**Document purpose:** SINGLE FIRST READ for every new chat. This document is the current V3 requirements/verified-work/open-work/CI/release register. Long engineering evidence stays in linked historical logs; DO NOT read all journals unless a specific source is needed.
**Status:** B152 combined offline regression PASS; B150 signed APK built, but B151/B152 last-2–4 candle correction NOT included in B150 APK. Final V3 phone acceptance remains OPEN.

## 0. FAST HANDOFF — read this section first
- Owner instruction: "OK" means proceed; batch related fixes/tests, don't stop between microsteps; before changing code inspect **latest relevant changed files**, not old ten commits; log changed paths, exact SHA, CI/job links, PASS/FAIL and why. Never claim a phone feature live merely because unit tests pass.
- Current Clone/V3 branch `pilot/v1-pure-original-clone-phone-20261120`; protected historical V1/older independent V2 untouched. Dhan market source only; Oracle secure SSK/login + token renewal + bounded gateway, app-owned controls/UI. No live trading orders.
- **Latest verified CI:** B152 full B3 offline regression [#44892963937](https://github.com/vaishnavi596/volume-king/actions/runs/44892963937) **SUCCESS**, trigger commit `a6029eb96f06d939e36772e2a5dd939e56a13694`. Prior B151 [#44892667842](https://github.com/vaishnavi596/volume-king/actions/runs/44892667842) **FAILED 1/1503** (missing new `candle_fetched_at` wiped prior fetch time); fixed in `src/candle_retention.py` at `bb4fa821c09d4968b609e90bb9d32e76393839cf`. B150 full regression [#44892201231](https://github.com/vaishnavi596/volume-king/actions/runs/44892201231) **SUCCESS**.
- **Latest verified signed APK:** B150 `SUDHAR 1 SENSEX Full Diagnostic APK 2.3.138 build 150`, [#44892473796](https://github.com/vaishnavi596/volume-king/actions/runs/44892473796) **SUCCESS**, workflow source `1d5927e75e7166f9644ed290ece3e265c70e3ddf`. Artifact ID **14703355087**, name `BOT-KING-SUDHAR-1-OPTION-CONTEXT-DIAGNOSTIC-B149-APK` (artifact label carries B149 despite actual B150 run; do not infer version from filename). Artifact is present and not expired at audit. It predates last 2–4 candle changes.
- **Next execution:** After verifying exact B152 branch code and no newer changes, trigger ONE new signed V3 phone APK workflow for the B152 candle patch; await real SUCCESS + artifact + package/signature checks before recommending install. On phone validate Dhan login, SENSEX explicit diagnostic, index prices/1m candles, Watchlist 3m, Scanner AUTO/manual selected timeframe and all 18 available filters, 54/70 errors-only doctor. Capture sanitized JSON and stage/timing; fix real failures in one batch. Do NOT change V1/Oracle production on an offline test alone.
- **Important:** This file is the canonical **V3** log. Former V2 master branch is an archive of older app work only, and any prior Clone feedback that temporarily lived there is represented here. Updating V2 journal for each V3 fix should STOP: append new V3 work here instead.

## 1. What V3 must do — owner-accepted contract
**Data:** Dhan API only. Oracle does OAuth renewal / authenticated SSK gateway / bounded pacing / technical transport cache; app independently owns Watchlists, timeframes, filters, Smart Control, scan priority and visual state. No Angel One/Yahoo trading/source fallback. Up to four phones, Master access safeguards; no assumptions about unlimited broker calls. A single protected request/response pipe is not proof of Dhan push streaming.

**Universe:** Up to **70 unique equities globally**, across Watchlists without duplicates; three separate indices NIFTY, BANKNIFTY, SENSEX; chosen 5–70 equities should scale requests to selected count, not fixed 70. Test 54 or 73 *instruments* is distinct from 54 or 70 *equities*. Index mapping NIFTY IDX_I/13; BANKNIFTY IDX_I/25; SENSEX BSE_I/51; FINNIFTY optional after three defaults. Picker order NIFTY > BANKNIFTY > SENSEX. Never change mapping by guesswork.

**Timeframe/UI:** Dashboard and main market directional panels default **1m**; Watchlist **3m**; Scanner selection includes 1m/2m/3m/5m and supported 10m/15m/30m/1h. Preserve saved selections. Selected timeframe, provider generation, instrument, expiry and cache must be isolated. Derive 3m from complete source-validated 1m groups where appropriate, never take 5m cache as 1m. Last 2–4 prior overlapping candles may receive corrected OHLCV within same timeframe and series; no fabricated or gapped candles. Quote freshness, candle historical status, UI repaint interval, and broker provider latency are **different clocks**.

**Filters/Engine:** Scanner has **18 supported selectable filters** and retains all saved choices, not old 15-slot truncation. The *five evidence engine chips* and reserved sixth inert display chip are different from those 18 Scanner filters. OI Support, OI Resistance, PCR, Max Pain, candle trend and News have evidence gates. Missing/invalid quote, OI/News or completed history => explicit WAIT/HIST/UNVERIFIED, never a live bullish/bearish vote. Three-move user rule where applicable. No fake Dhan quotes/options or live orders.

**Refresh/UX:** Do not lose green/red candles after page navigation/scroll; never remount whole page or trigger Dhan request simply by scrolling. AUTO scan must remain visible and work after login/resume and respect selected symbol/timeframe and default analysis target **60s** (selector 30/60/120). A target is not a guaranteed complete 70-share fetch cadence; broker pacing still applies. Retry Data, index/equity/Scanner/Watchlist adapters need independently diagnosed route logic. Resume must not wipe verified history or restart entire 51-equity scan; screen-off uninterrupted monitoring is NOT accepted without verified foreground service.

**Doctor/phone test:** Login first, tap `REFRESH DIAGNOSTICS`, then `TEST 54` or `TEST 70`. No stale report before refresh; avoid extra 54/70 live broker fanout. Error-only report: healthy rows summarized as counts; each actual failure includes symbol, timeframe, expiry, source/start, gateway route/status, blocked stage, cache endpoint, error code/class, last good and next action. Specific SENSEX read-only opt-in quote+1m probe after scanner idle; at most one each; positive Dhan result allowed only as **unverified** quote `quote_timestamp=None`, `live_verified=False`. Diagnose News/OI/PCR/Max Pain without inventing active votes.

## 2. Most important user-reported REAL PHONE failures (OPEN until new APK proof)
1. Index: SENSEX price/historical 1m missing or intermittent; NIFTY and BANKNIFTY prices sometimes appear but their red/green candles absent or regress. Source mapping known but Dhan entitlement, request and phone-cache stage still to prove with opt-in SENSEX diagnostic.
2. Watchlist: RELIANCE or other equities showed candle colors, then vanished/reset; after manual Refresh some slowly loaded, sometimes only a single symbol. Need last-good history, source/timeframe isolation and predictable render.
3. Scanner: Auto Scan 30s previously ineffective, user switched BANKNIFTY to RELIANCE and pressed Retry Data but Scan/Filter controls disappeared and scan did not start. Preserve visible AUTO/manual controls and saved symbol/TF.
4. Options/News: OI, PCR, Max Pain and News features at times don't show data or WAIT despite price/candles; separate actual unavailable Dhan/Oracle evidence from broken UI/control adapters. Don't award live votes without verified values.
5. Device UX: scrolling may trigger redundant refresh/rebuild, app can become sluggish; Android inactive/paused/resumed behavior, background monitor and auto mode unexpectedly resetting must be reproduced on phone.
6. Capacity: full 54/70 real cached quote/history/filters on device and end-to-end network latency still NOT verified, despite offline synthetic benchmark.

## 3. Evidence register: implemented, verified and limits
| Work / evidence | Latest verified state | Caveat |
|---|---|---|
| V3 combined offline baseline B150 | [#44892201231](https://github.com/vaishnavi596/volume-king/actions/runs/44892201231) SUCCESS, 1,501 tests | Static/offline; not phone |
| B148→B149 failures | B148 [#44891277801](https://github.com/vaishnavi596/volume-king/actions/runs/44891277801) 5/1501 fail; B149 [#44891989310](https://github.com/vaishnavi596/volume-king/actions/runs/44891989310) 1/1501 fail; old 15 filter, 30s refresh, SENSEX test guards updated | No evidence all live features worked |
| B150 SENSEX safety | Test correction `89c6e2be`; unverified Dhan quote cache guard, quote/history explicit opt-in | Still need live SENSEX provider/phone evidence |
| B150 signed APK | [#44892473796](https://github.com/vaishnavi596/volume-king/actions/runs/44892473796) SUCCESS, artifact ID 14703355087 | Older than B151/B152; phone install unverified |
| B151 last 2–4 historical candle patch | `src/candle_retention.py` commits `6e292b0e`, `c83ed886`; tests `67f86bd2`; [#44892667842](https://github.com/vaishnavi596/volume-king/actions/runs/44892667842) FAIL 1/1503 | Original missing-fetch-time regression |
| B152 fix | `bb4fa821` retains prior `candle_fetched_at` if partial data supplies none; [#44892963937](https://github.com/vaishnavi596/volume-king/actions/runs/44892963937) SUCCESS | Requires a NEW B152 APK to reach phone |
| V3 real-cache maximal Doctor test APK B147 | [#44880661257](https://github.com/vaishnavi596/volume-king/actions/runs/44880661257) SUCCESS, artifact 14697936877; separate `com.botking.v3live.bot_king_v3_doctor` identity | APK build passed; real phone acceptance still open |
| Offline 70-equity first-login benchmark | [#44870140640](https://github.com/vaishnavi596/volume-king/actions/runs/44870140640) SUCCESS; 73 instruments 175.801 ms Python validate/technical/queue/mock | 218 of 730 abstract UI updates rejected by 512-slot queue; NOT phone Flutter render/network |
| Synthetic Android Capacity Lab | 54/73 device experiments recorded in `docs/V3_BUILDING_PHONE_CAPACITY_JOURNAL.md`: 28/218 rejects; reported UI submit-to-manual-ack 875/1299 ms | Synthetic only; no Dhan API or actual options scoring |
| Oracle V1/Clone services / token sync | Prior read-only audit showed services up and clone timer completed | Timer success != verified market data; no live provider access confirmed here |

## 4. Pending priority work and acceptance gates
**P0 — release:** Complete one B152 source-head signed APK with full offline pre-sign gate; verify artifact, Android identity, signing; never label old B150 as B152. Document run ID, commit and result.
**P1 — phone:** Install appropriate distinct V3 test package safely (check signing compatibility); report phone Dhan login, REFRESH DIAGNOSTICS → TEST 54/70; explicit SENSEX full probe. Record start → gateway → cache → UI stage, error-only.
**P1 — Scanner/timeframes:** Test AUTO/manual, selected symbol, 1m Dashboard and 3m Watchlist through navigation/scroll/resume; verify all 18 selected filter preferences, engine sixth inert.
**P1 — missing options/news:** Verify authorized Dhan/Oracle OI/PCR/Max Pain and RSS/news cache independently; missing feed stays WAIT with actual typed reasons.
**P1 — data/capacity:** Validate adaptive 70 unique equity flow, B1 lossless bounded queue (512 cap currently rejects synthetic updates), 2–4 preceding candles and 1m→3m invalidation, cache and real device paint times; no 1s/2s complete data refresh promise.
**P2 — background:** Android screen-off/foreground-service acceptance is pending, don't declare uninterrupted monitoring.
**Safety:** No V1/old V2 branch edits, production/Oracle deploy, real trading, live order placement or secrets shown without explicit scoped requirement and safe checks.

## 5. Journal/file layout — one canonical live entry, old evidence retained
- **READ FIRST / APPEND TO:** `docs/V3_MASTER_JOURNAL.md` (this file; on Clone/V3 branch).
- **Detailed engineering history, consult only for an issue:** `docs/BOT_KING_WORK_LOG.md` (older chronological Clone/V3 work); `docs/CLONE_B2_SSK_GATEWAY_IMPLEMENTATION_20261120.md` (gateway); `docs/BOT_KING_CLONE_DAY_2_SPEED_CAPACITY_JOURNAL_20261121.md` (throughput); `docs/V3_BUILDING_PHONE_CAPACITY_JOURNAL.md` (capacity/doctor B147); `docs/BOT_KING_CLONE_20261120_HANDOFF_CONTINUATION.md` (old B3 baseline).
- **Older independent V2 historical archive:** branch `pilot/botking-v2-smart-gateway-20261118`, `pilot_v2/docs/archive/V2_MASTER_JOURNAL_ARCHIVE_THROUGH_20261121.md`; do not merge its application code into V3 without a separate mandate. V2 history is not V3 test evidence.
- **Rules when writing next:** At top of this file update snapshot/latest verified release link; append dated delta in section 6; exactly what was changed, why, exact file(s), commits, offline CI status, APK artifact/signature, real Android result and unresolved symptoms. Preserve older failures as history. Do not run unnecessary repeated PASS tests. No claim of SUCCESS while queued/in progress.

## 6. Dated V3 change log
### 2026-11-21 — V3 journal normalization / separation from legacy V2
- Audited separate branches and journal inventory, combined cross-chat feedback from older V2 Master reconciliation into this single V3 canonical handoff. Older V2 Master history archived untouched; its detailed entry is **not** authority for current clone release status.
- Source and published build evidence as of audit: B150 signed APK SUCCESS; B152 full regression SUCCESS; B152 corresponding signed phone APK **not yet verified/built**.
- No V3 runtime code changed by this journal normalization. Continue app improvements ONLY on current V3 branch, then record exact CI before APK.

