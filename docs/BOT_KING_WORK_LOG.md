# BOT KING — CONTINUOUS WORK JOURNAL

Use this append-only log for successive batches. Keep the newest entry at the
bottom; preserve evidence and corrections. The quick-start document at repository
root is `BOT_KING_HANDOFF.md`.

## 2026-11-15 — Cross-chat recovery and release candidate

**Baseline:** joint branch HEAD `e587485b02aa1ee57de40eb5547d9f8ca5a144d1`,
project version 2.3.125; installed device version unknown.

**GitHub source:** Previous Paper Bot and multi-engine changes were on joint
branch. Cross-list watchlist uniqueness and total-70 rules updated (commit
`c89368fd`), S18 guarded Oracle staging script committed, master contract saved
(`70ba1475`), joint branch made eligible for APK build (`683ec5c4`).
Closed-session login recovery revised through `ee1d75a4` and version
`2.3.125` committed at `e587485b`.

**Verified tests:**
- Oracle S17 13/13 security/health PASS.
- Oracle OAuth/status 200 authenticated, 51/51 equity quotes available,
  S19 3/3 index quotes available; freshness explicitly unverified.
- GitHub offline `ee1d75a4`: 804/804 PASS
  https://github.com/vaishnavi596/volume-king/actions/runs/43751577312
- Old intermediate attempts `6bf04e9` and `ea22fb2` failed offline tests.
- 2.3.124 APK build PASS
  https://github.com/vaishnavi596/volume-king/actions/runs/43746262145
- 2.3.125 APK build https://github.com/vaishnavi596/volume-king/actions/runs/43751755544
  **in_progress when this entry was made**. Recheck; do not assume final.

**Oracle production:** S15 server patch deployed; S18 watchlist store patch
not deployed. No token rotation, no live orders. No device QA proof for 2.3.125.

**Next actions:** Verify newest APK build and signature; resolve outstanding
Android quote/index/scan visual failures with installed-version evidence;
guardedly stage/deploy S18 WatchlistStore and end-to-end API integrations.

## New batch template

### YYYY-MM-DD — Batch name
- Branch/HEAD/version/installed APK:
- Change/commit/files:
- Offline CI run/result:
- Oracle deployed/backup/health:
- Device test/version:
- Unverified / failed:
- Safety / next three actions:

## 2026-11-16 — Backfilled audit of previous two work chats

- Point-wise evidence audit: `docs/BOT_KING_PREVIOUS_TWO_CHATS_STEP_BY_STEP_20261114_15.md`, 51 numbered checkpoints
  covering 14–15 November prior work and separately labeled current-chat checks.
- Explicit provenance legend [U]/[G]/[A]/[P]/[C]; incomplete transcript
  scope disclosed rather than inventing terminal commands.
- GitHub v2.3.125 run 43751755544 verified **SUCCESS**:
  804 tests, versionName=2.3.125, versionCode=74001, signer verified,
  artifact `volume-king-apk` uploaded (artifact ID 14175849838).
- No Android device verification or Oracle S18 watchlist deployment claimed.
- Next: device quote/index/scan smoke; guarded S18 production parity check;
  note exact latest HEAD and installed version in next batch.

## 2026-11-16 — Phone v2.3.125 watchlist refresh failure and app-only fix

- **User phone:** Installed v2.3.125; Watchlist displayed last-saved RELIANCE ₹1339.70 but user did not observe the expected first-login quote refresh. This is a device FAIL report; do not imply the last saved number must change during a market closure.
- **Oracle evidence from preceding checks:** OAuth authenticated, 51 equity snapshot, and S19 3 index quotes returned HTTP 200. No new Oracle requests or production changes needed for this source fix.
- **Source root-cause candidates confirmed in code:**
  1. Closed-session retry in 2.3.125 stopped when it saw *any old saved quote*, instead of proving a full successful snapshot for the *current login provider generation*. On a failed initial fetch it could strand the Watchlist until market open.
  2. Login snapshot outcome updated `market_status` but did not set visible `watch_batch_status`, leaving Watchlist status stale/inconclusive.
- **Changed:** `5da68b3a` adds current-generation equity success gate and bounded closed-session recovery; `9d94169a` adds expression-based behavior tests and a compact Watchlist quote status; `bd5c2212` routes login success/partial/failure to Watchlist status and last-success attempt clock.
- **CI:** `bd5c2212` offline regression 809/809 PASS:
  https://github.com/vaishnavi596/volume-king/actions/runs/43753705425.
- **Next candidate:** 2.3.126 signed release; verify build, signer, versionCode and artifact separately, then update from installed 2.3.125 **without clearing app storage**.
- **Pending mobile proof:** connect/check Dhan; verify 'Login snapshot' status on Watchlist, open/closed display, index batch, Super Five, rate-cadence at 09:15–15:30 IST and failure/retry. Last-known/unverified must not be described as a live exchange quote.
- **Oracle:** unchanged; watchlist server S18 cross-list restriction remains a separate staged deployment gate. Dhan OAuth and orders unchanged. 

---

## 2026-11-16 — MASTER STATUS RECONCILIATION (documentation only; no new patch)

**Requested scope:** Collate completed/failed/staged Oracle work, GitHub fixes,
installed Android evidence, and the remaining app roadmap in one persistent
handoff. This entry **supersedes older "in progress" notes for the exact runs
below** but does not retroactively change their historic observed state.
Provenance: user-shared command output in prior chats; existing S09–S19
contract / 51-point chat audit; current GitHub Actions verification.

### A. Audit baseline — where to continue

- Repo: `vaishnavi596/volume-king`. Integration branch:
  `fix/botking-joint-audit-70-15-20261115`.
- Pre-documentation application HEAD: `fe2faa97c0158709593462b9293fca6f34257c1d`
  (`pyproject.toml` version `2.3.126`). This documentation-only commit
  changes the branch HEAD; **the tested APK is associated with the prior code
  commit, not the journal commit**.
- Last **user-confirmed installed** APK: `2.3.125`, **with a reported
  Watchlist initial-refresh failure**, not MOBILE PASS. Current installed
  version after this report is not known.
- Key records: `BOT_KING_HANDOFF.md`,
  `docs/BOT_KING_ORACLE_APP_CONTRACT_20261115.md`,
  `docs/BOT_KING_PREVIOUS_TWO_CHATS_STEP_BY_STEP_20261114_15.md`,
  `docs/botking-mobile-audit-batches-20261115.md`.
  The 51-point report is **not a complete transcript export**.
- **Status vocabulary:** VERIFIED SOURCE / CI PASS / BUILD PASS /
  ORACLE DEPLOYED / AUTHORIZED MARKET-DATA PROBED / MOBILE PASS are
  independent. UNVERIFIED or PENDING means *do not infer working*.

### B. Oracle: actually checked or deployed

| ID | Work and evidence | True state |
|---|---|---|
| S09 | Static safety audit reported 27/27; preserve market-data-only and no-order limits | STATIC PASS; not runtime proof |
| S12 | `bot-king.service` and Nginx active, health 200, trading OFF; NSE equity registry 2,785 records; different Oracle-specific `server.py`; old backup inventory/permission audit | SERVER AUDIT PASS at check time; token-maintenance inaccessible files not classified as corrupt |
| S13 | Existing index, legacy quote-batch, snapshot, option expiry/chain paths inventoried; registry/option guards compared | SOURCE INSPECTED; individual route presence not every live response |
| S14 | `/v2/instruments/search` already implemented in `watchlist_api.py`; returns `source=dhan_registry` / `symbols`; registry source staged and adapter contracts aligned | EXISTING ROUTE; do not register duplicate |
| S15 | User output: source/backup/staged hashes and Python syntax PASS; guarded staged `server.py` deployed; service restart + health PASS, no rollback; 1 selected-LTP route and 2 dynamic-option guards. Trading flags unchanged, 0 orders by script | **ORACLE DEPLOYED** (server route patch only) |
| S16 | On-server source inspection: selected batch route count 1, dynamic guards count 2, syntax PASS | STATIC PASS (no separate deployment) |
| S17 | 13/13 unauthenticated security checks: protected routes return 403, no provider requests/orders | SECURITY PASS; **not** authenticated price/option functionality |
| S18-B | User-supplied actual `watchlist_store.py`: `count=5, limit=70` applies **per list**; duplicate rejection only within a list; persistence via atomic replace/rollback | **GLOBAL-70 AND CROSS-LIST UNIQUENESS NOT PROVEN DEPLOYED** |
| S18 patch | `scripts/oracle_s18_watchlist_patch.py` committed with offline tests, but never shown applied to production `watchlist_store.py` | **GITHUB STAGED ONLY; ORACLE DEPLOY PENDING** |
| Emergency probe | `systemctl is-active` active; `GET /health` 200; missing-key `/dhan/status` and `/v2/snapshot` 403, `GET /dhan/index-ltp-batch` 405 (POST-only); sampled log counters zero | EXPECTED METHOD/AUTH; not broker outage |
| Authenticated Dhan status | `GET /dhan/status` HTTP 200, `authenticated=true`, `market_data_configured=true`, `token_source=oauth_consent`, `token_validity=expiry_checked`, `reauthentication_required=false` | **AUTHORIZED STATUS PASS at probe time** |
| Equity snapshot | `GET /v2/snapshot` HTTP 200, source Dhan, 51 quotes, age 79.1s, freshness unverified, error null; RELIANCE/HDFCBANK/TCS keys present | **51/51 QUOTES PRESENT** at probe; not exchange-live certification |
| S19 Index batch | `POST /dhan/index-ltp-batch` HTTP 200, 3/3 (NIFTY 25144.3, BANKNIFTY 61034.1, SENSEX 81592.45), unavailable empty; freshness unverified | **AUTHORIZED INDEX RESPONSE PASS** at probe; numbers are not current live prices |

**Critical Oracle safeguards:** Never copy GitHub `backend/server.py` wholesale
over `/opt/bot-king-server/server.py`—Oracle has extra Assessment/OI and
expiry-cache features. Back up exact files and saved Watchlist JSON, syntax
check, hash-check and health-test before any production edit; preserve
`/etc/bot-king/server.env` / Dhan OAuth, never print keys or tokens, never
rotate credentials to "fix" a UI refresh. `live_orders_enabled=false`.
Older historical timestamped backup for `dhan_feed.py` was **missing** in one
user terminal check; do not claim all backups exist without an exact-path test.

### C. GitHub / Android: finished source, tests and builds

