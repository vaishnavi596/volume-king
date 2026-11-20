# BOT KING — B1 Closure: Original V1 Clone Baseline + No-Loss Transfer Lock
Date: 2026-11-20
Status: **B1 SOURCE/ARCHITECTURE AUDIT COMPLETE; DEVICE ACCEPTANCE IS A LATER OWNER GATE**
Scope: B1 only, no live Oracle activation, B2–B4 code migration, data claims, build or server writes.

## 1. Verified source identity and complete git tree
- Original base: `fix/botking-joint-audit-70-15-20261115`, GitHub compare base commit `e15c1e146df38ee2d18bd8ab5793f79be54e4074`.
- Exact pure clone: `pilot/v1-pure-original-clone-phone-20261120`; GitHub compare API found branch ahead by four commits and **exactly two changed tracked paths**:
  1. `pyproject.toml`: version-only `2.3.130` → `2.3.132` (1 added, 1 deleted);
  2. `.github/workflows/v1-pure-original-clone-apk.yml`: standalone APK build workflow (new 105-line file).
- **Every other tracked file is unchanged relative to original**. Re-fetched cloned `src/main.py` blob: `2cb4fa2421af117742aa1db3f04ecf22af33a4f8` (7,097 lines), identical to original V1. Re-fetched shared modules: `src/server_feed.py` blob `edad7d59fbd3066abc59a8bb21927d9a77ae3f22`, `src/scanner_engine.py` `fa3ca345c08c7d7f6e60206509eec2277ea560bb`, `src/paper_engine.py` `ae046b0170ddc66829402978d5e21b34889814fc`, `src/dhan_three_minute.py` `a243558dabb91b072e73e6039e70fd0f3e3ba8e8`, `src/shared_assessment_ui.py` `7d2f425a85fd93ed4897805d972aa84163f6c336`. The compare is the authoritative no-loss file proof; these checks are structure/contents, **not live runtime tests**.

## 2. UI/feature preservation map grounded in unchanged original V1
| Surface | Existing original code evidence | B2–B4 must preserve |
|---|---|---|
| Six tabs, dark-gold header/navbar, original components | `src/main.py:5820-5847`, `:5914-5924` | Home, Options, Settings, Scanner, Watchlist, Chart; untouched presentation/layout and navigation |
| Dashboard three indices and Super Five | `:1493-1615`, `:1439-1478` | Existing NIFTY/BANKNIFTY/SENSEX caption, ranking cards, evidence chips, no fake LIVE |
| Watchlist search, add/remove, directional filter, five lists | `:1617-1656`, `:2329-2351` | One canonical on-device selected-symbol store, five lists, 70 global unique equities, de-dup across lists and independent indices |
| Watchlist 3m candle votes, last-good retention | `:4688-4819`, `:1817-1846`, `:6761-6840` | Genuine completed matching 3m candles from 1m source, correct freshness, no 5m substitution |
| Scanner + Chart/WebView timeframe selection | `:4271+`, `:5049+`, `:2352+`, `:2637+` | Keep existing Scanner filters and original chart UI; changing scanner timeframes is B3/B4 owner-locked change, NOT part of B1 |
| Settings/Server URL+Access Key, app preferences, diagnostics | `:4249-4268`, `:748-758` | UI fields and settings/history/backup retained; secrets excluded from saved prefs; B2 auth may preserve the user-friendly experience but must NOT treat old ACS key as P-256 authorization |
| Paper-only ledger/SL/target, risk, five slots | `src/paper_engine.py`, `src/main.py:3694+` | Paper actions, plans and risk guard intact; real broker orders stay disabled |
| Dhan, legacy Angel/Yahoo paths | `:585-618`, `:4254` | No silent removal or real-trading activation without owner authorization |
| Help/Doctor, localization, Settings backup/restore | `:3908+`, `:4238+`, `:5833-5840` | Existing language, local diagnostics, backup semantics; no secret leakage |
| Unsupported original functions | `:4260-4261` | Alerts and Backtest are explicitly NOT CONNECTED in original V1. Do not label as working/live or add a substitute in B1 |

