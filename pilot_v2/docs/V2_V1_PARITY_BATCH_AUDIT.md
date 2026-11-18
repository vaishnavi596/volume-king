# BOT KING V1 → V2 SAME COPY — Source-based Feature Parity Audit
**V2-V1-PARITY-READONLY-SOURCE-INVENTORY-20261118 · read-only V1 reference, V2-only work**

## Grounding
V1 historical READ-ONLY file: `src/main.py` on `fix/botking-joint-audit-70-15-20261115` (never write here). V2 current code: `pilot_v2/android_app/src/main.py`, `app_state.py`, `scanner_state.py`, `smart_data.py` on V2 pilot branch. Source comparison only, NOT live-screen, Dhan or installed APK parity.

| Category | V1 implementation observed | V2 present | V2 gap / batch |
|---|---|---|---|
| Dashboard identity/index cards | Full screen sections, index selection, health navigation, directional vote UI | 3 index symbol labels, 1m history summaries, 5 WAIT filter slots | **FT2-P1** reproduce original card layout, chart/candle colors, signal/filter compact UI; no fabricated data |
| Navigation | Multi-screen Dashboard/Watchlist/Options/Paper/Scanner/Settings functions and tools | Bottom 3 tabs Dashboard/Watchlist/Settings; scanner controls inside dashboard | **FT2-P1** preserve 3-tab preference while making V1 Options/Scanner/Paper/tools accessible inside approved V2 UI with minimum clicks; keep paper non-executing |
| Watchlist | Quotes/candles, dynamic selected symbol refresh, filter vote context | Five local lists, 70 globally unique selection, 3m candle summary and WAIT filters | **FT2-P2** parity of row cards, colored completed candles, batch refresh and selected equity coverage, selection cross-list dedup; investigate user-visible intended 3 vs V2 5 lists without silently deleting stored lists |
| Scanner / charts | Multiple filters, selectable symbol/timeframe, chart JS via Lightweight Charts, historical scanner reports | Symbol + timeframe Dropdown, quote/candle text, no rendered real chart or scan result | **FT2-P3** add chart and source-gated scanner report/navigation, selected-symbol changes update without extra page reload |
| Super Five / analysis | Local cache, ranking/analysis, news context, 2s local revision observation, 5m historical policies | Static "no verified history/ranking" label | **FT2-P3/FT3-P1** source-gated ranking, last-good, percentages only if inputs; no fake live AI |
| Option Chain | Expiry/strike/CE/PE/option rows and diagnostics/refresh; option calls behind provider auth | Expiry Dropdown + validated local metrics summary; no chain/strike table | **FT3-P1** CE/PE/ATM±3/expiry/metrics display, valid index/equity broker capabilities, safe WAIT |
| Five chosen filters + sixth blank | V1 has broader historical scanner filters and directional vote panels (not all equal to V2 selected 5 engines) | V2 five evidence-gated OI-support/resistance/max-pain/PCR/candle trend, blank sixth | **FT3-P1** match owner's selected five evidence engines and display with same compact layout, never map old 10 scanner filters to the five selected engines without audit |
| News/futures/AI | News RSS context, futures/options factor integration and analysis; technical diagnostics | No configured authenticated news/futures producer; FilterEvidence source-gated WAIT | **FT3-P2** exact source/provenance availability, scoring & V1 parity without unsupported live signals |
| Settings / Master | Provider/access key, refresh preferences, Paper slots/controls, System Health/Error Doctor | Smart Data local toggle/interval/version only; "Device access/login not integrated" | **FT1-P1/FT2-P2** app-side Master enable/disable/feed permissions, access-key/session screen, protected bootstrap; preserve diagnostics and visible version |
| Transport & live data | Current V1 reads Dhan behind Oracle, with stale/partial behavior concerns | V2 local quote/evidence inbox, offline HTTPS reader, disabled-by-default auth HTTP shell, no real connection | **FT1-P2/FT3-P3** design source-only app client, later Oracle secure gateway provider verification in OWNER ORDER (app first, server last) |
| Signed installation | Legacy installed APK exists | V2 isolated Flet pyproject metadata and static prebuild gates | **FT4** only after app parity, regression, secure identity and owner approved build; actual V2 signed candidate not built |

## Agreed implementation order
1. **FT1-P1 + FT2-P1 joint UI skeleton parity:** preserve original Dashboard cards, navigation and Master/settings placeholder honesty; keep V2 own settings and 3-tab bottom nav.
2. **FT2-P2:** watchlist/selection, row candles, visible refresh controls and compact diagnostics.
3. **FT2-P3 + FT3-P1:** scanner/chart, Super Five, Option Chain and five actual evidence-gated filter surfaces.
4. **FT3-P2/P3:** legitimate AI/news/futures/options readiness, data-boundary tests, provider-independent app UI behavior.
5. **FT4:** one combined V1/V2 feature-checklist, Flet runtime/source regression, separately signed V2 candidate with identity inspection, then **Oracle demand-driven integration LAST**.

## Rules and evidence
Do not edit V1 branch/source/journal, no old-app fixes. Current last executable V2 `dcf1db007ad35d3b51ac1e00cd44680ab1666d16` CI #63 run 44343869624 **197/197 PASS**, isolated only. V2 General rules commit `e1be61105c083ef7d4c34d47ca5671f95cd16211` docs only. This inventory is an audit, no code changes, no Dhan market data, Oracle writes/restarts, APK, orders or phone checks. Actual V1/V2 visual parity still needs a device/screen audit before declaring same copy. **NEXT:** one FT1-P1/FT2-P1 bounded V2-only UI batch with tests and exact CI; do not redesign V1 UI.
