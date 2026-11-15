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
