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
