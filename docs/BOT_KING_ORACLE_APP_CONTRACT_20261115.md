# BOT KING — Oracle ⇄ Android verified contract (15 Nov 2026)

Status and scope: audit evidence through Oracle S18-B; GitHub branch
`fix/botking-joint-audit-70-15-20261115`. This is a **handoff contract**, not
proof of live exchange timestamps, live trading, an installed APK, or successful
deployment of new source to Oracle. Confirm HEAD before release.

## Cross-chat continuity / do not redo verified work
- Repo: `vaishnavi596/volume-king`. Production runtime:
  `/opt/bot-king-server/server.py`; service `bot-king.service`; Nginx.
  GitHub `backend/server.py` and deployed Oracle `server.py` have **different
  contents**; never overwrite Oracle wholesale from the GitHub tree.
- Prior builds reached BOT KING 2.3.123 with unified Trading Center /
  Paper Bot profiles, but this branch's completed offline CI is **not** a new
  Android APK, successful mobile test, or new live-trading authorization.
  The `main` branch may have an older version than the feature branch.
- Preserve signing/package/Android user data; a new release must advance
  both versionName (also visible in UI) and versionCode. Verify the exact
  built APK, artifact, and install/upgrade test. Do not delete legacy
  functionality unless an independent migration has been proven.
- Market data provider for the selected new product is Dhan only. Do not
  silently fall back to Yahoo or Angel for Dhan quotes/signals.
- No live order or purchase execution; `live_orders_enabled=false`.
  Paper Bot remains local/simulated until independently verified.
- Preserve functioning Dhan token renewal; never rotate credentials or
  edit renewal service for unrelated data issues.

## Oracle audit evidence (S09–S18)
- S09 static safety 27/27; S12 18 changed Python modules, 99 recent backup
  files, 2,785 NSE equity registry records with declared/actual counts matching.
  Registry file is `/opt/bot-king-backups/registry-audit/dhan_equity_registry.json`.
- S12 main service and Nginx active, health HTTP 200, live orders disabled.
  Some token-maintenance files were unreadable (PermissionError), not proven
  syntax errors. S12 journal sample 270 lines had no matched errors.
- S13: index LTP, legacy batch, snapshot, option-chain/expiry present.
  Global watchlist limit and index-only equity option guards differed from app.
- S14: **actual** `/v2/instruments/search` already registered in
  `watchlist_api.py`; its reply contains `source=dhan_registry` and
  `symbols` but does not require `live_orders_enabled` metadata.
  Do not add a duplicate path to `server.py`.
- S15: staged Oracle server patch applied successfully; source hashes were
  checked, server restarted and health passed; no rollback. The patch added
  `/dhan/selected-ltp-batch` and two dynamic equity option guards.
- S16 source syntax PASS, selected route count 1, dynamic option lookup count 2.
- S17 **unauthenticated** 13/13 security/health checks PASS, all protected
  routes returned HTTP 403; no broker price, validity, 70-symbol payload,
  expiry listing, candle freshness or real P&L was confirmed.
- S18-B Oracle WatchlistStore `count=5, limit=70` **per list**; `validate`
  rejects duplicates inside one list, but does not prohibit adding a symbol
  to another list; `replace` writes a staged in-memory value, saves
  atomically, and rolls back on failure. Cross-list uniqueness and global
  70 limit are **not deployed** yet.

## Definitive watchlist rule from user
Across five separately saved watchlists: **maximum 70 stocks in total**,
with **one symbol permitted in exactly one list**. If RELIANCE/TATA
belongs to List 1, List 2–5 cannot contain it. To move it, remove it
from its current list first. Reject both duplicate and 71st selections
before persistence; keep the existing lists; never auto-delete or
overwrite historical saved JSON merely to fix a conflict. Old data
must be reviewable; corrections may be deliberate. Android and Oracle
must enforce the identical rule, including add and replace/update.

## Source + runtime guards
- Registry verifies identity, not Dhan entitlement or a valid quote.
  Dynamic search must be authenticated and exact-symbol checked; do
  not auto-request quotes for all 2,785 equities.
- Selected equity LTP requests: 1–70 unique validated NSE equity symbols
  per request, one bounded Dhan batch, safe partial/429 response, no order
  calls, no fabricated timestamps or fallback.
- Original Oracle 51-equity snapshot remains cache-driven and read-only.
  Cached last-valid prices may be displayed as old/unverified, never live.
- NIFTY/BANKNIFTY/SENSEX index batch independent of watchlist scan.
  Preserve timeouts, pacing, 30-sec cooldown and resume logic.
- Equity option expiry + chain uses broker-listed expiry, F&O entitlement
  and mapping verification; never assume every NSE equity is optionable.
  Preserve the Oracle cached-expiry/409 guard, OI, Assessment snapshot,
  429 cooling and fail-closed signal eligibility.
- News/Futures/Options/Candle scores remain **unverified** until genuine
  independent providers and freshness verification exist. Do not
  invent directional percentages. Five engines require independent evidence;
  use WAIT when insufficient.

## Pending gates before new APK
1. Stage and check S18-B global watchlist server patch; back up existing
   `watchlist_store.py` and saved watchlist JSON; run isolated
   duplicate/70-limit/persistence tests; deploy with health+rollback.
2. Check S15 selected Dhan route, Oracle search and equity-option
   mapping using **scoped, safe, authorized** probes. Never print pairing
   key or OAuth token. Do not call market data simply to run an auth audit.
3. Confirm actual installed server routes, token and persistent snapshots
   without changing the renewing credentials.
4. Audit branch-vs-release file/commit versions and existing Paper Bot
   UI/functionality; run full offline CI, signed APK build, versionCode,
   package and upgrade compatibility, then on-phone testing.
5. Report distinct states: source committed, offline CI passed, Oracle
   deployed, broker live validated, built APK, installed APK, mobile tested.

Last checked GitHub source on this contract branch: `pyproject.toml`
version `2.3.123`; `main` displayed `2.3.95`. Do not infer that
a new artifact was built from this branch.
