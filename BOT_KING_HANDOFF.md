# BOT KING — START HERE IN EVERY NEW CHAT

**Project:** BOT KING (Dhan-only Android scanner and simulated Paper Bot)
**GitHub:** `vaishnavi596/volume-king`
**Current integration branch:** `fix/botking-joint-audit-70-15-20261115`
**Latest verified release APK:** `2.3.126` (GitHub Build #641 PASS); **installed phone:** `2.3.125` with reported first-login refresh/Super Five issues. No 2.3.126 mobile PASS. Confirm newest HEAD/build before making subsequent changes.
**Latest verified APK build run:** https://github.com/vaishnavi596/volume-king/actions/runs/43753960172 (2.3.126, `versionCode=74101`, signed, artifact ID `14177263980`). Previous 2.3.125 run: 43751755544.
**Latest verified 2.3.125 build:** SUCCESS, 804 tests PASS, versionName=2.3.125, versionCode=74001, pinned signing verification PASS; GitHub artifact `volume-king-apk` ID `14175849838` uploaded. **Device test still pending.**
**Canonical master improvement checklist — READ NEXT:** `docs/BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md` (12 work groups, source/CI/Oracle/device evidence and journal corrections).
**Historical 14–15 Nov step-by-step audit:** `docs/BOT_KING_PREVIOUS_TWO_CHATS_STEP_BY_STEP_20261114_15.md` (51 numbered checks with provenance and limitations).
**Prior verified full offline suite:** 804/804 PASS at commit `ee1d75a4137a172d776d0e6d607986fe4659605a` (run 43751577312).

> **Required new-chat procedure:** Fetch this file and
> `docs/BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md`, `docs/BOT_KING_WORK_LOG.md`, and
> `docs/BOT_KING_ORACLE_APP_CONTRACT_20261115.md` at the **latest branch HEAD**;
> inspect newest GitHub Actions result and actual `pyproject.toml` version BEFORE
> editing or claiming any APK is final. Do NOT assume this document is
> automatically loaded into a new chat: give the new chat the repository URL or
> this document link. Never report a stage PASS from a historical run.

## 1. Confirmed system facts (Oracle and user terminal output)

- Oracle host `bot-king-vnic`, service `bot-king.service`, directory
  `/opt/bot-king-server`; Nginx public HTTPS. Production Oracle
  `server.py` contains assessment and expiry-cache features not present in
  the GitHub `backend/server.py`. **NEVER replace wholesale.**
- Health HTTP 200 and service active. Oracle health intentionally reports
  `broker_connected=false`, `live_orders_enabled=false` (not a failure).
- S17 13/13 unauthenticated route security checks PASS.
- Authenticated Oracle `GET /dhan/status`: HTTP 200,
  authenticated=true, market_data_configured=true, token_source=oauth_consent,
  token_validity=expiry_checked, reauthentication_required=false.
- Authenticated Oracle `GET /v2/snapshot`: HTTP 200, source=dhan,
  51 equity quotes; snapshot age at probe 79.1 seconds,
  freshness=unverified, error=null.
- S19 authenticated `POST /dhan/index-ltp-batch`: HTTP 200 with
  NIFTY 25144.3, BANKNIFTY 61034.1, SENSEX 81592.45; unavailable=[],
  freshness=unverified. This validates response at test time,
  **not current market prices**. Do not claim these are exchange-live.
- Oracle S15 server route patch deployed and health passed.
  S18 **WatchlistStore** global-70 / cross-list-duplicate patch remains
  **staged in GitHub only**. Do not claim Oracle production is updated.
- Do not modify Dhan OAuth, credentials, token renewal or enable orders while
  fixing quote display; never print keys in reports.

## 2. User-approved behavior

- On every successful login, whether market is open or closed, **load the last
  available verified-origin equity quotes, three indexes and available cached
  candles** to Dashboard/Watchlist/Super Five. Label timestamps/freshness
  honestly: last-known/unverified, not exchange-live.
- While market is CLOSED: pause repeated market-data auto polling after initial
  load; allow bounded first-load recovery of missing quote data, not a
  never-ending API loop. The full 51-historical scan after login is distinct.
- When open (~09:15 IST, follow existing session-calendar guards): regular
  independently throttled quote pipelines should run again.
- Index batch is independently scheduled, not blocked by the Watchlist
  scanner. Super Five and scanner reuse available cached data; Dhan calls
  serialized and 429 cooldown respected. Avoid repeated 51-candle fanout.
- Five saved watchlists, **maximum 70 equities TOTAL across all five**.
  Each symbol may be in **ONE LIST ONLY**. To move it, remove from old
  list first. Never delete user's saved watchlists.
- Separate prices from signals. Missing/untimestamped News/Futures/Options
  evidence must remain WAIT rather than inventing BULLISH/BEARISH.
- Paper Bot is simulation, must not submit real orders.
- User prefers GitHub+Oracle work in 2–4 coherent edits/tests per batch,
  minimal repeated questions, no generated screenshots unless requested.

## 3. Confirmed GitHub work (not automatically deployed to device)

- 2.3.124 signed APK workflow PASS (run
  https://github.com/vaishnavi596/volume-king/actions/runs/43746262145),
  but that build predates latest first-login recovery.
- New branch 2.3.125:
  - `4e50d226`: Login fallback from failing individual NIFTY LTP
    (unless 429) to authenticated three-index batch, with strict
    source/safety checks and price retention after provider reset.
  - `6bf04e96` and `ea22fb2e`: earlier intermediate closed-market
    bootstrap attempts FAILED older regression tests. **Not release heads.**
  - `ee1d75a4`: restored old market-open polling code patterns and
    added bounded closed-market first-load bootstrap. Verified 804/804 PASS.
  - `e587485b`: version bump to 2.3.125 and signed APK build trigger.
  - Report only the ACTUAL current Actions result at the time you check.

## 4. Critical open issues

1. Device report: Watchlist, all three index prices, Super Five prices and
   automatic scanning appeared blank/stuck on the installed app. The installed
   app's version was **not confirmed**; do not equate current GitHub source
   with the installed APK. Oracle authenticated data checks passed.
2. Need finish/check 2.3.125 signed APK build, versionName/versionCode,
   package/signing identity, artifact before recommending installation.
   An APK build PASS != on-device PASS.
3. Need test first closed-market login, missing-data recovery and market-open
   refresh on Android; check Error Doctor and reconnect status. Normal
   market-hours refresh should not restart indefinitely.
4. S18 Oracle WatchlistStore global-70 uniqueness enforcement needs backup,
   staged patch review, server tests, guarded deployment and rollback. Existing
   watchlist data must be preserved.
5. Selected batch stock quotes and multi-symbol options remain to be
   tested end-to-end against Oracle with authenticated bounded calls.
6. Independent Super Five, scanner and candle cache parity / stale-history
   labels need actual device verification.

## 5. What to record after *every* substantial work batch

Before leaving a chat, commit a dated update to THIS file or
`docs/BOT_KING_WORK_LOG.md` containing:
- **Baseline**: exact branch, HEAD SHA and installed APK version (if known).
- **Change**: files modified, functionality and reasons; link commit(s).
- **Test**: CI run and actual PASS/FAIL with test count; Oracle results
  separate from device/user tests.
- **Production status**: staged / deployed / restarted / rolled back;
  backups and which credentials untouched.
- **Known issues / next three actions**: never hide unfinished work.
- **Safety**: read-only market-data vs paper mode vs live orders disabled.
If an item has no proof, write **UNVERIFIED**, not PASS. Do not upload
private keys, Dhan credentials, logs with tokens or user account details.

The historical authoritative contract is:
`docs/BOT_KING_ORACLE_APP_CONTRACT_20261115.md`.
The append-only batch journal is:
`docs/BOT_KING_WORK_LOG.md`.

## 2026-11-16 urgent phone feedback

- **Installed v2.3.125**: old saved quote values visible (RELIANCE ₹1339.70), but login Watchlist refresh not confirmed.
- Code defects patched `5da68b3a`, `9d94169a`, `bd5c2212`: stale saved quote prevented closed-market retry; Login outcome did not synchronize Watchlist status. New dedicated behavior tests PASS 809/809 on run 43753705425.
- Release candidate 2.3.126 is to be built and **independently signed/installed/tested**; don't call the phone fixed from offline tests.
- Market-open 09:15–15:30 IST polling and 60-second equity/index timers were preserved. The price may be numerically unchanged when the exchange is closed; inspect the displayed 'Login snapshot' status and snapshot collection age instead of demanding an impossible live tick.
- No Oracle restart or token reset was performed for this fix.

## 2026-11-16 master checklist and correction checkpoint

- The **authoritative current improvement inventory** is `docs/BOT_KING_MASTER_IMPROVEMENT_CHECKLIST_20261116.md`; start new chats there before implementing further batches. It separates original requests from actual Source/CI/Oracle/API/Device proof and reconciles older conflicting journals without deleting history.
- Current Android code uses **15 movable filter slots (10 defaults + 5 extra)**; the previous 10-slot-only status was an intermediate branch, not the latest integrated source. Original historical audits still use 10 default calculation filters.
- **2.3.126 Build #641 SUCCESS** with versionName `2.3.126`, versionCode `74101`, signing and artifact. **Phone 2.3.125 remains failing/unverified for first-login refresh, data and Super Five B/S**; newer APK is not automatically a device fix.
- Futures real acquisition, authentic News and verified independent Options directional scoring remain **PENDING**; Oracle S18 total-70 unique-watchlist server patch is **NOT DEPLOYED** as far as existing evidence shows. No real orders enabled.
- Older “need to finish 2.3.125 build” and “2.3.126 to be built” paragraphs above are **historical**; this checkpoint supersedes them. Do not silently edit/delete those historical records.


## 2026-11-16 — NEWER DEVICE FAILURE AND 2.3.127 REPAIR TRACK

- **Most recent user device report supersedes earlier installed-version notes:** v**2.3.126** was installed; **automatic refresh after login still fails/not observed** and Super Five B/S filters/data remain incomplete. Option Chain for HDFCBANK and other supported underlyings needs end-to-end verification. **MOBILE FAIL overrides any older "device untested" label for the reported behavior, but does not prove all screens failed.**
- **Do NOT call 2.3.126 fixed merely because Build #641 and 809 offline tests passed.**
- **Approved next repair programme:** `docs/BOT_KING_2_3_127_JOINT_REPAIR_PROGRAMME_20261116.md`. Read it before touching app: batches 127-A through 127-E (login bootstrap; independent equity/index; Super Five historical B/S; Options/HDFCBANK; regression/build). Version 2.3.127 is a **planned candidate, not yet built**.
- App source audit found per-login session bootstrap is not guaranteed on app-open; connected-only poll guards and closed-hours option loop are potential blockers. Actual mobile and server correlation remains unverified.
- Oracle production and Dhan OAuth unchanged; live orders OFF. Preserve old app data, 15 filters, five watchlists/global 70, historical 51+3 and signed package/versionCode policy.


## 2026-11-16 — New handoff checkpoint after 127 source joint work

- **Integration branch:** `fix/botking-joint-audit-70-15-20261115`; latest source full-regression verified commit `6fb58023a61c0ca55548fa48eb18860dcbadc933` [run 43759426158](https://github.com/vaishnavi596/volume-king/actions/runs/43759426158) **825 tests PASS**. Documentation commits after that do not change the tested app code.
- **Batch 127-A:** session-scoped login bootstrap, equity/index statuses, no second provider generation reset; offline CI PASS. Existing phone 2.3.126 Login Auto-Refresh **MOBILE FAIL**, v2.3.127 device test NOT DONE; secure auto-login on app restart still requires enrollment/reconnect design.
- **Joint 127-C/D source:** closed-hours local Super Five historical votes and saved rankings/technical B/S, bounded five-symbol headline context (not voting News score), selected Dhan broker-listed expiry/Option Chain first-login request, session-isolated RELIANCE/HDFCBANK/index option contexts and CE/PE OI/ΔOI/Volume preview, Error Doctor Paper Bot status, and trusted broker SessionExpired 401 handling. These are GitHub source/CI evidence only.
- **Read-only Oracle audit pending:** `scripts/check_127_oracle_readonly.py` is ready for authorized operator execution (requires preexisting env-supplied `BOTKING_URL` and `BOTKING_PAIRING_KEY`; never log/persist secrets). It summarizes 51 snapshot, 3 indexes, optional <=70 selected NSE equities, RELIANCE and HDFCBANK listed expiry/chain, 429/422 results. **It has not run on Oracle.** Never overwrite Oracle-custom `server.py` with repository backend.
- **Paper Bot:** already five manual simulated profiles, Start/Pause/Stop and paper ledger; source shows state in Error Doctor. Not an unattended Dhan-tick autobot; actual Android behavior UNVERIFIED. Live orders remain OFF.
- **Unfinished release gates:** independently verified News/Futures directional engines are WAIT; authenticated 51+3 refresh and listed stock CE/PE/provider entitlement checks on current Oracle are PENDING; Android tests for open/closed login, historical Top Five, option selection and Paper Bot are PENDING. **No new APK or version bump.** Current installed user version is still 2.3.126. Do not trigger final 127-E signed APK before the required functional gates; CI success is not device success.
- **Journal detail:** See latest append-only `docs/BOT_KING_WORK_LOG.md` entries for each patch, failed intermediate CI, successful run, production nonchanges and next tests. Treat this checkpoint as superseding older “127 audit only” status, without removing history.


## 2026-11-16 — Current status: 831-test index Login Recovery PASS

- Batch 127-B source fixes are now at tested SHA `7caac968c18437229a2d6384e99b1d9708fce6dc` ([Offline Regression CI 43786961360](https://github.com/vaishnavi596/volume-king/actions/runs/43786961360), **831 tests PASS**, verified log).
- Closed-market index recovery no longer treats saved historical NIFTY/BANKNIFTY/SENSEX prices as proof of a new login's complete 3/3. A single bounded retry is allowed only after current-generation PARTIAL/FAILED/COOLDOWN, never concurrently with LOADING or after 3/3 LOADED. All index/equity Dhan quotes remain exchange-time unverified.
- The durable full audit history—including intermediate failures and fixed tests—remains append-only at `docs/BOT_KING_WORK_LOG.md`; do not revert the newer index gate to a cached-price condition.
- **Required live acceptance:** run the committed, credential-safe `scripts/check_127_oracle_readonly.py` from an authorized operator environment, then inspect actual Oracle 51/3 + selected extra quotes and RELIANCE/HDFCBANK option listed expiry/chain. Current chat has no Oracle shell, so this has **not been done**. No build v2.3.127, signed APK, device acceptance or Oracle production modification; source CI PASS is not a mobile/market-data PASS.


## 2026-11-16 — 127-B persistent Watchlist snapshot recovery: 836-test PASS

- Root cause candidate identified from source: Oracle's `BOTKING_226_INGEST_ENABLED` defaults to off, while the app previously read only `/v2/snapshot`; without active cache collection the saved watchlist quotes would not advance even though the UI timer kept polling.
- Implemented a **read-only, fixed 51-equity Dhan direct batch fallback**, only after missing/stale cached Oracle snapshot, using preexisting `/dhan/ltp-batch` and at most one direct attempt per 180s per authenticated app session. Strict full-universe quote/unavailable contract; last-valid quotes are retained; no exchange-live claims, no per-symbol fanout, no live orders. Applied to Login and scheduled/Watchlist refresh.
- Source/test commits: `d38599f8`, `6c4625f5`, `f45d0f92`, source-string test updates `21ecf5e9`, `6b3af492`. Latest [offline GitHub CI run 43789687353](https://github.com/vaishnavi596/volume-king/actions/runs/43789687353): **836/836 PASS**, actual job log checked at SHA `6b3af492`.
- **Not production-proven:** Oracle runtime ingest flag and authenticated `/dhan/ltp-batch` entitlement were not checked. No production server change, Oracle read-only probe run, app versionCode/versionName bump, signed APK or mobile acceptance. Continue authorized production metadata smoke, then release version 2.3.127 test APK and explicitly confirm fresh login prices, 180s refresh, 3 indices, selected equities, stock option chains and Super Five without fabricated 5/5 signals.


## 2026-11-16 — S2D Server ↔ Dhan port/key/rate-limit repair checkpoint

- User requested first a full Server-to-Dhan rule reconciliation rather than another premature APK. The existing Android 127-B equity direct fallback/option work remains in branch; **do not replace or deploy** the customized Oracle server without timestamped backup and runtime comparison.
- Official Dhan v2 docs: `api.dhan.co/v2/marketfeed/ltp` uses `access-token` plus `client-id`, up to 1000 instruments per request, 1 quote request/sec; 24h access tokens, separate paid Data API entitlement, 3s option pacing. Distinct `X-BotKing-Key` is only BOT KING server pairing. Nginx external HTTPS443 ↔ Uvicorn loopback `127.0.0.1:8000` one worker; Oracle outbound Dhan data and OAuth both HTTPS443.
- Source fixes: `backend/dhan_feed.py` shared cross-instance 1.05s quote lock (commit `772c38ef`), no redirects/proxy forwarding for market-data headers (`e79f2669`), OAuth consent/key headers never follow redirects (`c61ab240`), corrected source-only operator script recognizing protected OAuth session or legacy token (`25cab964`, `16c88a58`), port 8000 loopback and no-key outbound Dhan data `api.dhan.co`/OAuth `auth.dhan.co` TLS443 checks (`6553ca83`, `cbca474e`), and guarded source regressions including one-worker requirement (`be10b4da`, `527ab932`).
- Latest proven CI source checkpoint `5a4f73b5`: [run 43792643011](https://github.com/vaishnavi596/volume-king/actions/runs/43792643011) **846 tests PASS**; full final `527ab932` run [43792941657](https://github.com/vaishnavi596/volume-king/actions/runs/43792941657) initially pending. Follow `docs/BOT_KING_WORK_LOG.md` for individual evidence/failed runs.
- **Cannot assert actual deployed connection rules are all enabled.** Production's real systemd User/EnvFile, token file vs OAuth session path and permissions, inbound public 443/firewall/TLS, outbound HTTPS, Dhan `/v2/profile` Data API subscription and 24h token validity, 51 stock+three indices+option chain live responses remain untested because there is no authorized Oracle SSH/credential access. A public host check from this environment could not resolve the DuckDNS host, which is **not proof the owner's Oracle is down**. No production edits, restart, Dhan OAuth rotation, order enablement, APK/version bump. Live orders OFF.


## 2026-11-16 — LATEST journal reconciliation and four-pipeline refresh design (SOURCE/PLAN, not deployed)

- **READ FIRST:** `docs/BOT_KING_EVIDENCE_AND_COMMAND_RUNBOOK_20261116.md` (new minimal-command evidence ledger; GitHub source commit `91eb6536`) alongside `docs/BOT_KING_WORK_LOG.md`, then `docs/BOT_KING_REFRESH_DEMAND_INVENTORY_20261116.md` (20 refresh consumers; source `af25d0c2`). Older handoff entries above are historical snapshots, **not the latest APK or production status**. Do NOT rerun proven nginx/listener/TLS/staged fake-quote tests just for new-chat orientation.
- **LATEST VERSION STATUS:** `pyproject.toml` source release version `2.3.128` from commit `48182f1b`; user reports the v2.3.128 GitHub Build **FAILED**, exact Actions run/job/step not yet inspected. No signed 2.3.128 APK, no device PASS. Last independently logged signed Build PASS is v2.3.127 #642 / run `43805532600` / 862 tests; v2.3.127 real user mobile screenshots FAIL (stale Oracle snapshot, seven issues, missing candles/filter votes). `src/main.py` 2.3.128 patch `70defe99` preserves shared 5m history and Super Five HIST; test source `2bb5fb2c`, no newly confirmed offline PASS.
- **FOUR LOGICAL PIPELINES user-approved for coordination (NOT IMPLEMENTED):** (1) equity+index quote snapshot; (2) 54 completed candles / Scanner / Super Five; (3) options CE/PE/OI/PCR/max pain + future independently verified derivatives; (4) News RSS + cached assessment/health. One Oracle-owned coordinator, global budget/cooldown, per-source revision, one shared cache, no extra request fanout. Four channels do NOT imply every channel firing concurrently, nor four direct Dhan requests. Dhan-only read-only orders OFF.
- **CURRENT vs TARGET:** App still: stock/index/option min 60s, Oracle assessment 180s, index candles 180s, 54-candle sequential scan then 180s rest, Super Five local 10s, Scanner local 2s, Watchlist mounted cells local 2s, News TTL 600s. Conditional tested targets: Oracle index 10–15s, equity quote 15–30s, selected option chain 30s, derived 2–5s local, completed 5m bars at candle close. Faster intervals **NOT DEPLOYED**; require Oracle production 429/latency/freshness verification. Market weekday 09:10–15:45 auto, 09:15–15:30 exchange-live eligibility; global outside-hours manual button requested but not implemented.
- **Oracle 1.05s quote gate:** staged module original SHA256 `7a8db92e...beb75` and proposed `beccda30...c33c` full in runbook; owner fake-quote test 1.051s, 429 cooldown, 0 network requests, dry-run PASS and production UNCHANGED. Quote-gate actual Oracle production deployment NOT PROVEN; do not assume applied or replace customized server files. Earlier Oracle 443/Nginx/8000/TLS health validated; see exact one-time command outputs in runbook.
- **NEXT MINIMUM ACTION:** First retrieve failed v2.3.128 Build job log, narrow fix and CI, then read-only verify stale snapshot collector and index HTTP stage (with no keys in output). Implement four-channel coordinator in bounded tested batches; advance signed versionCode/versionName only after tests; device acceptance separate. After every discussion/patch/command/test/deploy append dated evidence-backed journal entry, report PASS/FAIL/PENDING distinctly. Update root handoff after substantial status changes, never silently rewrite old history.


## 2026-11-16 — MANDATORY 7–8 latest GitHub Actions error-audit preflight

- **Owner's permanent workflow rule:** BEFORE each new batch/source patch/APK release read the **latest 7–8 Actions runs** on the same working branch, including Offline Regression and Build APK; inspect each failed step and actual job log, group repeating assertions into root causes, correct previous red tests/code before proceeding. Persist the run/job IDs, tested count, fail count, exact issue, repair commit, and PASS/FAIL/PENDING state in `docs/BOT_KING_WORK_LOG.md`. Group safe Oracle commands 2–4 together, track actual outputs, and never repeat already-proven server commands without reason.
- **FIRST reference:** `docs/BOT_KING_CI_EIGHT_RUN_PREFLIGHT_20261116.md` (commit `15006de5`, later expanded `69310d5a`), contains run/job failures #1536–#1541, build #643, exact assertion names, source/test patches and current status #1542–#1545. Old tests expected `dhan_feed.connected`, direct `quotes.get` and hardcoded local 10s; corrected HIST shared-cache/2s behavior remains offline-only and needs latest full CI.
- **Current source test-repair sequence:** `51321c92` joint bootstrap, `c08b7791` mobile regressions, `5ca1e8f0` watch incremental. GitHub #1541 failed with four old assertions; #1542–#1545 in progress on first check. **NO PASS** or signed APK inferred. No Oracle change, credentials or order operations. Don't bump version until current post-repair full CI PASS.


## 2026-11-16 — Latest CI/release and Oracle parity checkpoint

- **CI green:** Offline #1549 [43815714273](https://github.com/vaishnavi596/volume-king/actions/runs/43815714273), job `133127168728`, commit `0ab3e3f4`: **893/893 PASS** (543.626s). #1546–#1548 failed the same single obsolete test literal; fixed in `0ab3e3f4`. Use last-eight CI rule before next patch. Detailed result in `docs/BOT_KING_WORK_LOG.md` entry `APP↔ORACLE-03`.
- **Build green on OLDER head:** APK Build #644 [43814744656](https://github.com/vaishnavi596/volume-king/actions/runs/43814744656), head `52acae7b`: signed APK `com.botking.bot_king`, `2.3.129` versionCode `74401`, artifact `14202710472`. This APK **does NOT include later Oracle readiness/server contract patches** and has NO mobile PASS. No 2.3.130 release initiated.
- **Backend APP↔Oracle source:** seven core route pairs checked; new protected `/v2/server-readiness` source `f3163d4c`, regression `b4e3f9bc`, test correction `0ab3e3f4` CI PASS. App also calls `/v2/assessment/{symbol}` not present in repository `backend/server.py` source. Actual customized production server may differ. Snapshot ingester opt-in default disabled and 60s minimum in source; actual Oracle deployment/env/token status **NOT inspected**. Do NOT infer live app-server parity from CI; require sanitized collector enabled/age/count, protected route & index smokes, backup and staged comparison before server restart. Four-lane source policy is NOT Oracle deployed. Broker orders OFF.


## 2026-11-16 — APP↔ORACLE-06 grouped live readiness probe handoff
- **Source CI:** #1552 [43818041629](https://github.com/vaishnavi596/volume-king/actions/runs/43818041629) at `7a8db8ac`, exact job `133134482033`, **898/898 PASS**. Earlier #1551 **894/894 PASS**, #1549 **893/893 PASS**.
- **New grouped Oracle read-only probes:** GitHub scripts `scripts/audit_oracle_app_routes_readonly.py` (syntax/9 protected route decorators + SHA256; source only) and `scripts/audit_oracle_collector_runtime_readonly.py` (3 localhost GET-only checks: /health, authenticated /v2/server-readiness and /v2/snapshot, aggregate collector enabled/status/interval/age/quote count; no Dhan requests). Operator must securely provide `BOTKING_AUDIT_PAIRING_KEY` on Oracle host, never paste secret into chat/GitHub. Run both scripts after provisioning their code, then append actual sanitized outputs; **NONE run on Oracle yet**.
- **New tests:** `tests/test_oracle_collector_runtime_readonly.py` commit `573b04af`, #1553 [43819619493](https://github.com/vaishnavi596/volume-king/actions/runs/43819619493) was in_progress when last checked. SOURCE ONLY, no Oracle stage or deploy.
- **Why this gate:** Current GitHub backend source collector defaults OFF and min60s, while App expects a recent /v2/snapshot. Actual production flag/version and real 9-route parity are unverified. Do not increase quote rate, enable collector, replace customized Oracle server.py, or sign a 'fully fixed' APK on guesswork. Historical v2.3.129 signed #644 is still a pre-server-patch candidate, not mobile acceptance. Read-only, no real orders. Full details and exact result journal in `docs/BOT_KING_WORK_LOG.md`.


## 2026-11-16 — REFRESH-4P-03 handoff: first single-flight module, source-only
- Latest completed baseline #1553 [43819619493](https://github.com/vaishnavi596/volume-king/actions/runs/43819619493) at `573b04af`: **902/902 PASS**. The last-eight rule continues to apply.
- New `src/refresh_coordinator.py` commit `916835a4`: four logical read-only lanes, same-key single-flight, bounded TTL/cache, failure-not-cached. New `tests/test_shared_lane_refresh_coordinator.py` commit `d5062e7a` adds fake-provider concurrency/cooldown/cache tests; #1554/#1555 **in_progress** when read. Do not assert latest CI PASS until current-HEAD #1555 exact result.
- Crucial: this is a **standalone prototype**, NOT integrated into `src/main.py`, `src/server_feed.py` or deployed Oracle. App network refresh intervals and Oracle Dhan request volume are NOT yet reduced. No release or mobile success inferred.
- Keep next batch focused: finish red CI backlog, then integrate only one proven cache consumer, audit actual Oracle deployed collector/routes/age with the two read-only scripts and safe pairing key, only then optimize rate. Production backup before any server edit; live orders OFF. Canonical exact entry in `docs/BOT_KING_WORK_LOG.md`.


## 2026-11-16 — REFRESH-4P-04: first real bounded client coordination, awaiting full CI
- Latest prior-green #1554 [43820879016](https://github.com/vaishnavi596/volume-king/actions/runs/43820879016) = 902/902 PASS; #1555 [43820945746](https://github.com/vaishnavi596/volume-king/actions/runs/43820945746) = 907/907 PASS. Last-eight Actions audit performed before edits.
- App source [a0adc6e2](https://github.com/vaishnavi596/volume-king/commit/a0adc6e295a2abe06a0c250548ca0faeb71a1405) integrates `LaneCoordinator` **only** into Dhan client `server_readiness()`, validated 10s read-only cache, no unsafe payload caching, reset on disconnect. Offline integration tests [1e403599](https://github.com/vaishnavi596/volume-king/commit/1e403599b9a573e43ba81bbda5c024fdf3234102). CI #1556 [43822238523](https://github.com/vaishnavi596/volume-king/actions/runs/43822238523) and #1557 [43822272318](https://github.com/vaishnavi596/volume-king/actions/runs/43822272318) **in_progress at initial check**; no green claim yet for newest HEAD.
- **No additional market data acceleration:** Oracle app/source Quote 60s, Options 60s, server Collector default disabled/min60s remain unchanged. New readiness cache is a limited real application of single-flight, not 4 complete lanes or production deployment.
- **Next:** current-HEAD CI logs, then Oracle only read-only 2-script grouped route+collector operator audit; compare customized deployed server.py and safe env/age/count, do not repeat previous nginx/TLS checks; stage backup/rollback before any Server refresh change. v2.3.129 Build #644 signed older code only, not installed proof. Production not modified, orders OFF. Full entry in Work Log.