| Work | Evidence | State |
|---|---|---|
| Scanner page/filters/white chart | Saved mobile audits; fixes for Scanner page display, candle symbol/timeframe isolation and local WebView recovery, 10-slot OI filter add/remove/save; existing commits documented in 51-point report | CODE WORK; actual current Android end-to-end acceptance UNVERIFIED |
| 51-equity LTP/last good cache | Snapshot parser, 60s shared clock and last-price retention; authorized Oracle 51 snapshot | SOURCE IMPLEMENTED, ORACLE PROBED; user's v2.3.125 first-login refresh FAIL |
| Index independent price path | Index batch + separate poller, 60s guard and cached last-good retention; S19 3/3 Oracle quote test | ORACLE PROBED / SOURCE IMPLEMENTED; current mobile not proven |
| Dhan registry / selected equities | 2,785 registry records, symbol search, selected-LTP route and 1–70 contract; `cb18300a`, `a1ed56db`, `83749508`, `94dfa56c`, `73378bf0` | CODE + ORACLE S15 ROUTE DEPLOYED; authorized dynamic-equity end-to-end PENDING |
| Five watchlists total 70 | `c89368fd` Android one-symbol-one-list; S18 Oracle staged guard; 797/797 offline tests at prior checkpoint | ANDROID CODE PASS; ORACLE GLOBAL LIMIT PENDING |
| Paper Bot | Five simulated profiles and unified Trading Center retained; no real orders | PAPER CODE PRESENT; full Android entry/exit/P&L and persistence QA PENDING |
| Five-engine scoring | Technical/candle historical calculations; news/futures/options independence and freshness limited | Do not claim 5/5 verified; WAIT on missing evidence |
| 2.3.124 | Run [43746262145](https://github.com/vaishnavi596/volume-king/actions/runs/43746262145) | APK BUILD SUCCESS; not phone PASS |
| Initial 2.3.125 | Run [43751755544](https://github.com/vaishnavi596/volume-king/actions/runs/43751755544): 804/804 tests, `versionName=2.3.125`, `versionCode=74001`, pinned signer, artifact 14175849838 | APK BUILD PASS; **installed** but initial-refresh MOBILE FAIL |
| Failed interim recovery | `6bf04e9` run 43751332247 and `ea22fb2` run 43751541606 | OFFLINE FAIL; superseded, not release heads |
| Corrected closed-login recovery | `4e50d226` index batch fallback; `ee1d75a4` guarded first-load, 804/804 PASS | CODE PASS; first-login mobile still pending |
| v2.3.125 Watchlist root-cause fix | `5da68b3a`: saved price cannot substitute for current-login snapshot success; `9d94169a`: behavioral tests and visible `Quote check`; `bd5c2212`: login success/partial/fail reflected on Watchlist | 809/809 OFFLINE PASS, run [43753705425](https://github.com/vaishnavi596/volume-king/actions/runs/43753705425) |
| **2.3.126 latest verified code build** | Commit `fe2faa97`, run [43753960172](https://github.com/vaishnavi596/volume-king/actions/runs/43753960172); 809/809 tests PASS; `com.botking.bot_king`; `versionName=2.3.126`; `versionCode=74101`; pinned release signer PASS; `volume-king-apk` artifact ID **14177263980** uploaded | **BUILD/SIGN/ARTIFACT PASS**, **MOBILE NOT TESTED** |

The 2.3.126 release APK was created **before this journal-only commit**.
Do not mistake new HEAD documentation changes for a new signed build.
A successful GitHub APK by itself cannot prove that mobile login, quote
polling, scans, charts, Options or Paper Bot work end-to-end.

### D. User reports / confirmed mobile issues (don't erase when CI passes)

1. Earlier APKs displayed some Watchlist equity rates while
   NIFTY/BANKNIFTY/SENSEX lagged or were blank; later individual indexes
   appeared intermittently. This is not proof of permanent mapping failure.
2. v2.3.113: pairing-key header encoding error, Watchlist batch FeedError and
   white Scanner chart during symbol switch. Source safeguards added; Android
   retest needed.
3. v2.3.114: 54-symbol filter audit, 51 analyzed, three failures
   HDFCBANK/HINDUNILVR/NTPC; exact upstream error for those symbols unknown.
   REPORTED mobile issue, not verified repaired on latest phone.
4. v2.3.121 Options: NIFTY expiry/ATM CE window visible; ICICIBANK expiry
   HTTP 422. Broker-listed contract/entitlement and expiry mapping unclear.
5. **Installed v2.3.125**: old RELIANCE ₹1,339.70 displayed; no observed
   fresh Watchlist login check. In a closed market a successful new snapshot
   can return *the same price*, so verify request/result and collected-at age,
   **not** whether number changed.
6. For v2.3.126, no user-supplied installed-version confirmation or
   Watchlist `Quote check` screenshot/result exists in this journal.
7. Super Five, Scanner 5m/1m/15m, index Candle, Watchlist partial errors,
   settings persistence, resume and market-open timing require real device QA.

### E. Agreed rules / do not break in future patches

- First authenticated login (open OR closed): one bounded read-only load of
  latest available equity snapshot, independently loaded 3-index batch, and
  available saved candle/ranking/history for Dashboard/Watchlist/Super Five.
  A previously saved quote is NOT proof that current login fetched a snapshot.
- Closed market: after initial attempt and bounded recovery, pause automatic
  repetitive quote and history requests; still show last-known Dhan prices
  labeled **NOT LIVE / exchange timestamp unverified**.
- Normal session: existing `regular_hours()` checks Monday–Friday 09:15 to
  15:30 IST; Watchlist/equity snapshot and Index poll each independently
  rate-limited (currently 60s); separate candle scan roughly 180s; fast local
  Scanner/Super Five cache refresh paths must stay independent. Do not silently
  change these intervals. Official NSE/BSE holidays/special sessions not
  fully modeled: current weekday/time check alone is not authoritative.
- Preserve valid last-known quote on failed/partial Dhan response. 429
  cooldown, request serialization, bounded selected symbols and no repeated
  51-history fanout.
- Exactly **five** Watchlists with **70 different equities total** and a
  symbol in **one** list only; same rule server-side once S18 deployed.
- Dhan-only market-data provenance, no silent Angel/Yahoo fallback.
  Per-engine News/Futures/Options/Candle percentages need independent sourced,
  symbol-matched, timestamp-checked inputs. Missing data = WAIT, no fabricated
  directional signal. Historical candles must not be labeled verified live.
- App version label visible; signed upgrade must preserve Android package,
  signing identity, old watchlists, paper profiles and local saved settings.
- **PAPER trades only**; live broker order placement OFF. Keep token renewal
  unchanged; no credential exposure or unauthorized live orders.

### F. Remaining tasks and next planned app fixes — ordered, NOT done

**P0 — Before declaring 2.3.126 repaired**
1. **Device upgrade and identity:** Compare installed 2.3.125 → signed
   2.3.126 without uninstalling/clearing data; verify app shows v2.3.126,
   versionCode 74101, same signer/package and saved settings/watchlists.
2. **First login on closed market:** Settings Dhan Connect/Check using
   existing trusted HTTPS endpoint; verify Watchlist `Quote check • Login
   snapshot ...` is SUCCESS/PARTIAL/FAILED, index NIFTY/BANKNIFTY/SENSEX
   last-known prices, 51 equity snapshot and dynamic selected stocks. If
   status reports failure, inspect **sanitized Error Doctor stage/HTTP**,
   not just the price. Protect private pairing key.
3. **Real open-session test:** 09:15+ IST during actual trading session;
   Watchlist equity 60s schedule, independent index poll, resumed
   foreground, 30s manual floor, 429 cooldown, last-price retained on
   error. Do not call price "live verified" absent exchange timestamp.
4. **Scanner + Super Five:** Validate first cached analysis after login,
   independently paced 5m candle pass, fast cached Top 5 display,
   filters 10/10 and Bullish/Bearish continuity, 1m/5m/15m chart switching
   without white WebView, no 51-symbol request storm. Ensure WAIT for
   missing independent evidence.
5. **Android Error Doctor + Health:** report status separately for
   authenticated session, 51 snapshot, 3 indexes, refresh stage, histories,
   options and cached/stale age. A recovered error should not count as active.
   Watchlist timer should show `Market closed • auto-refresh paused`
   once initial load completes, not a fake live countdown.

**P1 — Oracle and actual integration (back up before deploy)**
6. **S18 global-70 server parity:** Verify `watchlist_store.py` currently
   deployed source and persisted data (read-only first), stage/backup both
   Python and Watchlist JSON, run isolated duplicate/cap/persistence tests,
   apply guarded patch only if the production guard is missing, health and
   rollback check; never delete existing symbols automatically.
7. **Dynamic equity:** Authenticated, bounded test of registry search,
   `POST /dhan/selected-ltp-batch` and 1–70 symbol response mapping, empty,
   invalid and partial cases. The S15 route code being installed does not
   prove 70-symbol functional response.
8. **Options/Futures:** Real Dhan-listed expiry/chain (NIFTY,
   BANKNIFTY and legitimately F&O-enabled equities), PCR/Max Pain/OI
   support/resistance and near-ATM ±3 strikes; futures money-flow must use
   verified mapping/independent inputs, not cash LTP guesses. Handle 422,
   409 and 429 safely.
9. **News and five-engine:** Independent sourced fresh News, Futures,
   Options and Candle/Technical scores, coherent 100-point bullish/bearish
   UI, no double-counting technical+candle votes and no 5/5 signals without
   evidence. Scope this after stable quotes/scanner.

**P2 — Release and operating quality**
10. **Market holiday calendar:** Replace weekday-only assumption with
    official NSE/BSE holiday and special-session policies; avoid wrong
    open-market classification, preserve controlled first-login snapshot.
11. **Paper Bot acceptance:** Five profiles, saved parameters, simulated
    entry/exit/P&L/SL/target/protection, background pause/resume and
    settings persistence. Real order route must remain disabled.
12. **Performance/data budget:** fast single-symbol/Top 5 cached checks,
    paced 51-candle history, serialized Dhan requests, bounded network
    payloads and no cross-screen duplicate upstream requests.
13. **Final release gate:** full offline/backend CI, signed APK artifact
    versionCode and certificate match, old-version upgrade compatibility,
    actual Android smoke test and two market scenarios (closed/open).
    Commit a new Work Log entry with evidence/FAIL/PENDING, never invent PASS.

### G. Immediate next actions when user authorizes actual development

1. Read the **latest** Handoff, this journal and 51-point audit; compare
   current branch HEAD and latest CI, installed app version and Oracle S15
   deployed source. Avoid repeating passed diagnostics without reason.
2. Get v2.3.126 **mobile** `Quote check` result and Error Doctor stage
   (without secrets); fix only proven UI/session or transport mismatches.
3. Test open-market independent index/Watchlist/Top5 scan and, as a
   separate guarded production batch, S18 server watchlist parity.
4. After each batch, append exact commands/outputs where available,
   commits, CI run, Android/Oracle status and next tasks to this journal.

**This entry is recordkeeping only:** production/server files, OAuth tokens,
Android source code, APK and broker order configuration were not modified
by writing this journal.


## 2026-11-16 — Canonical full master checklist and journal accuracy audit

- **Baseline:** integration branch `fix/botking-joint-audit-70-15-20261115` was at `2828a9625378b2911e165e2313e33f8879d373cf` before this documentation batch; release source `2.3.126` at `fe2faa97`. Installed phone per user: **2.3.125**, first-login Watchlist refresh not observed; Super Five B/S and Index data on phone unresolved.
- **New canonical checklist:** [`docs/BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md`](BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md) — 12 groups covering Dhan/OAuth, 70 equities & Watchlists, refresh, 54 historical candles, 15 movable filters, Super Five, CE/PE options, Futures OI, News/Five Engines, Paper Bot, UI/diagnostics and release/security. Each row carries source/CI/Oracle/device status and pending gates.
- **Evidence rechecked:** `pyproject.toml` version **2.3.126**; Build APK run [43753960172](https://github.com/vaishnavi596/volume-king/actions/runs/43753960172) **SUCCESS**, 809/809 offline tests, `versionName=2.3.126`, `versionCode=74101`, pinned signing PASS, uploaded artifact `14177263980`. This is **not** proof 2.3.126 installed/phone PASS.
- **Journal correction:** Older 10-slot Scanner filter entry is historically real for an intermediate branch, but **current integration `src/main.py` is `MAX_ACTIVE_FILTERS=15` = 10 defaults + 5 extra**. The 10 historical filter evaluations per symbol are a separate metric. Some old design texts mention five-tab navigation, whereas current source has six pages; user later discussed three bottom tabs. **Layout decision is pending**, not completed. Sources that said 2.3.126 build is pending are superseded by the verified successful build.
- **Other claims demoted/not promoted:** No proven independent live Futures acquisition/OI score, sourced News directional score, full option-eligible multi-underlying near-ATM CE/PE verification or complete five-engine 5/5. S15 Oracle guarded selected-LTP route deployed; **S18 production global-70 cross-list uniqueness patch remains staged only**. Historical 54-symbol/540-filter evaluation does not prove market-live or Android rendering. Paper Bot is simulation with live orders OFF; local execution timing is not broker RTT.
- **Source files modified this batch:** journal/checklist/Handoff documentation only; **no** Android code, Oracle service, Dhan token, production configuration, live trading flag or APK changed; no new release build triggered.
- **Next priorities:** (1) v2.3.126 closed/open market phone acceptance for Login Snapshot, 51+3 rates, Super Five B/S and Error Doctor; (2) authenticated bounded Oracle Options/selected-equity/expiry-chain integration tests, then Futures/News independently; (3) safely back up and deploy S18 WatchlistStore global-70 only after verifying actual deployed source and old saved watchlists.
- **Cross-chat rule:** Every new chat starts with `BOT_KING_HANDOFF.md` **and** the canonical checklist, then this append-only journal; never infer device/production state solely from CI or older summaries.


## 2026-11-16 — Installed v2.3.126 FAIL: joint 2.3.127 repair programme (AUDIT ONLY)

- **User-installed version:** **2.3.126** (supersedes earlier installed 2.3.125 status); **MOBILE FAIL:** user reports no expected automatic data refresh after login, incomplete Super Five filter/Bullish/Bearish outputs, and desired HDFCBANK/multi-underlying Options Chain unverified. The 2.3.126 GitHub Build #641 **SUCCESS** is not mobile PASS.
- **Inspected current app source:** `connect_angel` Dhan Connect/Check requires a usable pairing/session key, clears `server_access` afterward; no evidence app-open automatically reconstructs an authenticated server session. Equity/index/scan polls require `dhan_feed.connected`. The market-open `option_poll` excludes closed-market bootstrap; one selected mutable option metrics dict is not a multi-underlying cache. Super Five 10s local refresh is market-hours-gated and 51+3 historical scan is separate/slow. These are **confirmed code properties and root-cause candidates**, not proven one-to-one explanations for every phone failure.
- **GitHub programme:** `docs/BOT_KING_2_3_127_JOINT_REPAIR_PROGRAMME_20261116.md`, commit `04f7a7f7`, breaks changes into A login/session/bootstrap, B equity/index, C historical/Super Five B/S, D Options/HDFCBANK, E regression/release. Desired first-login behavior is once per new authenticated session whether open or closed, last-known data and separate component statuses, then bounded recovery and closed-market polling stop.
- **Oracle:** only earlier S15 deployment and authenticated 51/3 sample available; no new server write, restart, token/OAuth change, or live trade. S18 global-70 WatchlistStore still not proven deployed.
- **Current work state:** **PLAN SAVED ONLY**; no 2.3.127 app code/CI/build has been completed. Future code work must add behavior-level Flet Android and mocked Oracle tests; prove no double requests/stale-as-live and no non-Dhan fallback. Do not claim PASS from static assertions.


## 2026-11-16 — Batch 127-A implementation checkpoint (in progress, not a mobile PASS)

- **Baseline:** branch `fix/botking-joint-audit-70-15-20261115`, original audited HEAD `6ad4bca31d30be42c23847adbe509599f4da761e`; user-installed mobile APK **2.3.126**: automatic Login/Watchlist Refresh **DEVICE FAIL**, Super Five B/S incomplete. Signed 2.3.126 Build #641 passed but did not certify device function.
- **Files/commits:** `src/login_bootstrap.py` introduced an ephemeral authenticated-generation status model (LOADING, LOADED, PARTIAL, FAILED, COOLDOWN, NO AUTH) with no secrets or trading capabilities, commit `df284b85345cb4f8a25feca73618eafaadd0c005`. `tests/test_login_bootstrap_127.py` added behavioral generation/re-login, partial snapshot, stale result rejection, failed/429/no-auth cases, commit `3c2e18dee548c89e9620c02b03a5689a16cd85f3`. `src/main.py` joined login, batch and index observations to this state, exposed equity/index status in Error Doctor, kept cached prices as unverified, removed the post-login generation bump and immediate duplicate equity retry, commit `32605870a092d0aa5b61f5a77a96ec7f019651ee`.
- **CI:** Regression run [43756794895](https://github.com/vaishnavi596/volume-king/actions/runs/43756794895) **SUCCESS** on test-only commit `3c2e18d`; latest app integration run [43756950572](https://github.com/vaishnavi596/volume-king/actions/runs/43756950572) **IN PROGRESS at this checkpoint**. Do not label integrated source PASS before final outcome.
- **Scope/limits:** No actual Android device smoke test, Oracle authenticated probe or market-session verification was executed in this checkpoint. v2.3.127 is **not built**; `pyproject.toml` still `2.3.126`. No Oracle file edits/restart, credentials or Dhan OAuth changes; live orders remain OFF; read-only data/paper simulation only.
- **Remaining Batch 127-A:** evaluate latest integrated CI failure/success, fix regressions, verify exactly-once per authenticated generation (including session reopen) and index/51 equity independent statuses in mocked end-to-end tests. On process restart with no in-memory pairing key, the app still requires Settings reconnect; no raw pairing key is saved to preferences. Batch 127-B/C/D and signed APK release remain **PENDING**.


## 2026-11-16 — Batch 127-A CI regression repair (source tests updated)

- **Baseline:** Branch fix/botking-joint-audit-70-15-20261115, initial correction checkpoint HEAD `9b39c2bc59b0bf8c9ca68c9d39f7a0fc08641c63`; user phone v2.3.126 continues **DEVICE FAIL** for login auto-refresh. No new APK.
- **Failed integration run:** [43756950572](https://github.com/vaishnavi596/volume-king/actions/runs/43756950572), 812 total tests, 1 FAIL + 1 ERROR. Failure A: `test_watchlist_wiring.test_dhan_connect_keeps_batch_in_new_scan_generation` expected an obsolete second provider-generation bump after the login batch. Failure B: `test_dhan_activation.test_index_login_fallback_is_before_historical_only_and_reuses_prices` required the old `len(login_index_quotes)<3` check rather than new observed-batch deduplication.
- **Fixes committed:** `tests/test_watchlist_wiring.py` commit [52ee985c](https://github.com/vaishnavi596/volume-king/commit/52ee985c7a09c8fc251f4a9dcbeb102c0d66b175) asserts provider-switch generation precedes login bootstrap and cache generation is retained without a second bump. `tests/test_dhan_activation.py` commit [aa6ec9c](https://github.com/vaishnavi596/volume-king/commit/aa6ec9c09964b30ca89d3bcfa2534efe540f5647) asserts a verified index-login batch is reused, otherwise independently forced index bootstrap is scheduled. Other provider validation tests were retained.
- **CI new runs:** [43757353004](https://github.com/vaishnavi596/volume-king/actions/runs/43757353004) and [43757356078](https://github.com/vaishnavi596/volume-king/actions/runs/43757356078) were running/queued when this entry was written; **NOT YET PASS**. The change fixes outdated assertions and does **not** itself establish Android behavior correctness.
- **Oracle / device:** No new authenticated Oracle smoke proof, server modifications, token or credential changes, or mobile test. Paper-only, live orders OFF, read-only Dhan. v2.3.127 versionCode/name not yet advanced; build gated on 127-A/B/C/D.
- **Next:** Check latest CI outcome at the actual tested SHA; fix any new regressions; add behavior-level integration tests for login/open/closed/partial/index request scheduling and stage visibility; only then proceed to Batch 127-B.


## 2026-11-16 — Batch 127-A regression retest result (source/CI, not device)

- **Latest tested app+test commit:** `aa6ec9c09964b30ca89d3bcfa2534efe540f5647`. GitHub [Offline Regression Run 43757356078](https://github.com/vaishnavi596/volume-king/actions/runs/43757356078) **SUCCESS** after both regression adjustments; 812 tests were exercised by this suite (prior failed run confirmed 812; inspect final job logs for exact count before using that as a separate proof). Intermediate run [43757353004](https://github.com/vaishnavi596/volume-king/actions/runs/43757353004) FAILED solely because the second obsolete test remained in that intermediate commit; later run supersedes it.
- **Batch 127-A gate:** GitHub source regression **CI PASS**, mobile first-login/market-open/reopen acceptance **PENDING**. Coordinator has in-memory generation/status and cached-last-known safeguards. Secure persisted session or app-restart auto-authentication **NOT IMPLEMENTED**; without a usable in-memory pairing key, Settings reconnect remains required. User-reported 2.3.126 mobile auto-refresh **FAIL** remains historical fact until v2.3.127 device test.
- **Oracle:** No current authenticated Oracle calls or production changes; no credentials, Dhan OAuth, server restart, order route, signing or APK changes. No signed v2.3.127 artifact.
- **Next:** Batch 127-B independently verify equity (51 + permitted selected) and 3-index refresh with mocked partial/429 and state repaint, then 127-C Super Five/Scanner B-S and 127-D genuine eligible Option Chain; release 127-E gated on all required tests and mobile verification separately.


## 2026-11-16 — Joint 127-C/D initial source patches; PAPER acceptance audit

- **Starting source status:** previous 127-A integration run 43757356078 SUCCESS, 812 tests (CI only); installed 2.3.126 remains **MOBILE FAIL**. Current integration branch `fix/botking-joint-audit-70-15-20261115`.
- **Commit [5e76e390](https://github.com/vaishnavi596/volume-king/commit/5e76e390778adfbe1ddc885d73dcabeeb554f735)**: `src/main.py` Super Five's 10-second completed-candle cache recomputation now runs after market close without making any Dhan requests; provider-switch/login restores saved last-known Top Five ranking immediately as WAIT/historical, without an upstream 51-candle scan. Each authenticated Login initiates one selected mapped Dhan expiry/option-chain load even during closed hours. Existing 3.25s option pacing and regular-hours >=60s polling remain.
- **Commit [82979905](https://github.com/vaishnavi596/volume-king/commit/8297990577b94d8e9c74e31a04b989ec382d41c8)**: Closed-market regression updated to distinguish *local cached recompute* from scheduled quote/index requests. Offline test does not imply mobile PASS.
- **Commit [6e799d52](https://github.com/vaishnavi596/volume-king/commit/6e799d5273d6a4235d0c104a3271fc79c80393ac)**: Session-local, bounded (16 entries), generation/symbol/listed-expiry keyed read-only option evidence store; Super Five can show previous verified-origin Dhan PCR context for a separately selected RELIANCE/HDFCBANK/index symbol without confusing another symbol's metrics. This cache is *display only*, `signal_eligible=false` and freshness unverified, not a Futures/Options directional vote.
- **Commit [f42d554c](https://github.com/vaishnavi596/volume-king/commit/f42d554ce5c6a174161cc3f53bf8d0244559cf6f)**: Regression guards for closed-hour local Super Five, login-selected option startup, contextual isolation, and paper/live separation.
- **B/Oracle reality:** 51 fixed NSE equity quotes and three indexes remain separate paced paths; no new authenticated Oracle proof this batch. Actual RELIANCE/HDFCBANK broker-listed expiries, CE/PE strike premiums/OI, entitlement, 422/409/429 and deployed Oracle source require read-only session-level validation. A mapped symbol alone is NOT proof option availability.
- **Five engines:** Technical/candle can display historical B/S; options show PCR/Max Pain and seven-strike context where returned but no verified directional vote; News headlines require sourced relevant fresh items; Futures contract money flow not implemented. Missing engine data remains WAIT, no invented 100% signals.
- **Paper Bot:** five profile manual-tick simulation, Start/Pause/Stop, paper ledger, SL/target/protection are already in source; the user must select Paper mode, confirm manually verified contract and press Start. It does NOT auto-run on Dhan prices, and must not activate without explicit safe paper instructions. Mobile profile persistence/transaction audit pending; live orders OFF.
- **Tests/releases:** CI on the above commits was RUNNING at journal writing; not declared PASS. No version bump, signed 2.3.127 APK, real broker orders, Oracle modification, backup/restart or credential changes. Release gate 127-E remains blocked until 127-B/C/D verified.


## 2026-11-16 — Joint 127-C/D follow-up: CI correction and CE/PE ΔOI UI

- **Regression diagnosis:** [Run 43757881145](https://github.com/vaishnavi596/volume-king/actions/runs/43757881145) FAILED 1 of 816 tests. The new local-cache test incorrectly rejected *reading* `dhan_feed.connected` although it correctly makes no provider request. This is a test assertion error, not evidence of a new broker request. Commit [a5b41f3a](https://github.com/vaishnavi596/volume-king/commit/a5b41f3ac0080bdede16ae06a573de9e4efb1416) fixes the assertion to prohibit only Dhan batch/intraday/option method calls. [Run 43758042146](https://github.com/vaishnavi596/volume-king/actions/runs/43758042146) **SUCCESS** on that updated test and app source (816 regression tests). Earlier intermediate [43757798492](https://github.com/vaishnavi596/volume-king/actions/runs/43757798492) FAILED before the closed-market test was updated; newer successful runs supersede it.
- **Options CE/PE improvement:** Commit [069ff1b5](https://github.com/vaishnavi596/volume-king/commit/069ff1b50905d9d557945d194265961b45ad4800) adds CE/PE change in open interest (ΔOI = current OI − previous OI) to the ATM ±3 listed strike table. It shows an em dash if previous OI is absent, never invents change, and labels ΔOI as *not traded cash*. Premium/OI/Volume provenance and signal WAIT remain guarded.
- **Tests:** Commit [c4e4cc1d](https://github.com/vaishnavi596/volume-king/commit/c4e4cc1dc9db781001e67d8a725513858243df08) adds CE/PE UI and unavailable-value guards. Runs [43758115969](https://github.com/vaishnavi596/volume-king/actions/runs/43758115969) and [43758145328](https://github.com/vaishnavi596/volume-king/actions/runs/43758145328) were still IN PROGRESS at this journal checkpoint. Do not call the latest change PASS until CI resolves.
- **Release and actual feed:** No signed 2.3.127 APK, no fresh authenticated Oracle RELIANCE/HDFCBANK CE/PE proof, no device verification, no server restart or credential change. Paper Bot manual simulated Start/Pause/Stop remains operational in source; no claim of unattended or live broker execution. Exact API expiry/entitlement and 422/409/429 outcomes await server session evidence.


## 2026-11-16 — Paper state diagnostics and later 127-D CI checkpoints

- **CE/PE columns:** [069ff1b5 CI run 43758115969](https://github.com/vaishnavi596/volume-king/actions/runs/43758115969) **SUCCESS**; [c4e4cc1d CI run 43758145328](https://github.com/vaishnavi596/volume-king/actions/runs/43758145328) **SUCCESS** for added ΔOI/CE/PE guards. Results are offline source/contract tests, **not** Oracle RELIANCE/HDFCBANK option entitlements or actual mobile proof.
- **Paper Bot status:** [32eef099](https://github.com/vaishnavi596/volume-king/commit/32eef0996925c4d3becfb429c895a911e3729d26) exposes Paper Bot `Stopped/Running/Paused` and five-profile manual-tick limitation in Settings/System Health Error Doctor. [9c3539b9](https://github.com/vaishnavi596/volume-king/commit/9c3539b98634dd56f632bfeabb80deb8febaf940) adds test guards requiring the existing manual contract confirmation before Start and live-order separation. [43758278313](https://github.com/vaishnavi596/volume-king/actions/runs/43758278313) **SUCCESS**; latest [43758295339](https://github.com/vaishnavi596/volume-king/actions/runs/43758295339) was still running at record time.
- **Not done:** Paper Bot is not an unattended provider-mark auto-trading system. Automatic activation without user confirmation is deliberately blocked; orders remain OFF. Futures verified directional OI source and independent sourced News score still WAIT. Actual Android phone test and authenticated Oracle Options/selected-equity smoke remain PENDING; no production mutation, no new APK.


## 2026-11-16 — 127-C saved Super Five filter votes + full regression checkpoint

- **New code [f92174e5](https://github.com/vaishnavi596/volume-king/commit/f92174e58929d417e7f0e7ab7237ea7da1d05a28):** `five_engine_chips` can read previously saved same-provider Dhan Top Five historical rows when the per-session `watch_signal_cache` has not yet been rebuilt by the paced 51-history scan. Existing directional filter votes are displayed as historical B/S; the row must be historical and source Dhan, never a current or verified live/5-of-5 signal. No per-card Dhan request is introduced.
- **Test [3da3d932](https://github.com/vaishnavi596/volume-king/commit/3da3d93249eca1dd269b359ff9ba0d8d025d4c07):** adds saved-ranking, source, HIST and reuse guard to `tests/test_joint_bootstrap_options_127.py`. Latest [offline regression run 43758508003](https://github.com/vaishnavi596/volume-king/actions/runs/43758508003) **SUCCESS: 818 tests, OK**, job `132947796822`. This is the actual latest tested app+test commit; documentation commits afterward are not new APKs.
- **End-to-end acceptance remains separate:** 127-A source/CI proof and 127-C/D offline checks do NOT establish mobile login autofresh, all 51+selected equity data, three-index live/current timestamp, RELIANCE/HDFCBANK listed expiry/CE/PE contract actual Oracle access, independently sourced News/Futures voting or unattended Paper Bot. These remain **PENDING** and will be required before final v2.3.127 release. Paper Bot remains manually started local simulation with real order submission OFF.
- **Production and release:** Oracle remains unchanged/read-only historical evidence only; no new Oracle authenticated probes, service restarts, token changes, versionName/versionCode increments or signed APK. Continue Batch 127-B read-only actual endpoint integration and 127-D option entitlement before release gate.


## 2026-11-16 — Joint 127-C News context + 127-B/D read-only integration probe

- **News source improvement:** [0a140cd0](https://github.com/vaishnavi596/volume-king/commit/0a140cd03cdd92afc25029a9ad89d0b27e736fb4) adds one authenticated-generation local Top Five headline-context task (maximum five known Top Five equities, sequential 0.5s spacing, 256 KiB maximum per RSS response, reused 600s cache). It does **not** supply market data or count experimental phrases as an independently verified News directional vote. This is public headline context, while actual share/index quotes remain Dhan-only. [fb60e0a2](https://github.com/vaishnavi596/volume-king/commit/fb60e0a2f318cc025df974f05081db2534b11f4a) adds tests confirming five-request bound, no Dhan fanout and News WAIT policy. [Run 43758761236](https://github.com/vaishnavi596/volume-king/actions/runs/43758761236) **SUCCESS**; [43758740371](https://github.com/vaishnavi596/volume-king/actions/runs/43758740371) **SUCCESS**.
- **Stock Option Chain routing:** [3647804c](https://github.com/vaishnavi596/volume-king/commit/3647804c21b3a6e8bbfa1e62fffc72fdf021239d) adds mock route tests asserting correct NSE_EQ IDs for RELIANCE (2885) and HDFCBANK (1333), no exchange-live claim and no invented premium when Dhan does not supply a chain. This is **MOCK TEST**, not proof that the broker has listed expiries or entitlement. [Run 43758930482](https://github.com/vaishnavi596/volume-king/actions/runs/43758930482) **FAIL**: a separate `test_server_gateway` session-revocation assertion expected 401 but received 502; do not suppress or claim full PASS. Root cause/flake to be checked against newer full suite.
- **Bounded Oracle audit script:** [b05089cf](https://github.com/vaishnavi596/volume-king/commit/b05089cfb68a90f47d6e815cc751851931283b83) adds `scripts/check_127_oracle_readonly.py`. Operator-run, authenticated, no credential logging; sequential read-only status, 51 snapshot, 3-index batch, optional <=70 selected equities and broker-listed expiry/chain (default RELIANCE/HDFCBANK) with 3.5s option pacing. Only metadata/counts/availability, not unverified quote prices or order calls. This script has **NOT BEEN RUN on Oracle**; production unchanged.
- **Mock test of the probe:** [c049f712](https://github.com/vaishnavi596/volume-king/commit/c049f7123c9aa191357f37cf5c2a1c4f2f87338a) checks 51/3/selected and two stock options, 422 missing expiries, no fabricated chain and forbidden order-route path. Latest CI [43759118694](https://github.com/vaishnavi596/volume-king/actions/runs/43759118694) was **IN PROGRESS** when this entry was authored. If it fails, inspect exact newer job before proceeding.
- **Gates:** News/Futures real independent B/S still WAIT; user device v2.3.126 login refresh FAIL history retained. No signed 2.3.127 APK, version change, token reset, server restart/deployment or broker real order. Paper simulation remains manually started.


## 2026-11-16 — 127-B/D full regression uncovered session-expiry import-path bug

- **Repro evidence:** [run 43758930482](https://github.com/vaishnavi596/volume-king/actions/runs/43758930482) 821 tests / 1 FAIL; [run 43759118694](https://github.com/vaishnavi596/volume-king/actions/runs/43759118694) 824 tests / 1 FAIL. Both failed the existing security test `test_server_gateway.GatewayTests.test_broker_failure_is_sanitized_and_expired_session_is_revoked`: a broker `SessionExpired` was reported as generic 502 rather than revoking the session with HTTP 401. No other failure was reported in those runs. This defect became reproducible after newly ordered tests imported `backend.server` before top-level `market_feed`, yielding distinct `src.market_feed.SessionExpired` and `market_feed.SessionExpired` class identities.
- **Code fix [f434fdf8](https://github.com/vaishnavi596/volume-king/commit/f434fdf82d2208f51f7c006880231158728d73b9):** the GitHub `backend/server.py` run handler recognizes only trusted `SessionExpired` exception classes from the two known adapter module paths, revokes session and returns sanitized 401, while other faults remain 502. No arbitrary error string or secret is disclosed. **Not deployed to Oracle production** (production server is separately customized; do not overwrite).
- **Behavior test [6fb58023](https://github.com/vaishnavi596/volume-king/commit/6fb58023a61c0ca55548fa48eb18860dcbadc933):** confirms both trusted module-origin exception classes invalidate the authenticated read-only gateway session without leaking provider text. Original regression is retained. [CI 43759399916](https://github.com/vaishnavi596/volume-king/actions/runs/43759399916) and [CI 43759426158](https://github.com/vaishnavi596/volume-king/actions/runs/43759426158) were **IN PROGRESS** at writing; no PASS claim until final.
- **Release:** 2.3.127 APK not built; actual Oracle option CE/PE/mapped equity entitlement, selected 51+extra market data and phone acceptance remain unverified. No server commands, production restart, signing, credentials change or live orders.


## 2026-11-16 — Latest combined Batch 127 source regression SUCCESS

- **Latest tested SHA:** [6fb58023a61c0ca55548fa48eb18860dcbadc933](https://github.com/vaishnavi596/volume-king/commit/6fb58023a61c0ca55548fa48eb18860dcbadc933). [BOT KING Offline Regression Tests run 43759426158](https://github.com/vaishnavi596/volume-king/actions/runs/43759426158) **SUCCESS, 825 tests, OK**, verified from the actual job log. The preceding gateway-fix run [43759399916](https://github.com/vaishnavi596/volume-king/actions/runs/43759399916) **SUCCESS** as well. Earlier CI failures 43758930482 and 43759118694 were resolved by the trusted dual-import `SessionExpired` handling, not ignored.
- **Confirmed source scope:** Per-login Dhan read-only bootstrap/status and independent quote/index paths; cached historical Super Five filter B/S after close; bounded Top Five RSS headline context (not directional verified News vote); selected broker-listed Dhan option-chain on login; RELIANCE/HDFCBANK mapped mocked backend route and 16-entry per-session separate underlying/expiry context; CE/PE Premium/OI/ΔOI/Volume UI (missing values stay unavailable), PAPER simulation state shown in Error Doctor, session-revocation security regression fixed in GitHub source; no orders.
- **Not proven:** 825 offline PASS is **NOT MOBILE PASS**. No authenticated new Oracle run has established current 51+3+extra equity quotes, RELIANCE/HDFCBANK actually option-listed expiry/entitlement, CE/PE seven-strike data or current session freshness. Unverified/stale sources remain WAIT; real Futures feed and independent News directional 0–100 evidence are **PENDING**. Paper Bot remains a manually started simulated engine, not unattended trading.
- **Oracle/prod:** The read-only acceptance script `scripts/check_127_oracle_readonly.py` is committed, but **has NOT been executed on Oracle**. No production file changes, backup/restart, OAuth/token changes, real orders, version bump or APK build.
- **Release gate:** Continue 127-B authenticated Oracle read-only smoke and 127-D true provider option endpoint tests (including broker-listed validity, 422/409/429), plus mobile test after eventual release. Do not trigger 127-E signed APK until required A–D functional gates are satisfied, and do not conflate package build with phone PASS.


## 2026-11-16 — 127-B/D read-only Oracle probe hardening (new session)

- **Starting point:** GitHub source CI `43759426158` **825 PASS** at `6fb58023`; previous journal and Handoff preserved. **No authenticated Oracle commands or new APK** in this session.
- **Security fix [f899196b](https://github.com/vaishnavi596/volume-king/commit/f899196b9dbc3b016c0dcfc5083bfa01941c6b1f):** `scripts/check_127_oracle_readonly.py` now refuses HTTP redirects when carrying X-BotKing-Key, with explicit no-proxy opener; option sweep stops after a 429 rather than hammering subsequent stock expiries/chains. Session without authenticated market data skips option calls.
- **Further probe fix [ec528dac](https://github.com/vaishnavi596/volume-king/commit/ec528dac140b5979289eb65222fb5aff39cd5e1b), [197bbc39](https://github.com/vaishnavi596/volume-king/commit/197bbc398553523061c2a0fe78eed9828925f78e):** stop requests early on missing session and on account-wide 429 from quote/index/selected routes; prevalidate all option and selected symbols before first outbound request. Still read-only; no Oracle change.
- **Tests [bce97f38](https://github.com/vaishnavi596/volume-king/commit/bce97f381c3cfa7cbe11712b4609d7f2a98cb907):** redirect, no-auth and per-option 429 guards. [CI run 43781075480](https://github.com/vaishnavi596/volume-king/actions/runs/43781075480) **FAILED 1 ERROR of 827 tests**: test fake for expiry 422 lacked authenticated status and was correctly skipped by new security preflight. [d7347e63](https://github.com/vaishnavi596/volume-king/commit/d7347e6343d5a09268808a62b90a694fd2894fc9) fixes mock auth; [3b885e18](https://github.com/vaishnavi596/volume-king/commit/3b885e1855c13e9294f5bd3b5f43c7c9b830c753) adds separate account-wide index-429 stop regression. New final suite is **pending**, never assert PASS until its job completes.
- **Release gates:** 51/3 quotes, additional selected equity shares, real RELIANCE/HDFCBANK broker listed expiry, CE/PE seven strikes, expiry 422/409 and 429 evidence need authenticated operator-run Oracle smoke. This script has **not** been executed against production. Oracle backups not required for this code-only patch because nothing is deployed; live orders OFF. v2.3.126 device failure remains unresolved until a phone acceptance of a future release; 2.3.127 Signed APK NOT built.


## 2026-11-16 — Latest 127-B/D audit-probe regression PASS (new session)

- **Latest tested test/source SHA:** [3b885e1855c13e9294f5bd3b5f43c7c9b830c753](https://github.com/vaishnavi596/volume-king/commit/3b885e1855c13e9294f5bd3b5f43c7c9b830c753). [BOT KING Offline Regression run 43781254964](https://github.com/vaishnavi596/volume-king/actions/runs/43781254964) **SUCCESS: 828 tests, OK**, checked from actual job `133018719305` (previous `43781218974` also SUCCESS). This supersedes the preceding 827-test temporary mock failure `43781075480`; the test now correctly models authenticated 422 expiry rejection.
- **Verified source safety:** Read-only Oracle probe will not follow redirects or machine proxy configuration with a pairing key. It prevalidates requested symbols, stops immediately on unauthenticated/unconfigured status, and avoids subsequent option-chain calls after account-wide index/snapshot/selected 429, or after any individual option expiry/chain 429. New tests check bounded 51/3 counts, missing expiry, 403/no-auth, 429 and non-order route allowlist.
- **Critical evidence limit:** This is an **offline mock/CI PASS, not authenticated Oracle or device PASS**. The probe exists in GitHub but has NOT been run in the Oracle VM; no new real RELIANCE or HDFCBANK listed expiry/CE-PE response, 51+selected refresh or current collection age has been measured. Production Oracle code, Dhan OAuth, backup files, service, trade switches and credentials remain unchanged. No v2.3.127 APK, versionName/versionCode bump or mobile QA.
- **Next mandatory acceptance:** Have an authorized operator run `scripts/check_127_oracle_readonly.py` using existing secret-safe environment, review counts, actual entitlement and error classes, then repair any deployed/backend contract mismatch with timestamped production backups *only if needed*. Final APK gated on 127-B/D Oracle findings, missing verified News/Futures scope decision, and complete CI; do not mark mobile success before install/test.


## 2026-11-16 — Continuation reconciled with current GitHub branch

- Older chat patch `e2e3756dec67c3f95de760913c9bd0d434d997c1` (compact shared bars and scanner chart delivery) is already committed; Offline Regression run `43674063607` is confirmed completed SUCCESS. Its 778 local pytest/159 subtest evidence is historical, not the current app acceptance.
- Current integration branch is `fix/botking-joint-audit-70-15-20261115`, observed HEAD `b1fb8bc9a9d308c88bf7dc7bf5617d69a8a4644c`. Current journal was read before continuing; obsolete local 2.3.111 edits were not reapplied over newer work.
- Independently checked GitHub run `43781254964` at `3b885e1855c13e9294f5bd3b5f43c7c9b830c753`: completed SUCCESS. The preceding journal records 828 tests from its job log; this continuation checked run status, not a new local 828-test execution.
- Read current `scripts/check_127_oracle_readonly.py` and its CLI/environment contract. Next acceptance is operator-run authenticated public HTTPS status, 51-equity snapshot, three-index batch, selected-equity and RELIANCE/HDFCBANK listed-expiry/chain checks. Credentials must remain on the operator shell and never be pasted into chat.
- No Oracle session/SSH connection is available in this chat. Probe has NOT been executed by this continuation; no device PASS, actual option entitlement, new feed freshness or production safety result is claimed. No source repair, server deployment/restart, Dhan token change, version bump, APK dispatch or real order was performed. Await metadata-only Oracle output before deciding the next combined repair.


## 2026-11-16 — Batch 127-D option-chain cooldown + stale-selection repair

- **Source audit:** Existing option polling attempted every >=60s during market hours, but the Dhan gateway deliberately caches option HTTP 422 invalid underlying/expiry responses for 300s and applies 429 provider-wide cooldown. Repeated scheduled attempts can overwrite option diagnostics and create avoidable local retries even when the upstream is guarded. This is a **source-level defect**, not a current authenticated provider observation.
- **[97134aa7](https://github.com/vaishnavi596/volume-king/commit/97134aa7c363ab1bbef7f8307d307e905c1e0d89):** adds bounded (32), in-memory `option_retry_until` per provider generation, symbol, selection mode and manual expiry; 422 waits 300s; 429 honors at least 30s and Dhan gateway cooldown; successful chosen chain clears its key. Scheduled polling and manual actions guard both Dhan option endpoints; saved CE/PE remains unverified and no broker orders are introduced.
- **[7804c9d1](https://github.com/vaishnavi596/volume-king/commit/7804c9d168771ef786a6473b64af87b6e613683e):** adds 127-D source contract regression for bounded cooldown and per-symbol/expiry isolation.
- **[7eee0f21](https://github.com/vaishnavi596/volume-king/commit/7eee0f21100233fd6f1c62520119e3f658181590):** guards failure/cooldown publication so an old symbol/expiry request cannot overwrite status of a newly selected underlying. **[b4798e45](https://github.com/vaishnavi596/volume-king/commit/b4798e454263f79860dc2b0624be48e2d9dcb677)** adds test of this selection gate.
- **CI evidence:** Earlier 828-test suite [43781254964](https://github.com/vaishnavi596/volume-king/actions/runs/43781254964) remains PASS; preliminary [43784892390](https://github.com/vaishnavi596/volume-king/actions/runs/43784892390) SUCCESS for initial code-only patch. Latest full test [43784999118](https://github.com/vaishnavi596/volume-king/actions/runs/43784999118) still running/queued at log writing and is **NOT YET PASS**. Do not infer device acceptance.
- **No Oracle/production mutation** or authenticated fresh 51+3/RELIANCE/HDFCBANK option smoke; user still needs server operator-run metadata-only results. No versionCode/name increment, signed 2.3.127 APK or phone validation. Live orders OFF, Paper Bot manual simulation only.


## 2026-11-16 — Batch 127-D option retry, Batch 127-B selected-share diagnostics

- **Option error pacing:** [97134aa7](https://github.com/vaishnavi596/volume-king/commit/97134aa7c363ab1bbef7f8307d307e905c1e0d89) adds a bounded, session-local option cooldown keyed by generation/underlying/selection and manual expiry: HTTP 422 => 300s same-selection pause; 429 => at least 30s plus Dhan shared cooldown. Both automatic polling and manual requests check the cooldown, without discarding last-valid read-only CE/PE context. [7eee0f21](https://github.com/vaishnavi596/volume-king/commit/7eee0f21100233fd6f1c62520119e3f658181590) avoids publishing a stale old-symbol error/status after the user selects a different symbol. Regression updates [7804c9d1](https://github.com/vaishnavi596/volume-king/commit/7804c9d168771ef786a6473b64af87b6e613683e) and [b4798e45](https://github.com/vaishnavi596/volume-king/commit/b4798e454263f79860dc2b0624be48e2d9dcb677). Offline Regression run [43784999118](https://github.com/vaishnavi596/volume-king/actions/runs/43784999118): **829 tests, OK, SUCCESS**, verified from actual job log.
- **Selected extra NSE shares:** [a243b13d](https://github.com/vaishnavi596/volume-king/commit/a243b13dd167bb2010b51250241740f6eadafb1d) retains fixed 51-share result if the additional `/dhan/selected-ltp-batch` fails, but explicitly publishes a sanitized, 120-character route error in Login and Watchlist statuses. This makes an undeployed Oracle route (404), staged instrument mismatch (422), auth failure (403) or rate limit (429) visible instead of silently showing just `Partial`. [a31bc898](https://github.com/vaishnavi596/volume-king/commit/a31bc898d5a52dec29e09336ed90452155a6cfa5) adds regression checks. New latest full CI [43785242114](https://github.com/vaishnavi596/volume-king/actions/runs/43785242114) was running at journal creation; **not yet PASS** at that checkpoint.
- **Release blockers persist:** No remote Oracle shell/authorized pairing context available in this chat, and the read-only Oracle script has not executed on production. No verified RELIANCE/HDFCBANK CE/PE/expiry entitlements, no measured current 51+3+selected-data completeness, no independently verified Futures directional feed, no signed 2.3.127 APK, versionCode/name update or Android acceptance. No Oracle production mutations and live broker orders OFF; Paper Bot manual simulation only.


## 2026-11-16 — Combined 127-B/D latest full CI SUCCESS

- **Latest source+test SHA** [a31bc898d5a52dec29e09336ed90452155a6cfa5](https://github.com/vaishnavi596/volume-king/commit/a31bc898d5a52dec29e09336ed90452155a6cfa5), [BOT KING Offline Regression run 43785242114](https://github.com/vaishnavi596/volume-king/actions/runs/43785242114) **SUCCESS / 830 tests / OK** (verified from job log). Includes all 127-A/C/D prior source regressions plus 422/429 option cooldown and selected extra NSE share diagnostics.
- **Material changes:** Options refresh now honors per-current-selection 300s invalid expiry and Dhan account-wide 429 cooldown, avoids publishing stale different-symbol failure, and retains existing CE/PE data as unverified context. Login and scheduled Watchlist refresh now surface bounded sanitized failures of dynamic selected NSE equities without losing the fixed watchlist last valid prices. All remains Dhan read-only and paper-only; no live orders.
- **Proof boundaries:** This 830-test PASS is *GitHub offline*, not actual Oracle Dhan entitlement, not a fresh quote timestamp and not Android mobile PASS. No Oracle CLI execution or credential access was available. RELIANCE/HDFCBANK listed expiry/CE/PE, 51+extra+three-index runtime completeness, independent Futures/News directional engine and installed APK auto-refresh still need real end-to-end evidence. v2.3.127 APK has **not** been triggered; versionName/versionCode remain unchanged and Oracle production unchanged.


## 2026-11-16 — Batch 127-B after-close three-index recovery correction

- **Source defect found:** `dhan_index_poll` historically evaluated whether any saved NIFTY/BANKNIFTY/SENSEX quote was missing to decide a one-time after-close recovery. Cached old values could therefore hide an incomplete **new authenticated login's** batch. No current server measurement or mobile observation was used to infer a successful fresh quote.
- **[57e53806](https://github.com/vaishnavi596/volume-king/commit/57e53806a16f720bd50c0ccf24ffdc9d537d61e5):** switches recovery to the current provider generation's `login_bootstrap` index stage and actual `3/3` count. A stale saved price is not 3/3 new-login evidence.
- **[b56ab7bd](https://github.com/vaishnavi596/volume-king/commit/b56ab7bdd7907d2ec4d40d72ae35a641754aa61f):** further limits recovery to terminal PARTIAL/FAILED/COOLDOWN login outcomes, never while the first index request is LOADING; only one closed-session recovery per login generation and provider throttle is still maintained. No new per-symbol fanout, no false live timestamps.
- **Tests:** [c8252454](https://github.com/vaishnavi596/volume-king/commit/c8252454fd5aa8cff9f3a77eb70ffbb1c1c5a75b) and [2a2c2efa](https://github.com/vaishnavi596/volume-king/commit/2a2c2efa5f09839cfff7336b8b321c7238b84662) add source guards. An old `tests/test_dhan_bootstrap_behavior.py` test expected the entire bootstrap decision in a single expression and failed with missing temporary expression names on intermediate runs [43786680725](https://github.com/vaishnavi596/volume-king/actions/runs/43786680725), [43786775933](https://github.com/vaishnavi596/volume-king/actions/runs/43786775933). [a583abbf](https://github.com/vaishnavi596/volume-king/commit/a583abbf3b149e4f2c2be45e4124ad60ba7ec3c3) updates the actual source-AST behavioral test to evaluate all four named conditions in order, checking PARTIAL, FAILED, COOLDOWN, LOADING, LOADED, generation mismatches, saved prices and market hours. [7caac968](https://github.com/vaishnavi596/volume-king/commit/7caac968c18437229a2d6384e99b1d9708fce6dc) fixes an obsolete literal assertion that looked for `and not regular_hours()` instead of the actual `closed_index_bootstrap=(not regular_hours()` expression.
- **Final suite pending at journal write:** [run 43786961360](https://github.com/vaishnavi596/volume-king/actions/runs/43786961360) running. Prior `43785242114` 830 tests PASS is not a PASS for this new code. Do not build a new APK or claim new code PASS until latest checks finish.
- **Boundary:** No authenticated Oracle command or production deployment/restart; no real NIFTY/BANKNIFTY/SENSEX 3/3 after-login proof, no RELIANCE/HDFCBANK actual chain entitlement, no mobile validation, no versionCode/versionName bump. Paper-only and live orders OFF.


## 2026-11-16 — 127-B index recovery latest CI confirmed PASS

- **Latest actual source/test commit:** [7caac968c18437229a2d6384e99b1d9708fce6dc](https://github.com/vaishnavi596/volume-king/commit/7caac968c18437229a2d6384e99b1d9708fce6dc). [BOT KING Offline Regression run 43786961360](https://github.com/vaishnavi596/volume-king/actions/runs/43786961360) **SUCCESS, 831 tests, OK** (job `133036657494`, verified against full test log). Earlier intermediate CI failures were obsolete bootstrap expression/assertion tests; the *actual app-source condition* is now tested through the exact AST dependencies rather than reimplemented logic, including cached old prices with PARTIAL, FAILED, COOLDOWN, LOADING, LOADED, wrong generation, and open vs closed sessions.
- **Behavioral gain:** Once the *current generation* login index stage completes incompletely or fails, a single after-close index batch retry is permitted even when saved NIFTY/BANKNIFTY/SENSEX quotes are present. It is suppressed during an in-flight LOADING stage or after a verified-in-this-session 3/3 batch. Independence from the 51-share Watchlist is preserved, with source Dhan and freshness marked unverified.
- **Still pending:** No authenticated Oracle 51+index+selected-stock/Option Chain real acceptance and no installed v2.3.127 mobile test. 831 offline tests are **not** real-time market data proof. No APK/versionName/versionCode changes, Oracle production edits, restarts or live broker orders were performed.


## 2026-11-16 — Batch 127-C first-login News context repair (GitHub only)

- **Audit finding:** In `src/main.py` `refresh_superfive_news`, the per-generation RSS bootstrap selected symbols only from `top5_candidates`. On first install, cache reset, or no saved Dhan ranking, this list can be empty; the function then marks the generation handled and fetches **zero** equity headlines even though the user has a 51-stock Watchlist. This is a source-level first-login bug, not evidence of current live provider data.
- **Applied [1ad14ed3](https://github.com/vaishnavi596/volume-king/commit/1ad14ed37fc473b6c3ac3245f698a2358f07859f):** Prefer valid Top Five equities; if fewer than five are available, fill from configured Watchlist symbols until at most five distinct equities are selected. Continue existing 0.5-second RSS pacing, per-login request bound, generation/connectivity guard, 256KiB size cap and **News is unverified context, NOT a 0–100 directional trading vote or broker order signal**.
- **Tests [d36e2697](https://github.com/vaishnavi596/volume-king/commit/d36e26976174fe27dd45d5335b631508cbe817a9):** existing source-contract regression now checks fallback loop, distinctness, five-item stop and bounded per-symbol calls.
- **CI:** Latest [Offline Regression run 43787736873](https://github.com/vaishnavi596/volume-king/actions/runs/43787736873) at tested SHA `d36e26976174fe27dd45d5335b631508cbe817a9` **SUCCESS: 831 tests / OK** verified in actual job log; earlier source-only `43787714898` also SUCCESS. No APK build workflow was triggered.
- **Acceptance boundaries:** News context fetching is not verified on Android or the live network; standalone source CI PASS is not device PASS. Oracle 51+3+extra quotes and RELIANCE/HDFCBANK actual listed option CE/PE entitlement/expiry remain unverified because operator shell/pairing key is unavailable here. No production Oracle file, token, service, release version or live order setting was touched. v2.3.127 APK remains **NOT BUILT**; continue 127-B/D live smoke gate before a release.


## 2026-11-16 — Batch 127-B root-cause repair: missing Oracle ingester and bounded 51-equity bootstrap

- **Concrete source audit:** `backend/server.py` sets `BOTKING_226_INGEST_ENABLED=0` unless explicitly enabled in the Oracle environment, and `/v2/snapshot` only reads the process-local collector cache. `src/server_feed.py` correctly rejects `not_collected`/overdue snapshots, but the Android Login and 60s Watchlist polls previously invoked only that cache endpoint. **If production collection is disabled/overdue, old saved RELIANCE 1339.70 etc. can remain displayed indefinitely without a new quote.** This is an identified conditional source-path failure; production's actual env remains uninspected.
- **[d38599f8](https://github.com/vaishnavi596/volume-king/commit/d38599f865c2dcb589bcb8cb957dfeaa5c4ad149):** adds `ServerDhanReadOnly.equity_quotes_with_bootstrap()`: first try strict `batch_quotes()` from authenticated `GET /v2/snapshot`; if the cache is absent/stale, allow **one** explicitly authenticated `POST /dhan/ltp-batch` (the existing fixed-51, read-only server route) at most every **180 seconds per session**, respecting global Dhan 429 cooldown. Validate source Dhan, `live_orders_enabled=False`, fixed 51 stock universe, availability accounting and all finite positive LTP values. Never infer exchange timestamps, never issue individual 51 symbol requests or use Yahoo/Angel fallback. Failed requests are throttled and retain last-valid quotes.
- **[6c4625f5](https://github.com/vaishnavi596/volume-king/commit/6c4625f5df044e4b5f0b0023a396caee15378fdf):** Android initial Login batch and scheduled/page-entry Watchlist batch both use the *same* guarded recovery method, so existing timer, 60s poll, optional extra selected-equity batch, 30s manual and refresh repaint stay aligned.
- **[f45d0f92](https://github.com/vaishnavi596/volume-king/commit/f45d0f92aa86ce91bbc621f047d6da0f0de29c6a):** five new offline regression tests cover stale cache -> fixed read-only 51 quote route once; 180s repeat suppression; valid cache never triggering provider request; rejecting invalid/partial contract, unverified/simulated prices, Yahoo data, live-order flags; auth/network/429 fail-closed; session reset and both Android call sites.
- **CI repair:** Source-only run [43789468180](https://github.com/vaishnavi596/volume-king/actions/runs/43789468180) SUCCESS, but pre-regression intermediate [43789496191](https://github.com/vaishnavi596/volume-king/actions/runs/43789496191) and [43789557376](https://github.com/vaishnavi596/volume-king/actions/runs/43789557376) FAILED because *two existing source-string tests* still required the obsolete call `dhan_feed.batch_quotes` directly. Test contracts updated to the new bounded wrapper by [21ecf5e9](https://github.com/vaishnavi596/volume-king/commit/21ecf5e99e71acdca6daf45ac149b61e7a86fed2) and [6b3af492](https://github.com/vaishnavi596/volume-king/commit/6b3af4920f4f384aba4776b2074550c4496677e5). Final full [run 43789687353](https://github.com/vaishnavi596/volume-king/actions/runs/43789687353) running at journal creation; **not yet PASS**.
- **Crucial release boundary:** Github tests are mocked/offline. No authenticated Oracle `/dhan/ltp-batch` or `/v2/snapshot` response from user's actual server was obtained, no proof of current 51/3 data, extra stocks, stock option chains or phone refresh. No production Oracle changes, no OAuth change/rotation, no live orders, no signed APK and no 2.3.127 version bump. Continue authenticated read-only Oracle smoke and on-phone QA before final release acceptance.


## 2026-11-16 — 127-B bounded Dhan equity bootstrap fully tested

- **Final tested source SHA:** [6b3af4920f4f384aba4776b2074550c4496677e5](https://github.com/vaishnavi596/volume-king/commit/6b3af4920f4f384aba4776b2074550c4496677e5). [BOT KING Offline Regression CI 43789687353](https://github.com/vaishnavi596/volume-king/actions/runs/43789687353): **SUCCESS / 836 tests / OK**, verified from actual GitHub workflow job `133045040989`. This supersedes earlier failures caused by the two obsolete source-string test assertions.
- **Actual improvement:** both Login and recurring Watchlist updates first try server-owned 51-equity snapshot; when that read-only snapshot is absent/overdue, the paired Dhan gateway may use at most one validated **fixed 51-equity** read-only batch per 180s to recover. Valid cached snapshots never trigger an additional broker request. Bad contracts, source mismatches, malicious prices, forbidden live-order flags, network/auth failures and cooldowns fail closed. Old valid quotes are retained with unverified timestamp status. No Yahoo/Angel fallback or individual 51-symbol fanout. Existing index batch remains independent.
- **No device or server proof yet:** These 836 tests are offline source/contract regressions, not a live Dhan or Oracle acceptance. The actual Oracle opt-in ingestion status, Dhan market data entitlement, RELIANCE/HDFCBANK chain, 51 + selected stock + 3 index runtime freshness and installed v2.3.127 phone refresh still require authoritative checks. No Oracle production restart/changes, credential rotation, order activation, version bump or APK build. Live orders OFF.


## 2026-11-16 — 127-B 51-equity direct recovery versus Oracle snapshot provenance

- **Current branch reconciliation:** Newly committed separate branch work was found before modifying these files: [6b3af492](https://github.com/vaishnavi596/volume-king/commit/6b3af4920f4f384aba4776b2074550c4496677e5) and [CI 43789687353](https://github.com/vaishnavi596/volume-king/actions/runs/43789687353) had already added and validated a bounded, fixed 51-equity direct Dhan recovery through `equity_quotes_with_bootstrap`, **836/836 offline PASS**. This continuation retained that code instead of implementing overlapping fallback logic.
- **Display defect identified:** The direct `/dhan/ltp-batch` fallback stamped each result `snapshot_age_seconds=0.0` even though **it was not an Oracle cached snapshot**; scheduled Watchlist displayed `Oracle snapshot age 0s`. This mislabeled an unverified Dhan batch as a fresh Oracle cache. Login always said `Login snapshot` even when it was direct.
- **Applied [c27a86de](https://github.com/vaishnavi596/volume-king/commit/c27a86de43b7956eec17b108eaaf42a4c728dec7):** `src/server_feed.py` sets `quote_collection=oracle_snapshot` on validated cached quotes, and `quote_collection=direct_dhan_batch`, `snapshot_age_seconds=None` on validated direct recovery. No exchange-time claim; `freshness=unverified`, `live_verified=False`, `quote_timestamp=None` retained.
- **Applied [07cabde6](https://github.com/vaishnavi596/volume-king/commit/07cabde67c5591519bc87baae88341b2043624eb):** `src/main.py` separates Scheduled Watchlist `Dhan direct 51-equity batch` from `Oracle snapshot age Ns`; Login also distinguishes `Login Dhan direct batch` from `Login Oracle snapshot`, with existing partial counts, last-valid retention and selected NSE error context unchanged.
- **Regression repairs [7ab8fc75](https://github.com/vaishnavi596/volume-king/commit/7ab8fc752d3f7d9c91d64ffeb2701f33dd652281), [e1951631](https://github.com/vaishnavi596/volume-king/commit/e1951631c7d3e985b659b20bf566f754636d0acb), [7043cf9e](https://github.com/vaishnavi596/volume-king/commit/7043cf9e07b71c8b793556d6ab8d568b968f5762):** assert direct recovery has no fake snapshot age, cached snapshot has explicitly Oracle provenance, and Login status is mode-aware.
- **Final CI:** [BOT KING Offline Regression run 43790226101](https://github.com/vaishnavi596/volume-king/actions/runs/43790226101), tested source SHA `7043cf9e07b71c8b793556d6ab8d568b968f5762`: **SUCCESS / 836 tests / OK**, confirmed from actual GitHub Actions job log. This remains an offline code/contract PASS, not a phone or real Oracle PASS.
- **No production edits** or real authenticated Oracle tests; no Dhan credentials rotated, live orders enabled, versionName/versionCode changed or 2.3.127 APK built. Actual Oracle ingester/recovery route, 51+3 quote completeness, RELIANCE/HDFCBANK listed chain entitlement, and mobile Login→Refresh acceptance remain open gates.


## 2026-11-16 — 127-B/D operator-only read-only Oracle direct 51-equity acceptance scope

- **Baseline:** Prior completed source/contract workflow [43790226101](https://github.com/vaishnavi596/volume-king/actions/runs/43790226101) **836 tests PASS**; its read-only `equity_quotes_with_bootstrap` direct-fixed-51 fallback is GitHub-side only, not current Oracle availability proof.
- **[906950a2](https://github.com/vaishnavi596/volume-king/commit/906950a24dc052e5049f8ba69028f3e2c16fad16):** Updated `scripts/check_127_oracle_readonly.py` to recognize `/dhan/ltp-batch` as a strictly read-only route; NEW `--direct-equities-if-stale` is **opt-in**, never requested by default, and at most one fixed 51-equity upstream request is possible. If Oracle's fresh `/v2/snapshot` is usable, skip the direct provider batch. Report count, missing count, source/freshness/HTTP only—never LTP prices, tokens or pairing keys. A 429 from snapshot/index/direct now prevents later market routes; index 429 is checked **before** selected equities. Existing broker-listed RELIANCE/HDFCBANK 3.5s paced chain probe remains.
- **[bfa5365a](https://github.com/vaishnavi596/volume-king/commit/bfa5365ad6247b442d5d76af393a093c15775a6e):** Tightened direct optional probe: only a structurally valid `HTTP 200`, `source=dhan`, `live_orders_enabled=False`, `freshness=stale_or_missing` and recognized stale/overdue collection status can authorize this extra check. HTTP403/503, invalid safety contract or malformed response cannot trigger direct Dhan. No real order APIs available.
- **Tests [a2c58118](https://github.com/vaishnavi596/volume-king/commit/a2c58118034f9efc287b5e5392250d1e2d71f010), [4796ba0a](https://github.com/vaishnavi596/volume-king/commit/4796ba0a78495ba1eba0758be6192f1beb6a45f8):** healthy cached Oracle → zero broker fallback; stale → one direct batch only with explicit opt-in; broker 429 → no index/chain fanout; missing/invalid auth/safety/route → no bypass; HTTP codes/counts only, never prices/secret in output; index 429 skips selected equity request.
- **CI checkpoint:** Latest [run 43790868796](https://github.com/vaishnavi596/volume-king/actions/runs/43790868796) running when this log was written. Do not infer PASS until completed and checked from job log.
- **Limits:** Script is *not* being executed on actual Oracle here (operator shell/pairing key unavailable); no proof actual 51 direct quotes, NIFTY/BANKNIFTY/SENSEX fresh values, selected user equities, RELIANCE/HDFCBANK listed expiries/CE/PE. No Oracle production file edit/restart, no Dhan OAuth rotation, no signed 2.3.127 APK, no mobile PASS, no live orders.


## 2026-11-16 — 127-E strict read-only release acceptance verdict

- [CI 43790868796](https://github.com/vaishnavi596/volume-king/actions/runs/43790868796) completed **841/841 PASS** at source/test commit `4796ba0a`, validating optional `--direct-equities-if-stale`, account-wide 429 aborts, auth/contract safety preconditions, and secret-free metadata counts. This code was not run on user's Oracle.
- **[3e4a6b58](https://github.com/vaishnavi596/volume-king/commit/3e4a6b5800098b99bcfd5d9f336a4f082a1128c0):** `scripts/check_127_oracle_readonly.py` now adds `acceptance()` summary with explicit boolean checks: authenticated+configured status, **51/51** cached Oracle or explicitly opted-in validated direct equity response, **3/3** indices, all requested selected shares, and **7** ATM listed strikes/PCR/Max Pain per requested RELIANCE/HDFCBANK option underlying. Verdict `READ_ONLY_PROBE_PASS` requires ALL checks; incomplete results report `NOT_VERIFIED` and CLI exits with status 1. `exchange_live_verified=False` and `live_orders_enabled=False` remain explicit even on read-only probe PASS; this is **not** a phone, live timestamp, or order/trading authorization.
- **[e01584f2](https://github.com/vaishnavi596/volume-king/commit/e01584f20b82b608a0fa0090dde5eab14756ba45):** Regression tests assert no false PASS with partial 51/3, missing stock CE/PE strike window, stale cache, and CLI nonzero exit on incomplete data. Direct 51 can satisfy equity acceptance only when explicitly requested and complete.
- Latest full CI [43791161563](https://github.com/vaishnavi596/volume-king/actions/runs/43791161563) is **in progress at log time**; not yet PASS. No Oracle credential/SSH access in this chat, no live request, no deployment or new APK. Current installed v2.3.126 failure is still unresolved until device acceptance. Stop final signed v2.3.127 release until actual read-only Oracle counts and mobile QA pass.


## 2026-11-16 — 127-E latest full offline CI success

- **Last tested source+tests SHA:** [e01584f20b82b608a0fa0090dde5eab14756ba45](https://github.com/vaishnavi596/volume-king/commit/e01584f20b82b608a0fa0090dde5eab14756ba45). [BOT KING Offline Regression run 43791161563](https://github.com/vaishnavi596/volume-king/actions/runs/43791161563): **SUCCESS / 843 tests / OK** verified from the completed job log. This supersedes the previous 841-test checkpoint.
- **Operator-only CLI usage:** `python3 scripts/check_127_oracle_readonly.py --direct-equities-if-stale` with `BOTKING_URL` and `BOTKING_PAIRING_KEY` supplied privately on an authorized shell; default execution omits the broker direct route. The optional direct 51 Dhan batch is only attempted after a valid stale authenticated snapshot, at most once per invocation; account-wide HTTP429 aborts further calls. Report includes `acceptance.verdict`, 51/3/selected/options booleans and minimal diagnostic metadata with **no prices/keys/tokens**; incomplete acceptance returns nonzero exit code.
- **Proof limitation:** This is mock/CI PASS only. Actual Oracle source/route deployment, broker entitlement, source data quality, exchange timestamps, stock option 7-strike chain, and phone v2.3.126 refresh failure remain unverified. `READ_ONLY_PROBE_PASS` itself does **not** prove exchange live timestamps, signal eligibility, or trade permission. No authenticated Oracle shell/test was executed; Production and APK/version unchanged, orders OFF.


## 2026-11-16 — Joint SERVER ↔ DHAN ports, pairing key, token, quote quota audit

**Scope / external rulebook:** DhanHQ v2 official authentication, Market Quote and API rate-limit documentation verified on 2026-11-16:
- Market Quote `POST https://api.dhan.co/v2/marketfeed/ltp` requires `access-token` and `client-id` headers, up to 1000 instruments per call and **1 quote request per second**; see https://dhanhq.co/docs/v2/market-quote/ .
- Dhan API token validity is normally **24h**; OAuth consent API key/secret and the 24h access token have different validity. Dhan profile returns actual `dataPlan`, `dataValidity`, active segments and token validity; configured credentials do not establish entitlement; see https://dhanhq.co/docs/v2/authentication/ .
- DhanHQ v2 API rate caps distinguish Quote (1/sec) from historical Data (5/sec, up to 100k/day). Option Chain uses separate 3-second pacing and listed expiries; see https://dhanhq.co/docs/v2/ and /releases/ . Broker trading/order endpoints remain intentionally DISABLED in BOT KING.

**Source-level connection model:** external Android ↔ owner domain HTTPS 443 (Nginx) ↔ localhost 127.0.0.1:8000 (Uvicorn FastAPI). `X-BotKing-Key` is server pairing/auth only, **never the Dhan access token**. Oracle ↔ Dhan market/auth endpoints use TLS 443 and OAuth app credentials or protected read-only token. GitHub `backend/install-oracle.sh` declares /dhan/ and /v2/ reverse proxies; `backend/server.py` enforces 403 on absent/wrong pairing and no live orders. **Real Oracle firewall/Nginx/systemd, route deployment, env/session file mode, outbound DNS/TLS, Dhan token validity and dataPlan remain UNVERIFIED:** GitHub source ≠ deployed Oracle.

**Actual repairs applied and committed:**
- [772c38ef](https://github.com/vaishnavi596/volume-king/commit/772c38efc6ad3134bd37eb345dd265e11a9ae17c): Dhan adapter now serializes quote requests across instances using a shared lock and **1.05s floor**, including index, fixed 51 and selected equities. Rechecks global HTTP429 cooldown after waiting so no extra upstream quote request slips through. No per-stock 51 fanout or trading calls.
- [29a27118](https://github.com/vaishnavi596/volume-king/commit/29a2711898084cc54c8573546f3f843edca8fc73): adapter tests for cross-instance quote spacing and post-wait cooldown. Earlier source/test CI [43792084482](https://github.com/vaishnavi596/volume-king/actions/runs/43792084482) **844 tests PASS / SUCCESS**; later source commits also pending final combined CI.
- [e79f2669](https://github.com/vaishnavi596/volume-king/commit/e79f26698aeec4ec1c8afbc1a5e9060eb5ef3108) and [f7935e07](https://github.com/vaishnavi596/volume-king/commit/f7935e07310aae904ec3478a4b9b354d31aa9eb4): default server-to-Dhan `api.dhan.co` transport refuses HTTP redirects and ignores proxy environment for access-token/client-id, while retaining TLS validation; regression tests.
- [c61ab240](https://github.com/vaishnavi596/volume-king/commit/c61ab240bdbb7e75b690924674062e3397dae49e): Dhan OAuth consent/token exchange requests forbid redirects carrying `app_id`/`app_secret`. [b6a1818a](https://github.com/vaishnavi596/volume-king/commit/b6a1818acf7f626a31427ffa4d6a30b22b367da3) adds OAuth redirect test.
- [25cab964](https://github.com/vaishnavi596/volume-king/commit/25cab964ee878409ca46aa11798e9316aaed0f5b), [16c88a58](https://github.com/vaishnavi596/volume-king/commit/16c88a58297377ef8ee3b675f666ec049f3be875): old Oracle read-only readiness script no longer incorrectly requires a legacy `/etc/bot-king/dhan-token` when a protected OAuth `DHAN_SESSION_FILE` is available. Distinguishes configured sources, tests service-user file readability, never prints credential values. Correctly does not require opc to traverse root-only `/etc/bot-king` because systemd reads EnvironmentFile independently. Neither script nor production was executed/changed.
- [be10b4da](https://github.com/vaishnavi596/volume-king/commit/be10b4da74dc23b18e7aef005d34e0cf37961c1e): new static+syntax regression for audited port roles (443 inbound / localhost 8000), Dhan credential headers vs pairing key, quote 1/s, OAuth/legacy session checks and read-only adapter.

**Source audit result:** Dhan v2 headers, batch instrument limits, HTTPS origin, server pairing guard, 429 cooldown, 3s option pacing, configured 51+3+selected quote routes and live-orders OFF all appear in GitHub source. Token expiry checking for OAuth is coded, but **not an authenticated Dhan profile/dataPlan validity check**. Oracle's actual deployed changes/route list and port/firewall/token permissions cannot be claimed enabled without operator-run read-only proofs. Explicit status must remain **SOURCE PATCHED; ORACLE RUNTIME PENDING; APK v2.3.127 NOT BUILT**.

**Final combined CI:** [43792297962](https://github.com/vaishnavi596/volume-king/actions/runs/43792297962) in progress at initial journal append; verify job and update separately. No production restart, new credential, live order or signed APK.


## 2026-11-16 — Additional live-port readiness checks for owner-operated Oracle

- **[6553ca83](https://github.com/vaishnavi596/volume-king/commit/6553ca837ffeebf1300e72d86fc9071b521a5fab):** `backend/audit-oracle-dhan-readonly.sh` now checks `ss` 127.0.0.1:8000 loopback-only binding and credential-free outbound TLS to `https://api.dhan.co/v2/profile` on port 443 (no JWT/header; HTTP 401 is acceptable as a TLS/route reachability proof **only**, never token/data entitlement verification). Uses direct `--noproxy '*'` connectivity with short timeouts. Nginx config syntax and local health remain separate checks. No shell script was actually run on Oracle from this chat.
- **[5a4f73b5](https://github.com/vaishnavi596/volume-king/commit/5a4f73b5ee3d93abcafb5606e321cb73ee121cdd):** regression checks Bash syntax, no-secret port probes, and Dhan API route expectations. Await final full CI [43792643011](https://github.com/vaishnavi596/volume-king/actions/runs/43792643011).
- **Proof still missing:** actual Nginx public HTTPS 443 / firewall security group, certificate expiration and reverse-proxy deployment, private OAuth token access/expiry, Dhan `/v2/profile` Data API subscription, quote 51+3 status, options, and Android app. Source CI cannot establish remote port reachability or Dhan entitlement. No production changes, credential rotation or live broker orders.


## 2026-11-16 — S2D joint quota, key, port audit reconciliation

- Reviewed current GitHub `backend/server.py`, `backend/dhan_feed.py`, `backend/install-oracle.sh`, `backend/audit-oracle-dhan-readonly.sh`, `src/server_feed.py`, and the existing 127-B/D HTTP probe. **Source** shows: Android HTTPS443 to Nginx, private loopback Uvicorn 127.0.0.1:8000 / one worker, separate `X-BotKing-Key` pairing key, Dhan `access-token` + `client-id` header over HTTPS443, consent OAuth authentication to `auth.dhan.co`, quota 1/sec for LTP and 3s for chain, 30s response 429 cooldown, and read-only market/option routes. Dhan profile-based subscription and live exchange-timestamp verification are NOT established by `/dhan/status`; actual host/systemd configuration is not inferred from source.
- **Follow-up source and test commits:** [c2dfd439](https://github.com/vaishnavi596/volume-king/commit/c2dfd43986093cd4faec4b7469f6de9ca32b53fd) adds a regression that the per-process quote gate must run with a **single Uvicorn worker** as configured by installer. [cbca474e](https://github.com/vaishnavi596/volume-king/commit/cbca474eb76ae11a3a248df5f416470cb9c66851) adds metadata-only outbound OAuth TLS443/ `auth.dhan.co` reachability to the operator's audit, in addition to `api.dhan.co` and loopback8000. [527ab932](https://github.com/vaishnavi596/volume-king/commit/527ab93205f2c570c68ddac907a9b9fc6e94b77f) checks this network path in source-level regressions.
- **Intermediate full CI confirmed:** [run 43792643011](https://github.com/vaishnavi596/volume-king/actions/runs/43792643011) at `5a4f73b5` **846 tests PASS / SUCCESS**, verified full job log; final source/test `527ab932` workflow [43792941657](https://github.com/vaishnavi596/volume-king/actions/runs/43792941657) is **in progress** at this checkpoint.
- **No live Oracle execution** (SSH/credentials unavailable). Do not claim that actual Oracle public 443/proxy/cert, loopback8000, Dhan 443 outbound/auth, service-user access, 24h OAuth token/data-plan permission, verified 51+3/equities/options, or disabled order routes are proven until operator-safe runtime audit. Source changes NOT deployed, Oracle production NOT restarted, no credential change or signed 2.3.127 APK. Live orders kept OFF.


## 2026-11-16 — Server-to-Dhan S2D final offline CI confirmed

- **Latest audited source/test SHA:** [527ab93205f2c570c68ddac907a9b9fc6e94b77f](https://github.com/vaishnavi596/volume-king/commit/527ab93205f2c570c68ddac907a9b9fc6e94b77f). [BOT KING Offline Regression 43792941657](https://github.com/vaishnavi596/volume-king/actions/runs/43792941657): **completed SUCCESS / 846 tests / OK**, verified full job `133055266288` log. Covers quote pacing, no redirect token transport, authenticated server/key contracts, operator-only OAuth/legacy token readiness, one Uvicorn worker, private 8000 and credential-free outbound 443 checks.
- **Scope reminder:** This is offline/source CI only; *none* of the updated scripts or backend patches have been run/deployed on Oracle in this chat. No evidence that live production's public 443, private 8000, outbound Dhan 443, OAuth session permissions/24h validity, active Data API subscription, real 51/3 quote/option chain data or installed Android refresh are currently working. Current session's unauthenticated public-domain resolution attempt failed from this tool environment, not proof of host outage. Do not claim `Server ↔ Dhan all enabled` without owner-operated read-only Oracle evidence.
- **Next acceptance:** with authorized Oracle access, perform the exact reviewed source/config diff and timestamped backup before applying any runtime changes; execute `backend/audit-oracle-dhan-readonly.sh` and `scripts/check_127_oracle_readonly.py` on approved host without exposing credentials. In particular check `/v2/profile` fields `tokenValidity`, `dataPlan`, `dataValidity`, `activeSegment` without printing secrets; confirm 51 equities and three indices, selected equity, RELIANCE/HDFCBANK listed expiries/ATM CE-PE. Only then consider APK v2.3.127 and mobile QA. Live orders OFF.


## 2026-11-16 — S2D Oracle 8000 listener fail-closed source repair

- **Scope:** GitHub backend ↔ customized Oracle backend audit, source-only safety improvement. Branch `fix/botking-joint-audit-70-15-20261115`. Prior verified source CI 43792941657 at `527ab932`: SUCCESS, 846 offline tests; this is NOT Oracle production proof.
- **Confirmed bug in source audit:** `backend/audit-oracle-dhan-readonly.sh` previously passed if *any one* `ss` entry contained `127.0.0.1:8000`. A second `0.0.0.0:8000` or `[::]:8000` listener would not be rejected; that was an unsafe false-positive in port auditing (not evidence that Oracle actually has an exposed second listener).
- **Fix:** `a27f32a7` adds `only_private_8000_listener` validator, requiring at least one listener and every returned local endpoint to equal `127.0.0.1:8000`. No network credentials, configuration changes or production writes.
- **Regression:** `dbd13dfd` adds mock `ss` checks for normal, missing, IPv4 wildcard, IPv6 wildcard and mixed listener cases; `5245b0c8` corrects test regex/newline escapes and assertion. The final CI run `43795368582` was **in_progress at journal-writing time**; do not report tests PASS until completed and logs verified.
- **Oracle/server evidence:** No SSH access or production script execution, no deployed `dhan_feed.py` comparison, no real Dhan OAuth/entitlement or 51+3 quotes. User's earlier systemd output shows Uvicorn intended single-worker loopback configuration, but not that every network listener was checked. Absolutely no Oracle server edits/restarts/token rotation, no APK build and live orders remain disabled.
- **Next:** Verify run `43795368582`; have an authorized Oracle operator run read-only source parity and port audit (with appropriate sudo, no secrets printed), compare active Oracle `dhan_feed.py` / `server.py` with GitHub cautiously (Oracle has additional routes), back up exact files and runtime state before any targeted production patch, then verify authenticated data delivery and only later APK acceptance.


## 2026-11-16 — S2D strict port audit CI PASS and owner Oracle socket evidence

- GitHub CI workflow [43795368582](https://github.com/vaishnavi596/volume-king/actions/runs/43795368582) for `5245b0c8` finished **SUCCESS** (verified Actions status/conclusion); this verifies source regression at that commit, not Oracle deployment. Test count was not independently extracted.
- **User-supplied Oracle output:** `LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:*`. This supports an IPv4 **loopback listening socket** on port 8000; the `0.0.0.0:*` value appears in the *peer address* column and is NOT a public local binding. A full `ss` snapshot is still needed to exclude additional IPv6/public listeners; do not assert complete firewall or listener audit.
- The user's pasted terminal transcript contains no actual `HTTP 200` line for `/health` and no source-file hashes. **Local HTTP health, backend binary parity, OAuth authorization, Dhan 51+3 response and profile entitlement stay unverified by this particular output.**
- No Oracle code/config edit, service restart or Dhan key/token operation performed. Next safe probe: `sudo ss -H -ltn '( sport = :8000 )'`, `curl -sS --max-time 8 -o /dev/null -w 'HTTP %{http_code}\\n' http://127.0.0.1:8000/health`, SHA256 of deployed adapter/server, then curated source diff and targeted patch with exact backups only if needed.


## 2026-11-16 — S2D Oracle pasted terminal output reconciliation

- Owner's follow-up terminal output was interleaved/garbled, with the clean `sudo ss -H -ltn '( sport = :8000 )'` result `LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:*`. It shows an IPv4 loopback local listener; the wildcard is the peer column. No additional listener appeared in this pasted `ss` result.
- The owner output did **not** show a reliable `curl` HTTP result for `/health` or `https://api.dhan.co/v2/profile`, nor SHA256 file fingerprints; those checks are **NOT VERIFIED**, not PASS/FAIL. The URL/echo strings and prompt fragments were interleaved; avoid deriving network errors from the corrupted paste.
- Provided a single-line, read-only health and unauthenticated Dhan TLS connectivity probe to avoid multiline paste corruption. An unauthenticated Dhan HTTP401/403 may demonstrate endpoint reachability only, not OAuth, token, Data Plan or LTP entitlement.
- No GitHub backend source changes, Oracle deploy/restart, credential rotation or APK build in this checkpoint. Pending: usable health/Dhan HTTP outputs, Oracle file fingerprints/source comparison, authorized read-only authenticated checks, and targeted backup-before-deploy if a concrete gap is found.


## 2026-11-16 — S2D owner Oracle local health and unauthenticated Dhan HTTPS PASS

- **Direct operator-supplied Oracle outputs:** `LOCAL HTTP 200` on `http://127.0.0.1:8000/health` and `DHAN HTTP 401` on credential-free `https://api.dhan.co/v2/profile` (explicit direct/no-proxy HTTPS connection). This establishes local FastAPI HTTP readiness and Dhan HTTPS endpoint reachability. Dhan's 401 is **expected without credentials**; it is NOT an OAuth/token/plan/market-data authorization PASS.
- Earlier `ss` shows only `127.0.0.1:8000` for the reported snapshot; no exposed local listener shown. Nginx external 443, actual broker token status, `dataPlan`/`dataValidity`, protected pairing-key flows, authenticated 51+3 quote delivery and source-file parity remain unverified in this new check.
- **No production change or restart**, no Dhan credential change and no new APK. Next: compare SHA256/deployed code and run existing safe paired `/dhan/status` probe without exposing the pairing key; independently check entitlement/real market requests under authorized operator controls. Keep `live_orders_enabled=false`.


## 2026-11-16 — Owner Oracle Dhan adapter SHA256 captured (comparison pending)

- Owner terminal provided SHA256 of deployed `/opt/bot-king-server/dhan_feed.py`: `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`. This proves a file was hashed, NOT that it matches GitHub, includes the quote gate, or is deployed in the currently running process.
- Terminal `-bash: ate: command not found` is a stray/incomplete shell input; it is not a Dhan failure. No `server.py` SHA256 or actual adapter diff supplied.
- GitHub working branch backend adapter contains `QUOTE_MIN_INTERVAL_SECONDS = 1.05`; Oracle rate-gate parity still PENDING. Next: inspect the deployed adapter's gate markers read-only, compare with a trusted GitHub copy, then back up and stage only verified necessary modifications. No Oracle edit, restart, token change or APK build.


## 2026-11-16 — S2D Oracle deployed Dhan adapter quote gate absence confirmed by owner grep

- **Oracle operator read-only output:** `grep -nE 'QUOTE_MIN_INTERVAL_SECONDS|_quote_lock|_quote_next_allowed|DhanRateLimitError' /opt/bot-king-server/dhan_feed.py` returned `DhanRateLimitError` occurrences at lines 20, 52, 60, 94, 128, 165, **no quote-gate marker**. This proves the named GitHub 1.05s gate implementation is absent from the Oracle file as inspected; the existing cooldown/historical/option guards are present. It does not prove all alternative quote pacing methods absent without inspecting the actual method code.
- **GitHub source:** `backend/dhan_feed.py` has class-shared `_quote_lock`, `_quote_next_allowed`, `QUOTE_MIN_INTERVAL_SECONDS = 1.05`, and a gated `/marketfeed/ltp` request in `_post`. Direct whole-file replacement on Oracle is disallowed: production adapter and server may contain custom behavior; source diff and dependency tests required first.
- **State:** Required Oracle source parity patch identified but **NOT YET DEPLOYED**; no Oracle backup, SSH modification, restart or live authenticated Dhan quote probe in this turn. Request read-only first ~110 lines of Oracle adapter with no secrets, then create an anchor-verified minimal staging patch, exact backup, syntax/test/health checks and rollback strategy. Maintain single Uvicorn worker and read-only/no order policy.


## 2026-11-16 — S2D Oracle adapter exact-layout staging patch and tests

- User supplied actual first 115 lines of Oracle `/opt/bot-king-server/dhan_feed.py`. **Confirmed material differences** from GitHub: `_historical_retry_after`, `_option_retry_after`, `_intraday_next_allowed` and separate 30s cooldowns; `QUOTE_MIN_INTERVAL_SECONDS`, `_quote_lock`, `_quote_next_allowed` not present. The source header also has a duplicate `_option_retry_after = 0.0`; clean up only with a separate justified and tested patch. Avoid swapping GitHub adapter wholesale.
- [b358421d](https://github.com/vaishnavi596/volume-king/commit/b358421d4c35d34b2169d0f165be7438e3ed4aaf): added `scripts/oracle_s2d_quote_gate_stage.py` for **staging only**, with AST/exact text anchors, pre-existing quote marker detection, retention of separate historical/option cooldowns, class-shared quote lock and 1.05-second request-start floor. Produces independent before/staged files with SHA256+syntax checks; no live file writing, no service restart, no credential output.
- [fc442e94](https://github.com/vaishnavi596/volume-king/commit/fc442e9408fce8ce844f6f7f9bdc8e2055b2b8e8): synthetic offline tests for source preservation, fail-closed changed layouts and cross-instance two-quote pacing with fake clock and fake HTTP opener, no live broker access. GitHub workflow run `43796217369` **in progress when entered**; no CI PASS claim until verified.
- **Deployment NOT authorized by test alone**: first verify the source is unchanged and its observed SHA256 equals `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`. Review the entire proposed diff and test it against a complete isolated Oracle source copy; only then guarded production backup, controlled swap and restart with rollback/health checks. Oracle actual token/session and entitlement remain unknown; live orders OFF. No APK build.


## 2026-11-16 — S2D second Oracle adapter SHA256 unchanged; staging gate

- User re-ran `sudo sha256sum /opt/bot-king-server/dhan_feed.py` and supplied `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`, matching the earlier owner observation exactly. **Oracle adapter byte integrity relative to prior observation PASS**; this does NOT imply patched quote pacing already deployed.
- Latest available check of CI `43796217369` still reports `in_progress`; do not claim PASS. Staging-only script is committed at `b358421d` and regression at `fc442e94`. Next owner action: download source pinned to reviewed commit, validate `python3 -m py_compile`, run staging script with `sudo` only after rechecking SHA256, inspect generated proposed diff and backup. No live file edit/restart/order/token/APK performed.


## 2026-11-16 — S2D staging command issued; staging verdict not yet visible

- User-supplied Oracle terminal shows `python3 -m py_compile oracle_s2d_quote_gate_stage.py` returned to prompt without error and `sha256sum -c` explicitly printed `/opt/bot-king-server/dhan_feed.py: OK` for expected SHA256 `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`. These establish script syntax and unchanged production input at the probe time.
- User invoked `sudo python3 /tmp/oracle_s2d_quote_gate_stage.py`, but the pasted output stops there: **no `S2D_STAGE_PASS`, `PRODUCTION_CHANGED`, `PROPOSED`, `BACKUP` or traceback yet**. STAGING STATUS = NOT VERIFIED; do not mark PASS or perform production deployment.
- Current GitHub CI `43796217369` still reported `in_progress` at latest lookup. Next verify staging command exit and exact proposed/backup artifacts, inspect generated diff and complete CI before any live update. No evidence of production edit, restart, credentials change or new APK.


## 2026-11-16 — S2D historical failed CI runs reconciled with corrected PASS

- User supplied failure notices for old port-listener audit runs: [43795320471](https://github.com/vaishnavi596/volume-king/actions/runs/43795320471) at `a27f32a7`, and [43795340118](https://github.com/vaishnavi596/volume-king/actions/runs/43795340118) at `dbd13dfd`. Both were truly **FAILED**, confirmed from GitHub Actions job logs. Do not rewrite their historical status.
- **Root causes from job logs:** first failed an obsolete source-text test expecting `127[.]0[.]0[.]1:8000`, after validator changed to strict `awk` comparison; second failed the new `test_port_8000_rejects_secondary_public_or_ipv6_listener` regex fixture, showing `AssertionError: unexpectedly None : missing strict port listener validator`. These were offline regression/test assertions, **not real Oracle runtime failures**.
- **Superseding fix:** [5245b0c8](https://github.com/vaishnavi596/volume-king/commit/5245b0c8803c2f064b1ba2913cdc82c85b0b9f47), CI [43795368582](https://github.com/vaishnavi596/volume-king/actions/runs/43795368582) **SUCCESS / 847 tests / OK**, verified from completed job log. No need to rerun the two old commits.
- **Separate next S2D staging CI:** [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) for `fc442e94` still **in_progress** at latest lookup; do not promote its quote gate staging code to production-ready yet. Oracle staging execution output still absent. No deploy/restart, credential rotation or APK build.


## 2026-11-16 — S2D Oracle staging invocation failed due to pasted command concatenation

- Owner's Oracle shell showed `python3: can't open file '/tmp/oracle_s2d_quote_gate_stage.pyecho': [Errno 2] No such file or directory` after two commands were pasted together without separation. The actual staged script name is `oracle_s2d_quote_gate_stage.py`; the incorrect `.pyecho` path is a concatenation artefact, not evidence of missing correct script or Dhan/Oracle failure.
- **No successful stage output**, no `S2D_STAGE_PASS`, backup/proposed path, diff or deploy observed; staging NOT VERIFIED. Corrective operator instruction is a single independent command with an explicit existing-file check, and NO production install/restart.
- GitHub source CI `43796217369` still `in_progress` at latest query; do not declare gate patch CI passed. Prior original-file SHA256 verification and localhost health 200 remain separate observed checks.


## 2026-11-16 — S2D staged quote gate validated on Oracle source; production unchanged

- **Owner-supplied executed Oracle command:** `test -f /tmp/oracle_s2d_quote_gate_stage.py && sudo python3 /tmp/oracle_s2d_quote_gate_stage.py` completed and emitted `S2D_STAGE_PASS: YES`, `PRODUCTION_CHANGED: NO`, `PYTHON_SYNTAX: PASS`. Previous `.pyecho` paste failure was corrected.
- **Oracle stage artifacts (operator-reported):** backup `/opt/bot-king-backups/s2d-stage/dhan_feed.s2d.before.20261116T031325151738Z.py`; proposed `/opt/bot-king-backups/s2d-stage/dhan_feed.s2d.proposed.20261116T031325151738Z.py`.
- **Operator-reported SHA256:** original `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`; staged proposal `beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c`. Patch script's AST/layout validation and syntax check passed on **actual Oracle source**.
- **Critical limits:** Staging output does NOT establish diff review, unit/integration tests on staged complete Oracle file, or production deployment. Prior `/health` HTTP200 was verified in an earlier separate probe; latest pasted output interleaving does not provide a fresh successful health HTTP code. No source file changed, no service restart, token rotation, order feature or APK build.
- **Next gate:** review `sudo diff -u` of exact backup and staged path, ensure only quote lock/pacing plus helper import are added and production historical/option 429 cooldown branches unchanged; verify staging regression CI [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) completion (still in_progress in latest lookup) and run unit/behavior checks against staged module before controlled deploy.


## 2026-11-16 — S2D owner-provided exact Oracle proposed diff reviewed, production unchanged

- Owner pasted the complete unified diff between staged `dhan_feed.s2d.before.20261116T031325151738Z.py` and `dhan_feed.s2d.proposed.20261116T031325151738Z.py`. **Diff-scope review PASS:** only one `contextlib.nullcontext` import, three quote gate class declarations, and substitution of `/marketfeed/ltp` opener block with class-shared lock, minimum 1.05s gap and cooldown recheck. The existing `_historical_retry_after`, `_option_retry_after`, `_intraday_next_allowed`, HTTP error behavior and read-only endpoint allowlist were *not altered by this diff*.
- Staging script previously reported syntax PASS, original SHA256 `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`, staged `beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c`. Syntax and diff-scope checks do **not** prove concurrency/429 runtime behavior or data delivery.
- CI run `43796217369` remains `in_progress` at latest GitHub status lookup. **Production still unchanged** and no successful mobile test, server restart or new APK. Next stage: offline behavior checks using a fake opener on exact staged file (no token), verify CI, and if both pass, explicit atomic backup/rollback controlled deployment and localhost/Dhan quote smoke. Guard against network testing with actual token before authorization checks.


## 2026-11-16 — Standing S2D execution and journal continuity rule

- **Operator directive:** Continue jointly audited BOT KING backend work without stopping at explanations; append **every substantive Oracle command result, GitHub patch, test/CI outcome, backup, deployment/rollback result and unresolved item** to `docs/BOT_KING_WORK_LOG.md` on the working branch. Mark source-only, offline-CI, owner-terminal Oracle, live/server verification and Android mobile proof **separately**; link commits/runs and preserve historical failures. Do not call unrun actions PASS.
- **Current verified handoff:** Oracle staged quote-gate script reported PASS (backup and proposal), source SHA256 `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`, proposal `beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c`. Operator-supplied unified diff reviewed as limited to LTP quote pacing; no production patch or restart. Last requested stage `py_compile` and SHA recheck **not yet supplied**.
- **CI lookup at this entry:** [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) remains `in_progress`; do not mark new S2D staged patch validated by CI. Earlier port listener fix CI [43795368582](https://github.com/vaishnavi596/volume-king/actions/runs/43795368582) finished SUCCESS with 847 offline tests (verified logs).
- **Safety gates:** Do not overwrite Oracle's customized `dhan_feed.py` or `server.py` wholesale; backup and inspect exact targeted diffs, syntax and behavior tests first. Keep order execution disabled, no token exposure/rotation, and no APK until source ↔ Oracle runtime contract + mobile smoke checks are resolved.


## 2026-11-16 — COMPLETE CHAT RECONCILIATION: backend-to-backend S2D evidence ledger and handoff

**Purpose:** Retrospective roll-up of **this conversation's** Oracle operator terminal outputs, GitHub commits, failures/corrections, staging artifacts, findings and pending next steps. Original chronological entries earlier in this journal are retained as the audit trail, including initially unresolved states that were later resolved. Do not conflate a past observation with current production state.

### 1. GitHub source edits, tests and CI

| Scope | GitHub evidence | Final verified result |
|---|---|---|
| S2D source audit identified shared Dhan LTP rate-gate requirement | GitHub \`backend/dhan_feed.py\`: class-shared \`_quote_lock\`, \`_quote_next_allowed\`, \`QUOTE_MIN_INTERVAL_SECONDS=1.05\`; single Uvicorn worker required | Present in GitHub source, **not then present in Oracle production** |
| Strict Oracle TCP 8000 audit script | \`a27f32a7\`, \`backend/audit-oracle-dhan-readonly.sh\` | All port 8000 local listener addresses must be \`127.0.0.1:8000\`; source patch committed; Oracle production audit script execution not proven |
| Strict listener negative regressions | \`dbd13dfd\`; test fixture correction \`5245b0c8\` | Intermediate CI runs [43795320471](https://github.com/vaishnavi596/volume-king/actions/runs/43795320471) **FAILED**, [43795340118](https://github.com/vaishnavi596/volume-king/actions/runs/43795340118) **FAILED**; corrected [43795368582](https://github.com/vaishnavi596/volume-king/actions/runs/43795368582) **SUCCESS, 847/847 tests OK** per completed job logs |
| Historical failure root causes | Actual Actions job logs | Run #1487 obsolete source-text assertion expected former escaped \`127[.]0[.]0[.]1:8000\`; run #1488 regex overescaping yielded \`AssertionError: unexpectedly None: missing strict port listener validator\`; **test-code errors, not Oracle faults** |
| Fail-closed Oracle-specific quote gate staging tool | \`b358421d\`: \`scripts/oracle_s2d_quote_gate_stage.py\` | GitHub committed; stages separate before/proposed files with syntax check; production target not changed |
| Offline staging regression | \`fc442e94\`: \`tests/test_oracle_s2d_quote_gate_stage.py\` | Tests added for changed-layout rejection, custom cooldown preservation, fake opener/timing. Corresponding CI [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) was **IN_PROGRESS on latest checked response**; no PASS claimed for this separate workflow |

### 2. Oracle operator command outcomes (source: user-pasted terminal only)

| Command / probe | Actual evidence | Accurate interpretation |
|---|---|---|
| \`sudo ss -H -ltn '( sport = :8000 )'\` | \`LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:*\` (repeated) | IPv4 **localhost** listener present, no second listener in supplied snapshot; wildcard is peer address, not exposed bind; full external firewall/IPv6 policy not independently proven |
| \`curl ... http://127.0.0.1:8000/health\` | \`LOCAL HTTP 200\` in clean output | Local FastAPI health **PASS at that time**; later corrupt/interleaved command copy did *not* produce a new valid health result |
| \`curl --noproxy '*' ... https://api.dhan.co/v2/profile\` without token | \`DHAN HTTP 401\` | HTTPS/TLS reachability to Dhan REST endpoint **PASS**; without token, **NOT OAuth authentication, plan entitlement, or live quotes proof** |
| \`sha256sum /opt/bot-king-server/dhan_feed.py\` | \`7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75\` repeated and \`sha256sum -c\` printed \`/opt/bot-king-server/dhan_feed.py: OK\` | Oracle source-byte integrity **PASS against observed prior hash**, *not* GitHub byte-for-byte parity or running worker module proof |
| \`grep -nE 'QUOTE_MIN_INTERVAL_SECONDS|_quote_lock|_quote_next_allowed|DhanRateLimitError' ...\` | Only DhanRateLimitError lines 20,52,60,94,128,165 | GitHub's named 1.05-second shared quote gate markers absent from live Oracle source at inspection time; other custom pacing exists |
| \`sed -n '1,115p' /opt/bot-king-server/dhan_feed.py\` | Existing \`_intraday_next_allowed\`, \`_historical_retry_after\`, \`_option_retry_after\`, 3s chain pacing, HTTP429 30s cooldown, LTP logging; duplicate \`_option_retry_after = 0.0\` declaration | **Oracle code differs materially** from generic GitHub adapter. Never wholesale overwrite custom production file; duplicate assignment is a cleanup candidate only after separate tested patch |
| \`python3 -m py_compile /tmp/oracle_s2d_quote_gate_stage.py\` and original \`sha256sum -c\` | No syntax error; \`OK\` on original SHA | Script syntax and unchanged input **PASS** |
| Interleaved multiline paste | \`-bash: ate: command not found\`; \`python3: can't open file '/tmp/oracle_s2d_quote_gate_stage.pyecho'\` | Terminal command-concatenation mistakes only; **not** evidence of Dhan API or service failure |
| \`test -f /tmp/oracle_s2d_quote_gate_stage.py && sudo python3 /tmp/oracle_s2d_quote_gate_stage.py\` | \`S2D_STAGE_PASS: YES\`, \`PRODUCTION_CHANGED: NO\`, \`PYTHON_SYNTAX: PASS\`, backup/proposed paths/hashes | Real Oracle **staging PASS** on source; service not deployed/restarted |
| \`sudo diff -u ...before...py ...proposed...py\` | Owner supplied unified diff: one nullcontext import, 3 class quote-gate members, \`_post\` LTP lock+1.05s gate+cooldown recheck | **Diff-scope review PASS**; custom historical/option cooldown and error handling untouched. This is not behavioral load-test PASS |
| Last requested recheck \`sudo python3 -m py_compile <proposed> && sudo sha256sum ...\` | No later terminal result in this chat | **NOT YET VERIFIED**; no extrapolated PASS |

### 3. Oracle Staging artifacts — exact operator evidence

- **Original:** \`/opt/bot-king-server/dhan_feed.py\` SHA256 \`7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75\`.
- **Independent before copy:** \`/opt/bot-king-backups/s2d-stage/dhan_feed.s2d.before.20261116T031325151738Z.py\`.
- **Independent proposed copy:** \`/opt/bot-king-backups/s2d-stage/dhan_feed.s2d.proposed.20261116T031325151738Z.py\`, SHA256 \`beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c\`.
- All these file paths and hashes were supplied by Oracle operator, not directly accessed by the assistant. **No evidence of Oracle production-file modification, service restart, secrets rotation, authenticated quote calls or Android APK build.** Preserve these files for comparison and rollback planning.

### 4. Prior and current journal commits in this chat

The journal itself was updated repeatedly as evidence arrived. Relevant append-only history: \`e2ecce75\` (listener guard), \`b8f28d11\` (CI/sockets), \`0b07c2e8\` (garbled paste), \`59557905\` (health200/Dhan401), \`57e844b5\` (Oracle adapter hash), \`3f9ad7d0\` (missing quote gate), \`461c7af2\` (staging tool/tests), \`7c67c792\` (unchanged original hash), \`e5a40177\` (staging initially unverified), \`d1b676f1\` (failed old CI reconciled), \`1fd6b310\` (command concatenation), \`d0867939\` (staging PASS), \`87497f35\` (diff reviewed), \`220987ac\` (standing journal rule). Current recap is supplementary, not a replacement of entries above.

### 5. Outstanding execution gates and no-overclaim rules

1. **Verify GitHub staged-patch CI** 43796217369 to final result; if failed, inspect exact logs, repair on working branch, rerun and journal every outcome. Corrected port-listener CI 43795368582 already succeeded independently.
2. **Offline validate exact Oracle proposed module** (no broker calls, no secrets): staged Python syntax/hash and mock-opener quote spacing, shared instance lock, HTTP429 cooldown, historical/options unchanged. Avoid creating \`__pycache__\` in production code location if possible.
3. **Before any production edit:** exact current original file SHA match, preserved separate backup, inspect source diff and write atomic target-replacement/rollback procedure. Keep single worker and test \`/health\`, authenticated \`/dhan/status\`, index/51 quote results within provider rate limits without logging keys. Note provider data freshness and holiday/market-hours uncertainty.
4. **Backend parity next:** customized Oracle \`server.py\` routes/headers versus GitHub \`backend/server.py\`, options and 5 watchlist semantics, private localhost8000 ↔ Nginx HTTPS443, outbound Dhan HTTPS443, OAuth versus pairing-key separation. Do not copy GitHub server.py over Oracle server.py.
5. **APK later:** Only after backend/runtime/data verification and complete test journal. Keep read-only market data and \`live_orders_enabled=false\`; do not represent paper mode as live order execution.

**Working policy (user instruction):** Every substantive new command/result, edit, add/delete, CI, source-vs-Oracle mismatch, backup, deployment or unresolved fault must get an accurately scoped append entry in this GitHub journal on the working branch. Batch related work to save time, preserve production safety, and do not call unverified states PASS.


## 2026-11-16 — PRECEDING CHAT AUDIT: Nov 15–16 S2D & joint-backend handoff parity check

**Request:** Check the chat immediately before the current S2D conversation and verify its work was entered in the journal. Audit performed against the existing journal on working branch \`fix/botking-joint-audit-70-15-20261115\` plus recovered preceding-conversation context. This entry supplements rather than duplicates the earlier Nov 16 \`Server-to-Dhan S2D\` source/CI audit, the earlier \`Backfilled audit of previous two work chats\`, and the current-chat \`COMPLETE CHAT RECONCILIATION\`.

### A. Already covered in the existing work log — cross-checked

- **Previous conversation's principal S2D audit:** Android/BOT KING ↔ Nginx HTTPS 443 ↔ private FastAPI \`127.0.0.1:8000\` one Uvicorn worker; server ↔ \`api.dhan.co\` and \`auth.dhan.co\` HTTPS 443. Dhan \`access-token\` and \`client-id\` are broker headers, while \`X-BotKing-Key\` is a separate pairing header. Redirect/proxy precautions and metadata-only audit must not leak credentials. These rules and intended server config were already recorded as *GitHub source*, not automatically verified Oracle production configuration.
- GitHub shared 1.05-second upstream LTP request gate, option-chain 3s pacing and 429 cooldown 30s, single-worker requirement, script \`backend/audit-oracle-dhan-readonly.sh\`, source-level regression changes \`c2dfd439\`, \`cbca474e\`, \`527ab932\`. Previous chat's final confirmed [CI 43792941657](https://github.com/vaishnavi596/volume-king/actions/runs/43792941657) at \`527ab932\`: **846/846 offline PASS**. Previously journaled; do not conflate with newer 847-test listener-guard CI.
- **Important unverified production items from that chat:** public Nginx 443 policy/cert/routes and firewall, actual Oracle token/OAuth session validity, Dhan Data Plan/entitlement, source parity and live quote freshness. An unauthenticated profile call is a connectivity probe only. Production backend was NOT changed by that S2D source-only audit. Later/current-chat operator evidence is recorded separately.
- Preceding Nov 15 joint-backend handoff previously logged: source Dhan-only registry and selected-equity routes, Oracle S15 targeted server patch deployed (per prior operator evidence), 51 equity / 3 index batch quote probes (freshness unverified), S18 70-unique-across-5-list guard staged but not proven deployed, offline app/Android builds separate from runtime acceptance. Existing journal retains these checkpoints.

### B. Clarifying backfill from older steps visible in immediately preceding history

- **Nov 15 progressive source checkpoints:** Earlier project messages reported \`e6d6926b\` and **778/778 offline PASS**, followed by \`83749508\` and **788/788 offline PASS** during dynamic registry/70-quote/option work. These are *previous-conversation reported* milestones, **not independently revalidated CI run IDs in this reconciliation**. The journal had 778/788 aggregate checkpoint mentions and \`83749508\`, but \`e6d6926b\` was not explicitly indexed; indexed here to improve future handoff.
- **Oracle mapping and options limitation discovered Nov 15:** Prior operator output mapped NIFTY \`IDX_I/13\`, BANKNIFTY \`IDX_I/25\`, SENSEX \`IDX_I/51\`, HDFCBANK \`NSE_EQ/1333\`, ICICIBANK \`NSE_EQ/4963\`, RELIANCE \`NSE_EQ/2885\`. Expiry probes previously showed index responses HTTP 200 but the three equity expiry requests initially returned HTTP 422 because server/adapter route validation was index-only. Later S15 targeted production route patch was reported deployed; **these earlier failures must not be mistaken for an ongoing failure without new end-to-end verification**.
- **Prior Dhan futures OI evidence (S06):** A previous conversation reported a NIFTY November contract ID \`61471\` returning 74 intraday OI/close/timestamp points and OI values approximately 12,016,290 to 11,983,400; this was a point-in-time upstream data probe, **not** proof of general Futures directional signal scoring or fresh/live signal eligibility. Record as historical operator/assistant-reported evidence, pending independent replay and signal-data integration.
- **Product constraints stated in prior chat:** 200–300+ selectable instrument mapping scalability, five separate factor/filter scores with News and Futures requiring independent verified sources, and future two-way trade-path planning. The runtime must stay **market-data read-only and \`live_orders_enabled=false\`**; do not treat architectural discussion of app→server→broker orders as approval to enable or deploy real orders.
- **Previous app issue:** user-reported v2.3.125 first-login Watchlist refresh failing despite cached prices. Source fixes and CI do not constitute Android installed-device PASS. Keep this issue visible for the later APK/mobile acceptance sequence.
- **Source/runtime distinction:** On Nov 16 current chat, Oracle local \`/health\` HTTP200 and direct unauthenticated Dhan HTTPS401 were observed, and the Oracle-specific 1.05-second quote gate was **missing from deployed source** even though it existed in GitHub; staging and exact diff later passed, but no production installation or service restart is evidenced. See newer entries for exact SHA256, backup/proposed file paths and regression status.

### C. No-duplication audit disposition

- **Covered before this entry:** Core preceding-chat S2D rule matrix, HTTPS ports, pairing/auth separation, source patches and final 846-test PASS, prior S15/S18/S19 status, current-chat commands, two historical listener test failures and corrective 847-test PASS, and Oracle staged gate patch evidence.
- **Newly clarified here:** \`e6d6926b\` 778-test historical marker, the progression to \`83749508\`/788, earlier index/equity mapping and historical HTTP422 boundaries, S06 OI observation, 200–300+ scalability intent, and the explicit distinction between two-way *design goal* versus no-live-orders *implementation policy*.
- **Still not proven:** source⇄Oracle full \`server.py\` API parity, actual current Dhan OAuth/Data Plan/live-price freshness, latest S2D staging patch CI final result if pending, staged module behavioral testing on Oracle and controlled deployment, Android device acceptance. Do not mark these PASS without new evidence.

**Journal policy:** Preserve both chat recaps and individual commands; append each subsequent GitHub commit, Oracle terminal observation, CI failure/recovery and deployment/rollback with exact evidence. Do not overwrite earlier historical FAILED/UNKNOWN records when later work resolves them.


## 2026-11-16 — Previous chat's final Oracle systemd command actually executed (owner result)

- **Origin:** Owner explicitly identified this as the previously unfinished *last Oracle terminal command* from the immediately preceding chat, executed now. Command: `sudo systemctl show bot-king.service -p User -p ExecStart --no-pager`. This is fresh user-supplied Oracle terminal evidence; do not mistake interleaved pasted commands for executed checks.
- **Actual systemd output:** `User=opc`; `ExecStart` executable `/opt/bot-king-server/.venv/bin/python`, args `-m uvicorn server:create_app --factory --host 127.0.0.1 --port 8000 --workers 1 --no-access-log --limit-concurrency 8 --timeout-keep-alive 5`; start timestamp `Sun 2026-11-15 17:50:37 GMT`, PID `579875`, `stop_time=[n/a]`, `status=0/0`. These are **service configuration/process metadata**, not a completed current authenticated data-path test.
- **Conclusion:** Expected single Uvicorn worker and loopback-only bind settings are present in the systemd launch arguments, compatible with the GitHub class-shared 1.05s Dhan quote lock design. One worker does not establish source-file parity, quote gate deployment, valid Dhan credentials, fresh quotes or secure firewall by itself. Historical and option pacing remain Oracle-custom behavior.
- **Not proven in pasted transcript:** `sudo ss -lntp | grep -E ':(443|8000)([[:space:]]|$)'`, `sudo nginx -t`, and `curl --noproxy '*' ... https://api.dhan.co/v2/profile` appeared interleaved around the prompt but their corresponding outputs are not visible. Do not mark these commands newly PASS or FAIL based on this paste. Earlier separately verified `LOCAL HTTP 200` and unauthenticated `DHAN HTTP 401` retain their own historical evidence.
- **Outstanding:** source-versus-production quote gate patch still staged only (before/proposed copy and diff reviewed). No production file swap, process restart or APK build confirmed. Review proposed module behavior CI and isolated tests, check current health and nginx/443 endpoints, then choose guarded deployment with rollback.


## 2026-11-16 — Oracle Nginx syntax and 443/8000 listener real-output evidence

- **Owner-supplied actual command and output:** `sudo nginx -t; sudo ss -lntp | grep -E ':(443|8000)([[:space:]]|$)'`. Nginx printed `nginx.conf syntax is ok` and `configuration file ... test is successful`: **NGINX SYNTAX PASS**. This does not prove live TLS certificate, public routing, upstream responses, or external firewall.
- **Socket evidence:** `LISTEN 0 2048 127.0.0.1:8000 0.0.0.0:* users:(("python",pid=579875,fd=6))` — backend local IPv4 binding/pass for reported listener snapshot; systemd `ExecStart` previously identified single Uvicorn worker, same process PID `579875`.
- **Nginx socket evidence:** `LISTEN 0 511 0.0.0.0:443 0.0.0.0:* users:(("nginx",pid=392356,fd=6),("nginx",pid=392355,fd=6),("nginx",pid=103346,fd=6))` — IPv4 HTTPS listener bound on all interfaces, expected proxy front end. This is not proof of externally reachable 443, TLS validity, or complete Nginx proxy contract.
- **Joint status:** Oracle port design and Nginx syntax **PASS**, backed by operator evidence; quote adapter 1.05s gate remains **STAGED ONLY** with Oracle backup and reviewed diff, not confirmed deployed. CI [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) still **in_progress** at latest GitHub query. Nginx external HTTPS route/health, protected API auth, Dhan entitlement/live quote freshness, staged behavior tests, backend parity and APK still **PENDING**.
- No Oracle mutation, nginx reload/restart, token rotation or order execution as a result of this audit.


## 2026-11-16 — Oracle public HTTPS /health live probe confirms TLS and gateway response

- **Operator-supplied exact result:** `PUBLIC_HTTPS=200 TLS_VERIFY=0` from a direct no-proxy `curl --noproxy '*' -sS --connect-timeout 3 --max-time 10 -o /dev/null -w 'PUBLIC_HTTPS=%{http_code} TLS_VERIFY=%{ssl_verify_result}\\n' https://botkingrajesh.duckdns.org/health` run on the Oracle host. This verifies that the specified public HTTPS URL returned HTTP 200 with successful curl TLS certificate verification from the Oracle host at probe time.
- Combined with immediately preceding Oracle `nginx -t` PASS, local Python `127.0.0.1:8000` listener and Nginx `0.0.0.0:443` listener, this is evidence that the **public health route through HTTPS is responding**, not proof of authenticated downstream API contracts, external networks beyond the Oracle vantage point, OAuth token entitlement, or quote freshness.
- No secrets were sent with the health probe; no server code changed or process restarted. Oracle quote-gate production source **still not verified deployed**; source patch staged with exact reviewed diff and backup. S2D staging CI [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369): in_progress (no final conclusion) as of this check.
- **Next:** safe status endpoint capability probing without exposing `X-BotKing-Key` and isolated staged-module behavior test; then guarded authenticated API/data checks under service-user credentials, only after CI passes.


## 2026-11-16 — Oracle public Dhan Status missing-key authorization denial verified

- **Owner-supplied Oracle curl outcome:** `DHAN_STATUS_NO_KEY_HTTP=403` for unauthenticated request to `https://botkingrajesh.duckdns.org/dhan/status` (no `X-BotKing-Key` header). **Missing-key rejection PASS** on public endpoint. No secret was printed or transmitted by this unauthenticated check.
- **Scope:** This verifies exactly one negative authorization case at the public route. It does NOT prove valid-key success, other protected endpoints, token state, credential expiry, market-data entitlement, or live quote freshness. A 403 response could have come from gateway/app policy; protected-route response body and backend request path have not been further inspected.
- Prior separate operator evidence: `PUBLIC_HTTPS=200 TLS_VERIFY=0`, `LOCAL HTTP 200`, Dhan unauthenticated profile `HTTP 401`, Nginx syntax PASS, localhost8000 and HTTPS443 listener snapshots, single-worker Uvicorn. S2D quote-gate proposal staging and diff PASS but **NO PRODUCTION DEPLOYMENT**.
- GitHub staged quote-gate test CI [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) at commit `fc442e94`: in_progress, not final at this lookup. Never infer PASS for in-progress tests. Next validate staged module against fake opener and examine CI outcome, then safely verify authenticated `/dhan/status` with runtime-sourced key without echoing its value.


## 2026-11-16 — Oracle proposed gate SHA/syntax recheck and new offline behavior probe

- **Owner Oracle terminal result after `sudo python3 -m py_compile <proposed> && sudo sha256sum <proposed> <production>`:** proposed SHA256 `beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c`, production `dhan_feed.py` SHA256 `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75`. Because `&&` continued to the hashes, proposed Python syntax check **PASS**; both observed hashes match prior stage/original proofs. **PRODUCTION ORIGINAL UNCHANGED** by this step.
- **New GitHub code** [d1db05f8](https://github.com/vaishnavi596/volume-king/commit/d1db05f8beccff2d72ae4b9fda514a724346a1e4) added `scripts/audit_oracle_s2d_staged_offline.py`: hash-pinned and symlink/production-path rejecting probe which imports only the proposed module, uses a fake opener and fake credentials, verifies two quote starts separated at least 1.04s, cross-instance 429 cooldown denial, and presence of Oracle-special historical/option/intraday pacing fields. **Not run on Oracle yet**; no broker or network calls are made by its test logic; not proof of production market data.
- **CI** stage test workflow [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369): `in_progress` / no final conclusion at this lookup. The new commit's own CI result is also not claimed PASS. **Next:** download hash-pinned offline probe to Oracle `/tmp`, run `python3 -m py_compile`, execute `sudo python3 <probe>`, inspect output and CI; only then consider guarded production deployment with backup/rollback. No Oracle live source edit or restart.


## 2026-11-16 — Oracle exact S2D staged module offline behavior PASS; cancelled CI job rerun requested

- **Owner Oracle terminal output for hash-pinned `scripts/audit_oracle_s2d_staged_offline.py`:** `S2D_OFFLINE_BEHAVIOR_PASS: YES`; `STAGED_SHA256: beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c`; `QUOTES_TESTED: 2 fake opener calls across 2 instances`; `QUOTE_START_GAP_SECONDS: 1.051`; `429_SHARED_COOLDOWN: PASS`; `ORACLE_HISTORICAL_OPTION_FIELDS: PRESENT`; `NETWORK_REQUESTS: 0`; `PRODUCTION_CHANGED: NO`. **Oracle offline functional smoke PASS**, not live server or real Dhan quotes.
- **GitHub CI accuracy correction:** [run 43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) at `fc442e94` had reached `completed/cancelled`, job `133065508071` `offline-tests` cancelled. Cancellation is NOT PASS and is not proof of a test assertion failure. GitHub connector `rerun_workflow_job` requested a rerun of exactly cancelled job 133065508071 and reported `success: true`; record the workflow's new outcome only after independent verification. Status immediately after rerun request: `in_progress`, conclusion `none`, attempt 2.
- **Safety and deployment gate:** Proposed/original hashes were independently shown stable in owner's immediately prior message. Production `/opt/bot-king-server/dhan_feed.py` remains unmodified by offline probe. Pending fresh full CI verdict, guarded service deployment and post-restart authenticated data QA. Do not enable order features or claim Dhan live data proof from mocked timings.


## 2026-11-16 — S2D staging CI 850/850 PASS, guarded production deployment prepared but not executed

- **GitHub CI rerun evidence:** [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) attempt 2, commit `fc442e94`, finished `completed/success`. Completed job log showed all three new `test_oracle_s2d_quote_gate_stage` regression cases OK and `Ran 850 tests ... OK`. Earlier cancelled first attempt remains historic; second attempt SUCCESS. Note this CI covers code at `fc442e94` and **does not by itself certify subsequent added deployment script**.
- **Oracle offline test:** owner earlier ran hash-pinned `scripts/audit_oracle_s2d_staged_offline.py` against proposed Oracle module: 2 fake quotes gap `1.051` seconds, shared 429 cooldown PASS, custom Oracle historical/option fields present, 0 network requests, production unchanged. Both original/proposal hashes and diff reviewed separately.
- [e9a3a548](https://github.com/vaishnavi596/volume-king/commit/e9a3a54897462069cc4cf1c5fb33730c6d37e178) **SOURCE ONLY** adds `scripts/deploy_oracle_s2d_quote_gate.py`: defaults to guarded dry-run; `--apply` explicitly requires exact original/staged SHA256, root, normal-file checks, compile, active pre-deploy service and local health, on-disk 0600 backup, metadata-preserving atomic replace, service restart, health verification, rollback on exceptions. Does not read broker credentials or issue trade orders. No Oracle execution, so guard functionality must be tested by operator; don't say deployed.
- [9b4ffe22](https://github.com/vaishnavi596/volume-king/commit/9b4ffe2221c24d91664441ea0453b83398b9e457) adds `tests/test_oracle_s2d_deploy_guard.py` for dry-run/backup/hash/atomic/rollback invariants. **New CI on this later commit must be checked** before using installer in production; no test result claimed yet.
- **Next:** check newest CI; on Oracle download pinned deploy script, inspect it and run dry-run *without --apply*; verify output and journal. Only then consider `--apply`, restart, local + public health, protected API/Dhan data smoke and rollback proof. Never overwrite `server.py`, change OAuth/pairing credentials, enable live orders, or build APK before backend gates pass.


## 2026-11-16 — Oracle S2D guarded deploy script dry-run PASS (no production mutation)

- **Owner Oracle terminal output** after running `sudo python3 /tmp/deploy_oracle_s2d_quote_gate.py` without `--apply`: `SOURCE_HASH: PASS`, `STAGED_HASH: PASS`, `PYTHON_SYNTAX: PASS`, `PREDEPLOY_HEALTH: PASS`, `DRY_RUN_PASS: YES`, `PRODUCTION_CHANGED: NO`. This validates the guarded deploy tool's preconditions in the actual Oracle environment and explicitly confirms that **no apply/restart was performed by this invocation**.
- Hash guard checks use original `7a8db92e8b791af89d7f6e1e14511ad53904b1e0e84c23f880657dd2a46beb75` and proposed `beccda3067e14efb750e029383919e73ce5b41410caa424f5671bfa7ce43c33c`; syntax of proposed source and localhost health 200 passed at the time of the dry run.
- **GitHub deployment-guard CI:** [43799716934](https://github.com/vaishnavi596/volume-king/actions/runs/43799716934) at `9b4ffe22` remained `in_progress` on latest check, **not yet PASS**. Earlier staging regression CI [43796217369](https://github.com/vaishnavi596/volume-king/actions/runs/43796217369) attempt 2 850/850 PASS. Keep evidence separated.
- **Next:** independently verify completed deployment-guard CI and logs; run guarded `--apply` only after it passes with current Oracle source hashes and active service. On apply, preserve original backup, evaluate restart/rollback outcome, and perform local/public health, protected Dhan status and quote smoke checks before considering APK. Production quote gate NOT YET DEPLOYED. No credential exposure/rotation or live orders.


## 2026-11-16 — BK 09:10–15:45 IST automatic-refresh window requested for installed 2.3.126

- **User mobile observation/request:** installed BOT KING v2.3.126 does refresh with a 60-second next-refresh countdown, but pre-existing time gating does not start until 09:15 IST. Requested automatic feed activation at **09:10 IST** (pre-open readiness) and stop at **15:45 IST**. This is a **new app schedule requirement**, not a claim of exchange continuous trading 09:10–15:45.
- **Root cause confirmed in GitHub:** `src/main.py` local `regular_hours()` was shared by app auto-poll gating and live signal classification; original guard `weekday()<5 and (9,15)<=clock<(15,30)`. Moving that guard globally would risk labeling pre-open/post-close quotes *LIVE*.
- **Source change:** [73e5e3bf](https://github.com/vaishnavi596/volume-king/commit/73e5e3bff519e57c58f994d39a77b2810b3a3e09) retains `regular_hours()` at 09:15–15:30 for live-eligible analysis and adds `refresh_hours()` at 09:10–15:45 (Mon–Fri), applied to selected Watchlist LTP, index quote polling, index candle polling, background/resume and visible countdown/auto-scan refresh call sites. Pre/post-exchange data remain non-live by the existing regular-hours signal guard. **No exchange holiday calendar is verified**; 60s minimum quote-request cadence and 429 cooldown stay intact.
- **Tests:** [bb62682e](https://github.com/vaishnavi596/volume-king/commit/bb62682ef1d0d468d95bc57932586b346619aa65) updates old closed-session polling assertions; [3f216c87](https://github.com/vaishnavi596/volume-king/commit/3f216c8754b40f0e140bd1bd540a4ea34fe23a3b) adds exact 09:09/09:10/09:14/09:15/15:29/15:30/15:44/15:45 IST boundaries, weekends, poll wiring and live-trading signal separation.
- **CI at initial check:** [43800396261](https://github.com/vaishnavi596/volume-king/actions/runs/43800396261) on `3f216c87` **in_progress**, no source test PASS claim yet. Earlier production-deploy *script* regression CI [43799716934](https://github.com/vaishnavi596/volume-king/actions/runs/43799716934) at `9b4ffe22` now `completed/success`. That older result is separate from this new schedule patch.
- **Deployment/version distinction:** This fixes only GitHub source; **installed 2.3.126 remains unchanged**. No Oracle production patch/restart and **no new Android APK** was built in this scheduling checkpoint. Next: resolve any new CI failures, verify end-to-end schedule with app device time/IST/time-zone tests, preserve data freshness markers, then build a versionName/versionCode-incremented signed APK after server update and regression gates.


- **Additional schedule wiring:** [e30e49f5](https://github.com/vaishnavi596/volume-king/commit/e30e49f5c3a3531f31d84a5d3a18281643a35da6) changes the two remaining autonomous chart/candle and options refresh polling guards from `regular_hours()` to `refresh_hours()`, while keeping explicit live-signal calculations on `regular_hours()`. CI not yet verified at this commit. No APK/Oracle deploy.


## 2026-11-16 — BK incremental data-only UI refresh, user report and actual source audit

- **User product request / installed 2.3.126 feedback:** Automatic market data should refresh prices, candle chart and the five filter results **without reconstructing full screen or rewriting static ticker names** (e.g. HDFCBANK name). UI should react as soon as new cached data arrives (2s/5s/10s as appropriate), but this does **not** authorize 2s Dhan API polling.
- **Verified source inspection** on branch `fix/botking-joint-audit-70-15-20261115`: `src/main.py` `watch_visible_tick()` already sleeps 2s, changes only `watch_countdown.update()` when countdown changes and compares visible `fetched_at`, `price`, and `watch_signal_cache.timestamp` signatures. However a signature change still calls `request_view_refresh(4)`, which may rebuild the Watchlist view. Thus countdown isolation is implemented, while **row-cell-level diff updates for prices and filters are NOT proven**; further targeted Flet control identity/reference audit required.
- Existing offline guards `tests/test_watch_countdown_incremental.py` and `tests/test_watchlist_refresh_regression.py` verify countdown not rebuilding 51 rows on every timer tick and changed-data-triggered rerender. `tests/test_joint_layout_refresh.py` includes a chart test proving unchanged candle payload does not dispatch repeated JavaScript updates. These tests do NOT establish every Watchlist row or every filter cell is updated in-place on installed phone.
- **Recommended next batch (not deployed):** preserve persistent row/control instances and scroll/selection, update only changed Price/Change/5-Filter cells using stable symbol-keyed controls and coalesced mounted-control updates; keep chart incremental only on changed candle; render names/static UI only on navigation/list membership changes. Separate broker snapshot acquisition (existing ~60s floor + 1.05s upstream LTP gate, cooldown) from local UI timer (~2s) and snapshot-driven updates. Do not promise fresh broker quotes every 2s, or mark exchange-live before 09:15.
- The distinct 09:10–15:45 IST read-only refresh window was just source patched; preserve 09:15–15:30 live-signal eligibility, holidays/freshness qualifiers and existing background pause. **No row-cell UI refactor, new APK, Oracle deploy, or phone verification in this observation entry.** Implement and test as its own safe batch before reporting PASS.


## 2026-11-16 — Three-mode refresh user requirement: login, changed-data UI, manual off-hours request

- **User clarification for installed v2.3.126:** remove the visible 60-second Watchlist countdown. Load market data at login, keep prices/candle/five-filter outputs refreshed without rebuilding static ticker labels or resetting the entire page, and expose a visible **Manual Refresh** button that can check even outside 09:10–15:45 IST if the user suspects stale/stuck data. Distinguish data acquisition cadence from on-screen UI cadence; retain rate-limits and cache safety.
- **Existing source confirmation:** `refresh_all_dhan_quotes()` was already present, with 30-second minimum between manual requests, guarded Dhan snapshot cooldown, `refresh_watch_batch()` and `refresh_dhan_index_quotes(force=True)`. It had **no refresh-hours condition**, so manual off-hours requests are permitted when connected and foreground. It preserves last valid quotes instead of clearing data. Previously the action was buried in the Watchlist details expansion tile. `watch_visible_tick()` rechecked changes every 2 seconds but still calls `request_view_refresh(4)` on signature changes, which may rebuild the View; cell-level incremental rendering not yet proven.
- **App source commit** [7eff6f46](https://github.com/vaishnavi596/volume-king/commit/7eff6f46f9504a15ab77784441f67425c1ddcb2e) removes the recurring visible `watch_countdown` text and `next_watch_refresh_label()` from Watchlist, promotes a single prominent `Refresh data` button beside the Watchlist title; removes duplicate details button and 'LTP every 60 sec' note. Existing poll at no more frequent than the 60-second request floor, 2-second change detection and 30-second manual floor continue; visible countdown removed, NOT the provider safety throttle. Manual refresh is a quote re-fetch, not a destructive cache reset.
- **Regression commits:** [ecf07ba9](https://github.com/vaishnavi596/volume-king/commit/ecf07ba9960fd73acdd91f3c377ba7bd9b1a11e2) changes Watchlist incremental tests; [507292fd](https://github.com/vaishnavi596/volume-king/commit/507292fda7667d44e7e6c2561e5a8dad8bd2310a) changes off-hours refresh assertions. Historical 09:10–15:45 timing CI [43800485685](https://github.com/vaishnavi596/volume-king/actions/runs/43800485685) had FAILED (7 failures/14 errors); these were caused in part by old regression fixtures still expecting `regular_hours()` in polling and isolated bootstrap expressions failing to provide `refresh_hours`. Do not call old CI PASS.
- **Additional test reconciliation:** updated `test_dhan_bootstrap_behavior.py`, `test_dhan_index_poll_rate_guard.py`, `test_login_bootstrap_127.py`, `test_mobile_regressions.py`, `test_resume_immediate_dhan_batch.py`, `test_watchlist_partial_snapshot.py` to expect separate `refresh_hours()` polling windows and manual Watchlist UI; commits `90930568f`, `b9c533932`, `90bf6d505`, `cbe05be91`, `96989db34`, `d99ad8347`. **Must verify new CI before declaring regression success.**
- **Proof boundaries:** The real device's 2.3.126 is unchanged. GitHub source and tests modified, no APK build/mobile check; Oracle staged S2D backend dry run PASS but no confirmed production deploy. User request for true per-row/per-filter mounted-control updates remains future implementation (2-second local signature currently triggers view refresh), should not label the three-mode system fully implemented. Manual off-hours may return the broker's last traded/cached data; distinguish 'checked' from 'fresh market quote'.


## 2026-11-16 — User-reported #1492–1495 failed CI, stale regression fixtures repaired (follow-up)

- Owner supplied GitHub Actions failure notifications on `fix/botking-joint-audit-70-15-20261115`: [43800352575](https://github.com/vaishnavi596/volume-king/actions/runs/43800352575) at `73e5e3b` FAILED (#1492), [43800369378](https://github.com/vaishnavi596/volume-king/actions/runs/43800369378) at `bb62682` ultimately FAILED (#1493), [43800396261](https://github.com/vaishnavi596/volume-king/actions/runs/43800396261) at `3f216c8` FAILED (#1494), [43800485685](https://github.com/vaishnavi596/volume-king/actions/runs/43800485685) at `e30e49f` FAILED (#1495). These runs test *older commit snapshots* and do not establish the current branch's result.
- Independently reviewed [43801385160](https://github.com/vaishnavi596/volume-king/actions/runs/43801385160) job logs (older intermediate commit `96989db`): **855 tests; 2 FAIL, 2 ERROR**. Failure evidence: `test_dhan_scan_progress_visibility` still expected the removed text `LTP • every 60 sec`, `test_watchlist_partial_snapshot` still expected `regular_hours()` in the equity poll. Errors: `test_market_closed_refresh_gates` and `test_refresh_window_0910_1545` tried splitting the app source using the deleted `# Compact countdown` anchor. Earlier [43800485685](https://github.com/vaishnavi596/volume-king/actions/runs/43800485685) reported **7 FAIL/14 ERROR** before the wider suite fixture updates.
- **Three GitHub test-only corrective commits:** [ce27c730](https://github.com/vaishnavi596/volume-king/commit/ce27c730d) updates refresh-boundary test anchor to existing `# The Watchlist observes`, [7543cbca](https://github.com/vaishnavi596/volume-king/commit/7543cbcab) fixes closed-market test's deleted anchor, [e49f9037](https://github.com/vaishnavi596/volume-king/commit/e49f9037a) changes `test_dhan_scan_progress_visibility` to check new non-countdown watchlist detail string. Prior six regression files were also updated to expect `refresh_hours` while keeping `regular_hours` for live signals.
- **Newest test CI** [43801833684](https://github.com/vaishnavi596/volume-king/actions/runs/43801833684) at `e49f9037a` was `in_progress` / `pending` at this query; **do not yet mark PASS**. No APK build or Android mobile verification, no Oracle production mutation, and no real Dhan order. Follow up on latest CI rather than rerunning old known-broken commit snapshots.


## 2026-11-16 — CI user reports #1492–1507; latest intermediate #1506 diagnosed and test defects fixed

- **User-supplied GitHub notification list:** runs #1492 through #1507 on branch `fix/botking-joint-audit-70-15-20261115` show several historic completed failures and some in-progress runs. These test distinct commit snapshots; do not conflate the failures with the newest source without inspecting logs.
- **Actual GitHub Actions evidence:** run [#1506](https://github.com/vaishnavi596/volume-king/actions/runs/43801830111), commit `7543cbcab`, finalized `failure`. Fetched offline-tests job `133083656692` logs: `Ran 855 tests`, `FAILED (failures=1, errors=2)`. Error 1: `test_closed_market_disables_auto_poll_but_manual_refresh_is_available` method omitted `self` (`TypeError: takes 0 positional arguments but 1 was given`). Error 2: `test_pollers_and_manual_watchlist_use_wider_window` attempted to split by deleted `def next_watch_refresh_label()` (`IndexError`). Single failed assertion still expected removed `LTP • every 60 sec` label, addressed in subsequent commit `e49f9037a` that was **not** part of #1506.
- **Applied regression-only corrections:** [4bc1ca03](https://github.com/vaishnavi596/volume-king/commit/4bc1ca03c8217d5a60aede2ccd6e3d3cbe5d8169) restores required `self` test method signature; [a1efbb3f](https://github.com/vaishnavi596/volume-king/commit/a1efbb3f137d5ce3e335a7eb31c2b4ab592e58de) replaces deleted countdown-function assertion with an assertion on current `Refresh data` Watchlist header, and confirms `watch_countdown` absent. Earlier `e49f9037a` updated obsolete LTP text expectation.
- **New run** [43802182219](https://github.com/vaishnavi596/volume-king/actions/runs/43802182219) at `a1efbb3f` `in_progress` / `not concluded` at latest check. **No clean CI PASS asserted**; re-check final logs. No server deploy, restart, APK build or mobile proof from these CI fixes. Log remains intentionally append-only.


## 2026-11-16 — Combined refresh-window/countdown/manual-refresh branch CI #1509 fully PASS

- **Independent GitHub Actions confirmation:** [BOT KING Offline Regression Tests #1509 / run 43802182219](https://github.com/vaishnavi596/volume-king/actions/runs/43802182219), commit `a1efbb3f137d5ce3e335a7eb31c2b4ab592e58de`, `completed/success`; `offline-tests` job `133084772198` `completed/success`. Retrieved complete workflow job log reports **`Ran 855 tests in 76.709s`, `OK`**, zero reported failures. Specific relevant PASS names: `test_closed_market_disables_auto_poll_but_manual_refresh_is_available`, `test_equity_and_index_poll_require_open_session`, `test_index_force_is_explicit_bypass_only`, `test_page_entry_and_resume_reuse_cached_closed_data`, `test_super_five_local_loop_reuses_candles_after_close_without_network`, `test_boundaries_and_weekend`, `test_live_signal_eligibility_still_uses_exchange_session`, `test_pollers_and_manual_watchlist_use_wider_window`.
- **Prior run statuses:** #1508 at `4bc1ca0` failed and #1507 at `e49f903` failed on intermediate snapshots before final stale-fixture corrections. #1504 at `d99ad83` was still `in_progress` in the same GitHub listing; do not incorrectly mark it completed. The passing #1509 is the **latest branch CI as queried**; it is authoritative for source at `a1efbb3` only, not evidence of Android/mobile or Oracle behavior.
- **Verified scope:** source-level read-only 09:10–15:45 IST refresh guard, separate 09:15–15:30 live signal eligibility, Watchlist visible 60-second countdown removal, prominent manual quote refresh that can run outside refresh hours subject to 30s floor and Dhan cooldown, existing two-second signature-based data-change observation. **Still pending**: actual persistent cell-level Flet controls to avoid row rebuild on changed quotes/filters; fresh signed Android APK with versionName and versionCode bump and phone test of login/close/manual flows. Oracle 1.05s staged quote gate remains undeployed to production; previous script CI and Oracle dry run passed, but server live-proof and rollback deployment validation remain pending. Do not conflate CI with mobile/server proof.


## 2026-11-16 — BK cell-level mounted Watchlist data refresh implemented, CI syntax fault corrected, enhanced regressions pending

- **Actual source change:** [889c6f95](https://github.com/vaishnavi596/volume-king/commit/889c6f9523cb8f6fb9b4298e24e0f5898841e384) modified `src/main.py`: Watchlist Row builder creates persistent mounted `price_cell`, `change_cell`, `five_cell`, `assessment_cell`, `signal_cell`, `freshness_cell` per symbol stored in `watch_row_cells`. `watch_visible_tick()` observes cached changes locally every 2s and calls mounted `.update()` for changing cells instead of invoking `request_view_refresh(4)`; `flush_view_refresh()` skips re-rendering a currently mounted Watchlist on generic quote refresh. Static ticker label, row structure, button and Android list scroll stay mounted for data refresh. Manual refresh and 09:10–15:45 refresh window remain; **no 2s API polling**.
- [ee31fd31](https://github.com/vaishnavi596/volume-king/commit/ee31fd312423a4430d877badb1cc4e6ec2153426) adds per-symbol signature check to avoid recomputing the full five-filter widgets for unchanged symbols. Filtered (Bullish/Bearish/Neutral) membership changes still call `fill_watch()` / list-only update, rather than reconstruct the full page; explicit filter selection can rebuild list as before.
- **Test updates:** [4bfbbeb4](https://github.com/vaishnavi596/volume-king/commit/4bfbbeb416de88d20644ac94cc4599ce8ff48124) and [359615e3](https://github.com/vaishnavi596/volume-king/commit/359615e36ac03838f68c48e09f4c469a87e74973) adjusted tests from whole-View update expectations to mounted cell updates.
- **CI failure caught and corrected:** run [#1512 / 43803907925](https://github.com/vaishnavi596/volume-king/actions/runs/43803907925) and [#1513 / 43803944433](https://github.com/vaishnavi596/volume-king/actions/runs/43803944433) failed due to Python `SyntaxError: unexpected character after line continuation character` in updated `tests/test_watchlist_refresh_regression.py` introduced by a literal `\\n` in an assertion edit. [267f4ae4](https://github.com/vaishnavi596/volume-king/commit/267f4ae49e9462e7538ab9309eaf82ac38789cb0) replaced those literals with actual newline characters, restoring test syntax. These failures were test source syntax and **do not prove application execution failure**. New [#1514 / 43803984473](https://github.com/vaishnavi596/volume-king/actions/runs/43803984473) was `in_progress` at latest explicit check; no PASS asserted yet.
- **Further regression:** [899ab00f](https://github.com/vaishnavi596/volume-king/commit/899ab00fb273266ac826249b1502c4543db619e6) adds tests checking stable mounted six dynamic Watchlist controls, signature skip for unchanged symbol, 2s cache UI observer, avoiding Watchlist page rerender, and existing manual refresh non-destructive quote behavior. New commit CI status not yet confirmed.
- **Remaining/limits:** Source code and tests are committed but behavior not confirmed on an installed phone. Check latest CI on `899ab00f` and inspect failures; verify new row UI at runtime and avoid refresh/selection regressions. Oracle 1.05s quote gate staged and dry-run PASS but **not deployed**. Do not claim live broker freshness, any new APK, or production rollback tested.


## 2026-11-16 — BK mounted-cell CI #1510/#1515 triage, stable index independence, offline Flet behavior test

- [#1510 / 43803865657](https://github.com/vaishnavi596/volume-king/actions/runs/43803865657) CI at `889c6f95` returned `failure`, `Ran 855 tests in 105.138s`, four failures: old `Quote check` inline-text assertion; old Watchlist index-inclusive signature assertion; old `if signature!=last_visible_signature:` assertions in two tests. New code uses persistent `watch_status_text`, only visible equity rows in Watchlist; indices remain independently rendered on Dashboard; signature checks skip identical cached snapshots. This was an intermediate old snapshot.
- [#1515 / 43804027500](https://github.com/vaishnavi596/volume-king/actions/runs/43804027500) at `899ab00f` `failure`: `Ran 857 tests`, only two old assertions remained, `test_ui_shows_actual_quote_check_even_when_closed_timer_is_paused` and `test_watchlist_change_detection_includes_indexes`. The newer code's shared UI contract requires source tests updated rather than reintroducing full-page redraw.
- **Fixed test contracts in GitHub:** [89bab604](https://github.com/vaishnavi596/volume-king/commit/89bab60492) asserts persistent `watch_status_text`; [7ddce43c](https://github.com/vaishnavi596/volume-king/commit/7ddce43c55951d7d0c3d5802aa7a9e04bc999b2c) asserts only active equity list is updated while three-index Dashboard source still owns independent NIFTY/BANKNIFTY/SENSEX refresh. Previously recorded `4bfbbeb4`/`359615e3` adjusted signature assertions and `267f4ae4` repaired test syntax.
- **New behavioral Flet regression:** [483fba46](https://github.com/vaishnavi596/volume-king/commit/483fba461db7f80c740e5e4b95e948c32727090b) adds `tests/test_watchlist_mounted_cells_behavior.py`: start real Flet controls in the existing offline `test_audit` harness; simulate changed quote, execute one 2s tick with no HTTP/broker calls, confirm updated Price/Change and identical Row/Cell object identities. [25213f1d](https://github.com/vaishnavi596/volume-king/commit/25213f1d358f57de821fb275b727fb2bf09407fc) uses an entirely fake in-memory Dhan session in the test to avoid quotes being hidden as disconnected; no live credentials. New CI [#1519 / 43804234307](https://github.com/vaishnavi596/volume-king/actions/runs/43804234307) **in_progress as last checked**, not PASS; test behavior awaits logs and may require fixture fixes.
- **Still pending:** latest clean CI, Android APK/mobile mounted-control scroll test, Oracle 1.05sec staged quote gate production apply/health/data checks. Source success is not production or mobile proof; no orders or credential exposure.


## 2026-11-16 — BK mounted Watchlist follow-up: behavioral failure cause, manual button status fix, release readiness checks

- **#1517** [43804137051](https://github.com/vaishnavi596/volume-king/actions/runs/43804137051) at `7ddce43c` CI FAILED `Ran 857 tests` with exactly one remaining stale assertion: old test searched `ft.TextOverflow.ELLIPSIS` inside `watchlist()`; quote-status is now a persistent `watch_status_text` constructed outside that page builder. [80957a6b](https://github.com/vaishnavi596/volume-king/commit/80957a6b08ee1f517047b9c42ad1b6684ca5c726) updates assertion to the actual declaration without removing ellipsis coverage.
- **#1518** [43804211674](https://github.com/vaishnavi596/volume-king/actions/runs/43804211674) at `483fba46` CI FAILED `Ran 858 tests`, two failures: same old ellipsis assertion and new `test_price_change_updates_same_mounted_row_without_page_navigation` got `'—' != '2,077.30'`. The new offline test had simulated a Dhan quote but did not mark mock in-memory session connected, so the app correctly masked disconnected quote. [25213f1d](https://github.com/vaishnavi596/volume-king/commit/25213f1d358f57de821fb275b727fb2bf09407fc) sets a fake, non-network Dhan connection in that fixture. **Outcome of #1519 after this fix was still in_progress** when observed.
- **Functional UI edge found:** Once whole-page Watchlist refresh stops, the earlier inline `Refresh data` button could remain disabled after login or busy state changes. [88987247](https://github.com/vaishnavi596/volume-king/commit/889872477ff780b5079ea8eec945efbbc3df53db) keeps the mounted button reference and updates its `.disabled` property on the 2s local tick, without rebuilding the page; initializes persistent quote status on navigation. [ab9b25dd](https://github.com/vaishnavi596/volume-king/commit/ab9b25dd5628702dff51171f4ff0e7660f841028) adds guards for the button's in-place enable/disable and quote-status initialization. No Dhan API call introduced by UI updates.
- **Release audit:** `pyproject.toml` version `2.3.126` still; `.github/workflows/build.yml` auto-triggers APK build on version file push and uses `flet build apk --build-number "$BUILD_CODE"` with `BUILD_CODE=$((10000 + GITHUB_RUN_NUMBER * 100 + GITHUB_RUN_ATTEMPT))`; permanent signing is guarded by pinned key certificate secrets. **Version must be advanced only after new offline CI passes and source is ready, not while still regressing.** No release build yet.
- **New CI** [#1522 / 43804530234](https://github.com/vaishnavi596/volume-king/actions/runs/43804530234) at `ab9b25dd` was `in_progress` on last check. Server S2D quote-gate remain staged/not deployed, Android v2.3.126 unchanged, no live orders.


## 2026-11-16 — BK local stale-age UI update without API polling; new targeted regression

- **Functional correctness audit:** The new 2s mounted-row observer previously compared only changed source quote/signals. A recent quote's on-screen freshness label could remain "LTP time unverified" beyond its 60s age threshold if no broker reply changed the quote; likewise scanner/five-engine state could age beyond its allowed window without triggering a UI cell repaint.
- [2bffd72e](https://github.com/vaishnavi596/volume-king/commit/2bffd72e3f47e61afa431b98af2e4dcbacb70ce5) adds pure local `watch_cell_age_flags(sym, now_epoch)` to watch actual quote 60s, signal timeframe freshness, five-engine evidence 300s eligibility boundaries. Both whole-visible and per-symbol signatures now include flags, triggering per-cell update on staleness threshold crossing **without any new Dhan API request**. This does not falsely mark a stale quote as live. This source patch's [#1523 / 43805009733](https://github.com/vaishnavi596/volume-king/actions/runs/43805009733) was `in_progress` at first check; no PASS claim.
- [60a2944d](https://github.com/vaishnavi596/volume-king/commit/60a2944db68bf807d7983311f8aec0b99c0477b9) adds `tests/test_watchlist_local_stale_transition.py` using the actual app function AST and entirely fake cached HDFCBANK data. Tests cover crossing 60s/300s thresholds, missing timestamps, and no broker fanout/re-render source guarantees. Its new CI run must be checked.
- **Release status:** persistent cells, manual button state and freshness aging are GitHub-only source changes. Do not declare completed until latest CI and actual phone verification. Original installed 2.3.126, no new APK or Oracle backend deployment in this entry.


## 2026-11-16 — BK CI #1520 remaining stale UI test diagnosed; running regression backlog separated

- GitHub Actions [#1520 / 43804419006](https://github.com/vaishnavi596/volume-king/actions/runs/43804419006), source `88987247`: **FAILED**, `Ran 858 tests in 111.994s` with precisely **one** failed assertion, `test_ui_shows_actual_quote_check_even_when_closed_timer_is_paused`, still expecting `ft.TextOverflow.ELLIPSIS` text inside `watchlist()` rather than the persistent `watch_status_text` declared separately. The targeted subsequent test correction is [80957a6b](https://github.com/vaishnavi596/volume-king/commit/80957a6b08ee1f517047b9c42ad1b6684ca5c726), and the newer button-regression test is [ab9b25dd](https://github.com/vaishnavi596/volume-king/commit/ab9b25dd5628702dff51171f4ff0e7660f841028).
- Active CI backlog at latest check: #1519 (`25213f1d`) `in_progress`, #1521 (`80957a6b`) `in_progress`, #1522 (`ab9b25dd`) `in_progress`, #1523 (`2bffd72e`) `in_progress`, #1524 (`60a2944d`) `in_progress`. These are **different commit snapshots** and should not be reported PASSED until completed with job-log evidence. Current code at `60a2944d` includes pure local age threshold checks; no APK build or mobile test.
- **No Oracle source mutation or service restart** during this checkpoint. Deployment script previously dry-run and CI verified but requires operator-controlled production apply, rollback/health checks; avoid claiming production quote gate deployed.


## 2026-11-16 — BK #1519 later CI proof: Flet mounted-cell test passes after fake session fix, one unrelated stale assertion remains

- Independent job-log inspection for [#1519 / 43804234307](https://github.com/vaishnavi596/volume-king/actions/runs/43804234307), head `25213f1d`, resulted `completed/failure`, `Ran 858 tests in 554.804s`, exactly **one** failing test: `test_ui_shows_actual_quote_check_even_when_closed_timer_is_paused`, which still expected old `ft.TextOverflow.ELLIPSIS` inside the Watchlist function instead of the new external persistent status Text declaration. Later commit `80957a6b` fixes this obsolete assertion. The previously failing `test_price_change_updates_same_mounted_row_without_page_navigation` is **not** in this run's failure list; this supports success of the no-network mock Flet test on the intermediate code, but full suite not yet PASS.
- #1521 at `80957a6b`, #1522 at `ab9b25dd`, #1523 at `2bffd72e`, #1524 at `60a2944d` were all `in_progress` when checked after #1519 finished. Prior success #1509 at pre-refactor `a1efbb3` (855 tests) remains valid only for its own commit. **Do not claim latest cell-level CI PASS until final complete.**
