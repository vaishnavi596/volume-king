# BOT KING V2 — Remaining V1→V2 Functional Parity Gates (2026-11-18)

**Purpose:** prevent a clean-copy or offline CI PASS from being mislabeled a completed migration. V1 sources read-only; `pilot_v2/` only receives new code. No old Angel One/Yahoo, server settings, credentials, trade execution or fallback.

| V1 domain/connection | Ported into V2 | Actually wired | Latest test grade | Still required to close |
|---|---|---|---|---|
| Dark-gold Dashboard, Watchlist, Help Doctor | Partial | Partial | #87 offline PASS | Exact font/layout/V1 feature parity, Android rendering |
| Five Watchlists, 70 unique equities total | Yes | Yes | #87 offline PASS | Real Dhan data refresh/phone validation |
| Watchlist → Scanner 3m selected symbol | Yes | Yes | #86 PASS | Real data and device interaction |
| Scanner → historical chart (1/3/5m, 15/35/70 bars) | Yes | Yes | #87 PASS | V1 richer WebView/chart control parity |
| Super Five historical shortlist → Scanner 3m | Yes | Yes | #85 PASS | Verified live five-filter ranking, partial updates |
| Shared five-factor evidence on Dashboard/Watchlist/Scanner/Super Five | New pure V2-only view adapter | New coverage labels, existing shared inbox | New exact CI PENDING | Real authenticated evidence and completed engine; no invented scores |
| Sixth filter slot | Intentionally blank | Yes | Existing offline contracts | Keep blank until explicitly changed |
| Options CE/PE selected expiry → ATM±3 | Historical-only adapter | Partial | #87 previous pass | Real selected symbol/expiry Dhan data, PCR/max pain/OI and correct expiry refresh |
| News/Futures/AI/percentages | Partial source contracts | Not live | Not end-to-end | Verified source feeds, cross-symbol scoring and evidence trace |
| Smart Data 09:10–15:45 IST, manual-only after close | Local settings/contracts | No real polling | Offline partial | App data-only refresh, shared provider budget, 0–70 demand, no full-page redraw |
| Master and delegates | Offline auth prototype | Not to actual phone | Offline contracts partial | 1 Master+3 delegated cap correction, real login & revoke, secure Dhan authorization |
| Alerts and safe Paper mode | V1 requirements identified | Not yet | Pending | Local non-executing UI/logic; live order calls remain OFF |
| Separate V2 APK / Oracle | Metadata & offline prototype | NO | No mobile CI | Full regression, signed V2 package, phone acceptance, owner-approved Oracle last |

## Safe migration sequence (do not call completed prematurely)
1. Finish selected-symbol cross-screen local UI and actual V1 screen controls. Maintain a single factor engine per symbol/timeframe; show WAIT for missing evidence.
2. Integrate app-owned local workflow for Options expiry, Scanner, Super Five, Alerts and safe nonexecuting Paper where source dependencies can be isolated from V1 provider code.
3. Integrate 5 evidence-gated filters and data-only Smart Refresh against authenticated read-only contracts; source-disabled News/Futures/Options remain WAIT. Correct P-256 Master + 3 delegate count.
4. Run exact-code-SHA full regression and Android visual validation. Signed V2 APK only after gates; Oracle production backups/deploy/read-only Dhan integration LAST and separately approved.

