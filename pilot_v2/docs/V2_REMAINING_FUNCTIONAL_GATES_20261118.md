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
