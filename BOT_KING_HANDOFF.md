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
