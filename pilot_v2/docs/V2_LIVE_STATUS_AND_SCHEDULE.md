# BOT KING V2 — CURRENT STATUS, CATEGORY-WISE JOURNAL & NEXT CHAT SCHEDULE

> **OWNER LATEST (same Flet V2 branch, finish existing batch):** Current S1 synthetic CI #25 44304920157 PASS at 86b39da; no new branch or ad-hoc feature. App-first Flet V2 → joint CI → signed candidate APK → Oracle gateway; 4-device target deferred to combined existing multi-device batch (current code limits 3). See V2-OWNER-SAME-FLET-BRANCH-FINISH-ACTIVE-BATCH-20261118.

Updated 2026-11-18. **This is the canonical start page for the next chat.** Use latest GitHub evidence if newer than this snapshot.

## Verified baseline
| Item | Verified status |
|---|---|
| Repo and branch | `vaishnavi596/volume-king` / `pilot/botking-v2-smart-gateway-20261118` |
| Last V2 source commit | `d8fe238d95d9f9fbf51453005f7a82589d0c98ec` |
| Exact latest source CI | #23 run `44302676179` **SUCCESS**, same SHA |
| Working V2 | Isolated offline source and synthetic tests; default-OFF FastAPI GET shell; **not production** |
| Oracle production | Existing server NOT changed/restarted; no real 2026-11-18 V2 preflight executed |
| Dhan | No V2 live call or consent operation verified |
| Android | Standalone Flet offline source at `pilot_v2/android_app`, version metadata 2.0.100 |
| Signed V2 APK / actual installed package | **NOT BUILT / NOT VERIFIED** |
| Live orders | OFF, no order route/action |
| Existing BOT KING | Untouched, remains reference and rollback |

## Category tracker — completed vs blocked
| Category | Tested or committed work | Still needed |
|---|---|---|
| 01. Repository and workflow | Isolated pilot branch, `pilot_v2/`; docs-only push regression exclusion; targeted latest-commit CI audit | Real integrated staging and release gates |
| 02. Identity and three mobiles | Master + max 2 delegated phone grants; hashed expiring SQLite sessions; disable/revoke offline PASS | Actual authorized master bootstrap, real Android Keystore and device enrollment |
| 03. Login cryptography | ECDSA P-256 challenge/nonce replay and durable key rotation; atomic current-key check + session issue, corrected CI #19 FAIL→#20 PASS | HTTPS/rate limits, real authorized pairing and audited server integration |
| 04. Watchlist demand | Five watchlists, global max 70 unique equities, adaptive selected 0/5/51/70; 3 independent indices | Real server-persistent selections and verified Dhan mapping |
| 05. Quote cache and scheduling | Shared revision/last-good cache; 429 cooldown; SQLite worker-shared quote leases | Trusted Dhan collector, entitlement, index/equity API split, freshness, real response |
| 06. V2 gateway | Strict versioned read-only schema, feature-flag OFF, GET quotes/indices protected by bearer+feed permission; CI #22 | Oracle actual integration, TLS and health/data smoke |
| 07. Candles and scanner | Timeframes and behavior specified: watchlist 3m; index Dashboard 1m; scanner 1m; Super Five 5m | Complete real historical retention, scanner auto-selection/chart sync, source evidence |
| 08. Filters | Five engine concept, evidence-gated WAIT; sixth slot **blank/reserved** | Valid actual futures/options/news/candle evidence and scoring; never fabricate percentages |
| 09. Mobile UI | Separate Flet V2 offline shell, API message fixture | Secure login client, Dashboard/Watchlist/Settings and filter UI, signed APK |
| 10. Oracle audit | Read-only `oracle_preflight.py` and operator instructions; synthetic CI #23 PASS | Execute on actual authorized Oracle host and inspect redacted report |
| 11. Android build | `android_build_gate.py` metadata preflight; intended `com.botking.bot_king_v2`, 2.0.100/code100 | Separate V2 signing build; inspect actual APK package, versionCode, certificate and install |
| 12. Journal and regression | Per-batch source+test+Master Journal+Work Log+Handoff; historic FAIL preserved | Append actual future CI results in each active turn; no asynchronous promise |