**At this checkpoint:** prior executable code `51da2bef55e6b59d5ab47dffba7d513ed32a6e96` was [CI #87 249/249 SUCCESS](https://github.com/vaishnavi596/volume-king/actions/runs/44368036631). New shared-factor batch must pass its own exact-SHA CI. No Dhan requests, orders, V1 code or Oracle production changes.

## LATEST CHECKPOINT — CI #88 & V2 Index Chart Navigation
- Verified latest executable source CI **#88 253/253 PASS** at `c8d06b6af35bf8e5d8f335c7455b50c2a55f0b26`, run [44370132223](https://github.com/vaishnavi596/volume-king/actions/runs/44370132223). Shared five-factor WAIT/HIST coverage now connected across Dashboard, Watchlist, Scanner and historical Super Five; no artificial LIVE or sixth filter.
- Next code batch adds local `1m Chart` buttons to NIFTY/BANKNIFTY/SENSEX Dashboard cards, selecting the validated index in existing Scanner. Source `android_app/src/main.py`; tests `tests/test_index_chart_routing.py`. **New exact CI PENDING** until verified.
- Still NOT final complete V1 copy or live operation: remaining V1 UI controls, options/scoring, smart data, Master+3 delegated auth, alerts/Paper safe functions, signed V2 APK and Dhan/Oracle integration must pass separate gates. Old server/Angel/Yahoo/credentials/orders excluded.


## V2 three Dashboard analysis slots — next source CI pending
- Previous exact CI #88 **253/253 PASS** for shared five-factor context; subsequent exact CI #89 **255/255 PASS** for independent Dashboard Index 1m Chart buttons at `ea4233d8c0d2c27a015fb0ba76515bbba45e0ac9`, run 44370643743.
- Read-only V1 `dashboard_index_analysis()` had 3 selectable analysis panels. V2 app now adds **three V2-local independent slots** for selected Watchlist equity or three indexes; V2 device-only persistence, 1m quote/candle/filter context, 1m Scanner navigation, removed-symbol fallback. New `local_analysis_slots.py` with negative/positive tests. Exact new Actions CI still PENDING, not device verified or provider connected.
- Remaining: full V1 layout, alerts, paper-safe UI, full options/News/Futures/AI, Dhan-only authenticated read-only data refresh, master+3 delegated login, package/Android acceptance and Oracle LAST. Details in `V2_REMAINING_FUNCTIONAL_GATES_20261118.md`. No legacy server settings, V1 code, Angel/Yahoo, OAuth, live order or APK changes.

## VERIFIED CI #90 — Current V2 checkpoint
- Exact code SHA `1bbf63cd45e0ef64c9021ffdf2b41ec948f3af81`; [V2 CI #90](https://github.com/vaishnavi596/volume-king/actions/runs/44371437426) **259/259 SUCCESS**. Previous #89 255/255 and #88 253/253 PASS.
- V2 has three separately selected, V2-device-persisted V1-style Dashboard analysis slots for NIFTY/BANKNIFTY/SENSEX or selected Watchlist equities, shared source-gated 1m quote/candle/factor context, and direct 1m Scanner chart navigation. Invalid/removed choices fail closed. This is **offline-only**.
- Remain NOT COMPLETE: V1 exact styling/click paths, full Options/News/Futures/AI five-source engine and real Super Five, Smart Data refresh/last-good live provider, Master + 3 delegated device secure login, paper-only/alerts UI, full Android APK and actual phone verification; Oracle/Dhan production deployment LAST after approval. See canonical snapshot and remaining functional gates. No V1/server-provider/Angel/Yahoo/credentials/orders changes.


## V2 local-only Settings Backup/Restore — new CI pending
- Last exact source CI #90 run `44371437426`, SHA `1bbf63cd45e0ef64c9021ffdf2b41ec948f3af81`, **259/259 PASS** for V1 three Dashboard analysis slots and prior cross-screen filter/index coordination.
- New feature source `local_settings_backup.py`, V2 `main.py` Settings backup export + confirmation-gated restore, and `test_local_settings_backup.py`. Export contains ONLY Watchlists, Scanner, Smart Data and three Analysis Slots. Strict schema validation rejects old V1 server settings, credentials, provider names, secret fields and wrong/removal/duplicate data. Restore remains local to the app and preserves source-gated filter caches. **New exact CI PENDING**, no real phone acceptance yet.
- The still-missing full V1 callable UI and server-last Dhan data/integration gates remain open. No V1, Oracle, Dhan, live orders or signed APK touched.

## CI #91 local backup assertion failure → corrective CI pending
- Run [#91](https://github.com/vaishnavi596/volume-king/actions/runs/44372461992) at source SHA `74ea3c107118da66fdccd480796db935353dedcd`: **262/263 tests passed, one source-string assertion FAIL**, because backup export call is wrapped across lines. The actual strict local preference roundtrip/security tests passed.
- Only test `test_local_settings_backup.py` source assertion corrected to accept real multiline Flet code. No app logic/auth/provider/credentials changed. **New exact CI PENDING**, do not claim PASS until verified. Historical #91 stays FAIL.


## CURRENT V2 source checkpoint: CI #92, 263/263 PASS
- [GitHub Actions #92](https://github.com/vaishnavi596/volume-king/actions/runs/44372838093) exact executable source SHA `2e35e6a4b6182acdab589360e28981e05aa856ae`, **SUCCESS 263/263 Python offline tests**. CI #91 is historical FAIL 262/263 because of a wrapped call assertion and was corrected in #92; no app logic changes in correction.
- Safe local-only Settings Backup/Restore, selected Watchlists, Scanner, Smart Data and 3 Dashboard Analysis slots passed source/functional regression. Earlier #88 cross-screen five-filter coverage, #89 index→1m Scanner and #90 three independent analysis slots remain green. V2-only, no old server settings, broker secrets, Angel/Yahoo, V1 branch/code, Dhan calls, trades, Oracle deployment or APK.
- **NOT FINISHED:** actual V1 feature-complete Android UI, Alerts, safe Paper operations, authenticated Dhan refreshed data, genuine five-factor News/Futures/Options/Candle scoring/real Super Five, complete CE/PE/OI/PCR/Max Pain, Master+3 delegated login, smart refresh and phone/build checks. Do not mark FULL V1→V2 migration complete or LIVE from offline CI.
- NEXT: inspect last executable source SHA #92, then address remaining local UI/functional parity and missing trusted data contracts in V2-only batches, exact new CI, later Android, Oracle LAST.


## V2 PAPER preview-only clean migration — exact CI pending
- Prior source CI #92 `2e35e6a4b6182acdab589360e28981e05aa856ae`, run `44372838093`, 263/263 PASS. Examined V1 `paper_engine.py` read-only: deterministic math/datetime, no networking, provider or order calls. Copied exact pure blob to V2; added `paper_preview.py`, manual risk/stop/target UI to Settings, and `test_paper_preview.py`. **NO BUY/SELL/EXIT order controls or unattended bot enabled**, manual hypothetical calculations only.
- New exact-code CI PENDING; full V1 5-slot Paper Bot/alerts still NOT ported. No V1/old server settings/Angel/Yahoo/Oracle/Dhan OAuth/live order/APK changes. Remaining gates in V2 tracker.


## Verified current CI #93 — 267/267 PASS / migration not yet complete
- [GitHub V2 #93](https://github.com/vaishnavi596/volume-king/actions/runs/44373958095) exact code `29fd2645d3cc5783175fdf5bac33d81a51e24131`, **267/267 offline PASS**. V1 pure deterministic paper engine copied unchanged; Settings now has non-executing manual Paper risk/stop/target preview, with source-security and negative tests. No broker or live orders.
- CI #92 was 263/263 PASS for local preference backup/restore; earlier #91 historical FAIL fixed. Cross-screen five-filter, Index → Scanner, three Dashboard Analysis Slots also green in source regression.
- Still OPEN: V1 actual five-bot paper ledger, alerts/notifications, exact V1 UI/rich chart, complete verified Dhan five-filter/News/Futures/Options/Super Five, smart refresh, Master+3 delegates, Android signed V2 device tests, Oracle production LAST. This is **not full V1→V2 acceptance**. No V1/old provider settings/Angel/Yahoo, Oracle restart, Dhan calls or APK.


## V2 five PAPER planning slots — new CI PENDING
- Prior CI #93 run 44373958095 at SHA `29fd2645d3cc5783175fdf5bac33d81a51e24131`: **267/267 PASS**. New V2-only `local_paper_slots.py`, `test_local_paper_slots.py`, and real Settings UI add five independent local **manual risk preview** slots; no broker orders, positions/fills or automatic paper trading. Exact new code SHA CI PENDING.
- Read-only V1 `src/paper_bot_slots.py` contains legacy settings migration and event ledger; intentionally **not** imported/copied wholesale. Still missing real V1 five-bot safe journal/alerts/UI parity, verified Dhan data/filters, Master+3 device login, complete Android app testing and Oracle last. No V1, Angel/Yahoo, credentials, Dhan/Oracle server, orders or APK changed.


## VERIFIED V2 CI #94 — 270/270 PASS; five local paper-risk slots
- Exact source SHA `27039f8dfb496f8355ef56f17f9a53efb84bfc8a`, [run #94](https://github.com/vaishnavi596/volume-king/actions/runs/44423433609), job SUCCESS **270/270 offline Python unit tests OK**. New app-only `local_paper_slots.py`, Settings dropdown for Bot 1..5, local manual risk preview save/clear, no trade or order, plus strict source/functional regression.
- Previous code #93 267/267 PASS. These are **planning records**, not V1 5 paper bot execution, ledger, or alerts. Full V1 visual/function parity, verified Dhan/Options/News/Futures 5-filter signals, Smart Data, Master+3 delegates, Android phone acceptance and Oracle LAST remain open. V1/old settings/Angel/Yahoo/server/credentials and APK untouched.


## V2 five Paper slot stale-input safety fix — CI pending
- Last verified CI #94 run 44423433609 exact SHA 27039f8dfb496f8355ef56f17f9a53efb84bfc8a **270/270 PASS**. Subsequent V2 source patch invalidates previously calculated manual paper risk preview whenever manual side/numeric input changes; prevents storing a stale calculation in any of five planning slots. New regression added in `test_local_paper_slots.py`; exact current CI PENDING.
- No broker network, V1 server settings, Angel/Yahoo, OAuth, orders or APK changes. Other full V1/Android/live-data gates remain open.


## VERIFIED CI #95 — PAPER PREVIEW STALE-INPUT GUARD — 2026-11-19
- [BOT KING V2 Pilot CI #95](https://github.com/vaishnavi596/volume-king/actions/runs/44424322447), exact source `b3679df967b84591d7cca06c9bfaed5031af8cf4`, **COMPLETED SUCCESS 271/271 Python offline tests OK**, pilot-contract job SUCCESS (2.229s). Previous #94 at `27039f8dfb496f8355ef56f17f9a53efb84bfc8a` was 270/270 PASS.
- V2 Settings side and any manual numeric paper planning input now invalidate `paper_last_preview` so an old calculation cannot be saved as a fresh five-slot planning record. `test_local_paper_slots.py` explicitly tests both callbacks and the save gate. No broker, server, provider or automatic-trading actions added.
- The current V2 local PAPER feature is five independent manual **risk preview** records, NOT V1 full five-slot Paper Bot trading/ledger execution or alerts. Remaining gates: full V1 UI/interactive charts, nonexecuting paper ledger/alerts, authenticated Dhan-only five filters/Options/News/Futures/AI and Super Five, adaptive refresh, Master+3 delegates, V2 Android build/device acceptance and Oracle production LAST with separate approval.
- Scope: only `pilot_v2/`. V1 code, old server settings, Angel One/Yahoo, credentials, Dhan API, Oracle, orders and APK unchanged. Docs-only follow-up is NOT a new executable CI.
