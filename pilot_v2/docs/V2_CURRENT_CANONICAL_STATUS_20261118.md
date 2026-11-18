# BOT KING V2 — CURRENT CANONICAL STATUS & RESUME INDEX
**As of 2026-11-18 | Docs-only snapshot; supersedes earlier "current"/"pending" entries for CURRENT status only.** Historical entries remain unmodified in the append-only Master Journal and Work Log.

## 1. Exact checkpoint
| Field | Current verified state |
|---|---|
| Repository | `vaishnavi596/volume-king` |
| Active branch | `pilot/botking-v2-smart-gateway-20261118` |
| Scope of allowed writes | `pilot_v2/` only. V1 read-only |
| Last **verified executable** SHA | `51da2bef55e6b59d5ab47dffba7d513ed32a6e96` |
| Last **verified executable** Actions | [V2 CI #87](https://github.com/vaishnavi596/volume-king/actions/runs/44368036631), run `44368036631`, **SUCCESS 249/249 Python offline tests**, no failing step |
| Pre-consolidation docs HEAD | `1cf6e0e15de12a5604ed10e80afb9586d9989c1a` (**docs-only**, after CI #86) |
| This documentation snapshot | Docs-only; the latest executable proof is #87, not this journal commit |
| Deployment/device/trading | **V2 not deployed; no V2 APK built/installed or phone acceptance; no real Dhan live data, Oracle production changes, token renewal or live orders** |

**Evidence hierarchy:** SOURCE COMMITTED ≠ CI PASS ≠ Android runtime/visual PASS ≠ authenticated Dhan LIVE verified. Pending at an earlier SHA can have a later verified PASS; use the newest exact-SHA evidence, preserving historical failures.

## 2. Actual app-first migration progress (not a full V1 copy)
| Category | Ported / wired in V2 | Still incomplete / not verified |
|---|---|---|
| V1 look-and-feel | Safe V1 dark/gold palette, compact index/Watchlist/health cards, header + bell/version, some readable typography, three bottom tabs | Exact V1 dashboard/screens, all fonts/padding, chart WebView and Android pixel/interaction acceptance |
| Dashboard indexes | NIFTY / BANKNIFTY / SENSEX independent 1m model and historical/cache-only labels | Real fresh prices, correct 1m signals, continuous data refresh |
| Watchlists | Five locally saved lists, globally ≤70 unique equities (indices separate), 3m row view, local group search, Chart button → 3m Scanner; invalid/removed roster guarded | Real authenticated quote/candle refresh, responsive full V1 controls/device check |
| Scanner & chart | V1 Scanner + chart indicator engines copied to active V2, historic 1m/3m/5m analyses, 15/35/70 local chart bar window, LineChart, native OHLC geometry, selected symbol/timeframe state, Help | V1 full rich chart controls/WebView parity, device rendering, verified LIVE data |
| Super Five | Explicit WAIT for live ranking, historical-only shortlist, safe candidate → 3m chart and Help | Actual verified five-engine live ranking / partial-refresh behavior |
| Options | Selected verified-expiry offline roster, CE/PE strict seven-strike cache, trusted listed spot→ATM±3 normalizer, invalid/replay last-good retention, Help | Actual authenticated Dhan chain, complete expiry/OI/PCR/max pain refresh, equity/options coverage, device check |
| Filters/analysis | Five evidence-gated slots plus sixth blank, HIST/WAIT guards; technical historical indicator summary separately labeled | Full V1 signal panels, truly sourced News/Futures/Options/OI/Candle inputs, bullish/bearish percentages and AI parity |
| Settings/Help Doctor | Device-owned Smart Data preferences, local topic Help, safe Error Doctor cause/next action, contextual Help icons | V1 complete functionality, actual data-only manual refresh/market loop, master authorization UI |
| FT1 login & FT2/FT3 infrastructure | Isolated mock/offline P-256/session/revocation, shared-cache/quote-budget contracts & rate-lane tests | Deployed trusted master + up to 3 delegated session enforcement, token/OAuth read-only gateway, live provider validation |
| Paper/alerts | Old V1 requirements inventoried, live orders intentionally OFF | Safe non-executing paper/alerts/screens migration and regressions |

**Six V1 staging Git blobs match source exactly:** `analysis_quality.py`, `candle_retention.py`, `chart_indicators.py`, `dhan_three_minute.py`, `five_engine.py`, `scanner_engine.py` in `pilot_v2/v1_clean_staging/`; only Chart Indicators & Scanner Engine are also present in active V2 `android_app/src/` at earlier audit. This does not prove other modules are wired into app. See [Migration Manifest](V2_V1_CLEAN_MIGRATION_MANIFEST.md), [Function Graph](V2_V1_FUNCTION_DEPENDENCY_MAP.md), [Source Parity Audit](V2_V1_SOURCE_PARITY_AUDIT_20261118.md).

## 3. CI trail / resolved errors
| CI | Source commit | Result | Meaning |
|---|---|---|---|
| #71 | `cc722add` | 231/231 PASS | Earlier listed ATM adapter baseline |
| #73–#77 | `d569cf2` through `b30bac2` | FAIL | **One** `OptionEvidenceError` NameError; later fixed, failures retained |
| [#78](https://github.com/vaishnavi596/volume-king/actions/runs/44362040001) | `d1f0560c` | 237/237 PASS | Missing exception import correction |
| [#79](https://github.com/vaishnavi596/volume-king/actions/runs/44362597344) | `431a93d0` | 238/238 PASS | Local Help Doctor UI |
| [#80](https://github.com/vaishnavi596/volume-king/actions/runs/44363192734) | `db9e36a6` | 239/239 PASS | V1 dark/gold Dashboard/Watchlist cards |
| [#81](https://github.com/vaishnavi596/volume-king/actions/runs/44363552011) | `eb83b3d5` | 240/240 PASS | Context Help routing |
| [#82](https://github.com/vaishnavi596/volume-king/actions/runs/44364272154) | `cc70f97f` | 241/241 PASS | Scanner/Options visual Help |
| [#83](https://github.com/vaishnavi596/volume-king/actions/runs/44364734475) | `51a8c574` | 243/244 FAIL | One stale Watchlist source-string assertion, code feature remains |
| [#84](https://github.com/vaishnavi596/volume-king/actions/runs/44365018806) | `09bc354e` | 244/244 PASS | Corrected assertion / Watchlist search |
| [#85](https://github.com/vaishnavi596/volume-king/actions/runs/44365732818) | `ad917cb5` | 245/245 PASS | Historical Super Five to chart |
| [#86](https://github.com/vaishnavi596/volume-king/actions/runs/44366294149) | `8739cb9a` | 246/246 PASS | Watchlist → Scanner 3m button |
| [#87](https://github.com/vaishnavi596/volume-king/actions/runs/44368036631) | `51da2bef` | **249/249 PASS** | Local Scanner 15/35/70 bar history window |

## 4. OWNER rules (authoritative)
- V2 equals V1 **real screens, behaviors, engines** but no old server settings, Angel One, Yahoo, legacy credentials/auth/order paths. Copy only audited UI and local functions to V2; **do not import V1 `src/main.py`** (mixed providers) or old server modules.
- **App-first** product/design/state/filters and smart scheduling. Oracle integration/deploy **LAST** after app functional/CI and planned device build acceptance; server only owns authenticated read-only Dhan token/technical cache/rate-limit transport.
- **70 distinct selected equities total across five lists**, no duplicate; 3 independent indexes. Dhan demand proportional to selection (5 means fetch 5, not 70), shared cache/serialization. Market automatic polling only 09:10–15:45 IST; outside hours freeze except explicit *data-only* manual refresh. Watchlist 3m; index & default Scanner 1m; selected Scanner timeframe permitted 1m/3m/5m. Five actual filters, sixth intentionally empty and excluded from scoring.
- Offline unverified market inputs = **HIST or WAIT**, never fabricate live, bullish/bearish percentages, OI/news/futures votes or orders. Keep last good on incomplete response.
- Target **1 Master + up to 3 delegated devices** (4 total) per latest owner rule; some older prototype code/docs still assume max 3 **including Master**. **OPEN MISMATCH**, do not silently mark corrected or deploy.
- Old V1/production/Oracle/keys/APK unchanged without separate authorized approval; no live orders. New V2 package/version signing/install acceptance pending.
- User `ok` means continue doing real safe work, not just report. Before each V2 code change inspect previous actual commit/files and exact applicable CI; failed CI must be diagnosed/fixed before another unrelated patch. Combine 2–4 related files/tests and journal updates in one atomic commit, verify the same source SHA. Do not build APK early.
- Each live action records source SHA, changed files, test count, CI run/FAIL/PASS/PENDING, Dhan/Oracle/order/APK/device facts and next. The **Work Log & Master Journal preserve history**; do not overwrite failures or call a docs-only SHA an executable PASS.

## 5. Exact next batch (app-first)
1. **FT2 V1 parity inventory / actionable gap list:** read original V1 source *read-only* and current V2 Flet main. Group remaining visual/functional screens (Dashboard panels, actual Scanner chart controls, Super Five live gates, Options selected expiry/update, Paper non-executing, alerts, Settings, Help Doctor) by imports/callbacks, and mark `PORTED / WIRED / CI TESTED / DEVICE VERIFIED` separately. No old provider/system config.
2. **Next safe implementation:** pick coherent 2–4 V2-only UI/local function files + regression; preferably connect remaining selected-symbol chart navigation/option UI controls, then test exact SHA; avoid cosmetic-only pseudo parity.
3. **Then FT1/FT3 app integration:** master login/first bootstrap and Dhan-only read-only evidence/cache/smart refresh UI contracts. Offline tests cannot establish actual Dhan entitlements, expiry token, authenticated transport, 1–4 phones.
4. **Later FT4:** full exact-SHA regression, distinct V2 Android metadata/signing and real phone visual/functional acceptance; only then staged, backup-and-rollback Oracle production integration under explicit approval.

## 6. New chat resume / source of truth
**Read order:** (1) [this current status](V2_CURRENT_CANONICAL_STATUS_20261118.md), (2) [General Framework](V2_GENERAL_FRAMEWORK_RULES.md), (3) [Handoff](V2_HANDOFF.md), (4) [Live Status & Schedule](V2_LIVE_STATUS_AND_SCHEDULE.md), (5) latest actual branch HEAD/Actions, (6) Master Journal + Work Log only for needed history and failures. This snapshot is authoritative *as of the checkpoint above*, but must be checked against newer HEAD/CI each turn. Repo General records = these `pilot_v2/docs/` files; do not claim an actual GitHub Discussions → General post was created.


## V2-FT2-SCANNER-CHART-WINDOW-CI87-VERIFIED-20261118
- Exact [V2 Pilot CI #87](https://github.com/vaishnavi596/volume-king/actions/runs/44368036631), run `44368036631`, source SHA `51da2bef55e6b59d5ab47dffba7d513ed32a6e96`: **SUCCESS 249/249 Python offline tests OK**, no failing step.
- App source: `pilot_v2/android_app/src/main.py`, new `chart_window.py`; test `pilot_v2/tests/test_chart_window.py`. Scanner chart display selects 15/35/70 cached completed historical bars, 35 default; changing dropdown uses local window only, never refreshes quote/candle data, does not change timeframe or produce a LIVE claim.
- Safeguards: strict window choice type/range; completed history, invalid new data retains last-good; five filter+blank sixth, symbol/timeframe, 70 equities and 3 indices unchanged.
- Limit: source CI not Android Flet rendering or authenticated Dhan/Oracle provider integration. No V1, Oracle, Dhan API, orders, APK.
- NEXT: V1→V2 functional parity inventory and grouped local app control wiring, then exact code SHA CI; Oracle production last.