## All major completed CI stages and known error
- #1 V2 isolation; #2 journal; #3 **FAILED** malformed mock proof; #4 correction PASS.
- #5 continuation workflow; #6 P-256/token-status policy; #7 master-approved enrollment; #8 shared read-only cache; #9 70-share union.
- #10 quote budget; #11 persistent SQLite quote lease; #12 durable sessions; #13 P-256→session composition; #14 shared nonce; #15 new audit rule; #16 key enrollment/rotation.
- #17 fast-track audit; #18 dynamic current key + docs CI exclusion; #19 **FAILED** test reused rotated-out Master session; #20 correction PASS.
- #21 gateway/Android wire fixture; #22 OFF-by-default HTTP and offline Flet V2 shell; **#23 PASS** Oracle audit and prebuild metadata tooling.
- Above stage descriptions are OFFLINE evidence; no online market-data or installed APK proof. Each exact commit/run and failure detail remains in `V2_WORK_LOG.md`.

## Next schedule — stages, not calendar promises
**S1 — IN PROGRESS (offline collector capability gate added; actual Oracle report still pending):** Get actual **read-only** Oracle inventory from an authorized operator if access exists; otherwise continue offline Dhan capability/status/mapping and trusted collector contracts. Distinguish real Oracle evidence from synthetic assumptions.
**S2 — Shared Gateway + Dhan:** One authenticated, rate-limited data source for 1–3 phones; global 70+3 demand; 429 cooldown; revision/freshness/cache and per-device permissions, protected feature-flag OFF staging tests.
**S3 — Candles/5 filters + Android:** Develop candles/options/assessment evidence and Android UI *in parallel against one frozen API contract*. Preserve last good with honest stale labels, WAIT if evidence absent; sixth blank.
**S4 — V2 APK:** Separate build pipeline, signed package/version/certificate verification, first-phone functional smoke. No old-app replacement.
**S5 — Oracle controlled deploy:** Approved backup/preflight, reversible feature-flag rollout, health and protected-data tests, rollback; leave old BOT KING active until fully accepted.

## Rules for every "OK" and new chat
1. **Only the immediately preceding V2 commit and its actually changed files**, plus exact applicable CI. PASS→proceed; FAIL→fix same failure first; PENDING→follow that run. No automatic ten-commit checks. Broaden only if a concrete regression/dependency demands it.
2. Group 2–4 coherent source edits with corresponding tests and all three journals into **one mixed commit and one main CI**. Avoid redundant docs-only CI. Keep source PASS separate from production deploy and mobile verification.
3. For each live test/commit add a category-specific log row/entry: date, batch, touched files, previous SHA+CI, new exact SHA+run ID, PASS/FAIL/PENDING, actual test error, correction/retest, Oracle changed/restarted?, Dhan requests?, orders?, APK built/verified?, NEXT blocker.
4. Do not state that background work or automatic journaling happens outside active interactions. GitHub Actions may run; its actual report should be inspected and then journaled at the next active turn.
5. Production writes/restarts, Dhan OAuth consent, real external device enrolment, order access, signing secrets and old-app shutdown require their own secure authorization. Ordinary isolated GitHub V2 code/test/journal work may proceed without repeated micro-approval.

**New chat prompt:** "BOT KING V2 का Journal पढ़कर पिछला अधूरा काम आगे बढ़ाओ". Fetch branch HEAD + previous commit CI, read this register/Work Log, then continue from the earliest incomplete safe gate instead of asking for the project again.

## Latest S1 activity — S1-DHAN-CAPABILITY-FAIL-CLOSED-20261118
- Prior source CI #23 PASS. A pure offline quote capability planner and tests now require actual Oracle observation + Dhan authentication and separate index/equity entitlements before provider work can even be planned. **Real Oracle evidence still NOT supplied; GitHub synthetic PASS cannot certify it.** New commit CI pending. Category 05 remains PARTIAL; next verify exact CI, then real read-only Oracle report.

## Latest S1 integration — S1-READINESS-DURABLE-LEASE-INTEGRATION
- CI #24 `44304560985` PASS for prior capability contract. Staged offline coordinator now joins the capabilities matrix to one shared persistent rate lease for index and equity mock work, with no real Dhan call. New exact CI pending. Actual Oracle server capability evidence remains absent; S1 is NOT complete. Next verify new source CI, then read-only operator preflight.