## 3. Oracle audit #9 existing B1 operational gate (already PASS)
Evidence: owner-run `44684424803` and previous `44560073808`, actual SSH job logs retrieved: SSH connected, user opc, V1 service active and local health HTTP=200, Nginx syntax PASS, sudo available. No need to repair SSH gateway or restart V1. V2 already staged (38-file manifest verified, all dependencies available), but service inactive, port 8001 absent, public V2 route HTTP404, private environment absent/unsafe, Master+Pairing not provisioned, HTTPS proxy unverified, signed phone login and live Dhan unverified.

## 4. B2/B3/B4 no-loss integration contract (requirements, NOT implemented)
- **B2**: Implement *separate* V2 authenticated reader adapter that binds to existing UI data models via one controlled app-side switch and avoids dual upstream polling. Reuse existing V2 Auth+Unified Gateway; do not overwrite V1 7,097-line shell with V2's 3-tab pilot or erase existing prefs. Protected V2 Master enrollment, P-256 device signer, Oracle pairing/HTTPS route require explicit owner approval and verified tests; no bypass of V2 auth via legacy ACS.
- **B3**: Keep snapshot source identity, timestamp/freshness and 429 backoff. Critical verified source gap: V2 `pilot_v2/unified_data_pipeline.py` currently supports only quotes/indices; candles in FUTURE_LANES explicitly rejected. Need real validated timestamped 1m→3m source before expecting Watchlist 3m LIVE. Single provider-side quota and multi-device coordination, saved historical display remains HIST.
- **B4**: V2 scanner/super_five/options/assessment lanes also currently unsupported; preserve five domain filter identities `oi_support,oi_resistance,max_pain,pcr,candle_trend` and inert sixth slot; original V1 T/C/N/F/O chips are not equivalent. No LIVE or trade-eligible signals without actual genuine broker freshness and correct expiry/timeframe evidence.
- Any change to original chart/scanner default timeframes, migration of Angel/Yahoo, Master/4-device enrollment or alerts requires its designated later batch and owner-gated requirements. Never add features without an owner requirement.

## 5. B1 pass/fail register
| Gate | Evidence | Conclusion |
|---|---|---|
| Git tree exact parity | GitHub compare response, only 2 metadata/workflow paths | PASS |
| Core six page/component source preserved | Identical blob SHA and existing UI definitions | PASS (source) |
| Watchlist 5 lists, 70 unique, search/3m code retained | Existing original definitions, identical blob | PASS (source) |
| Broker/ACS UI, paper/options/chart/help and settings retained | Identical blob + referenced modules | PASS (source) |
| V1 production isolation | Oracle audit #9 | PASS |
| Prior feature gap inventory and future owners identified | Reviewed prior V1→V2 roadmap + actual V2 quote/indices-only code | PASS |
| V1 clone Android behavior/owner phone comparison | Not supplied as acceptance for all six surfaces | **PENDING OWNER DEVICE GATE**, not a source-defect |
| Production V2 P-256 Master login / candle & filter LIVE | V2 service inactive; gateway source rejects those lanes | **PENDING B2–B4**, not B1 PASS |
| New APK signature/artifact | Workflow code exists; binary success not confirmed here | **NOT CLAIMED** |

## 6. Completion scope / handoff
**B1 engineering/source audit CLOSED**; no missing copied code or required B1 code patch identified, so unnecessary changes were deliberately avoided. User device acceptance remains a distinct release gate; do not represent the six-page runtime as accepted. **Next work B2** only within owner-approved gateway adapter scope; B3 and B4 dependencies are documented, not silently applied. Journal source comparison, tests and user gates. Original V1 and source-only clone remain untouched.
