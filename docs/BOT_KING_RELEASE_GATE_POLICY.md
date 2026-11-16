# BOT KING — Joint Audit First, APK Last (Release Gate)

**Owner decision — 2026-11-16.** This release rule applies to every future BOT KING Android APK. No emergency, market-hours deadline or convenience overrides these gates. The already running v2.3.130 Build #645 is allowed to conclude as a **diagnostic candidate**, not a completed/approved production release. Do not start another APK build merely to observe unresolved Oracle problems.

## Non-negotiable release order

1. **Consolidate all known defects** from the latest user phone screenshots/reports, source code, existing Journal/Handoff, and the latest **eight GitHub Actions runs**. Identify overlap and unresolved items; classify by GitHub app, GitHub backend, customized Oracle production, Dhan upstream, and device.
2. **Complete source and server fixes first.** Batch related add/edit/delete changes and tests together. Do not overwrite Oracle's customized `/opt/bot-king-server/server.py` blindly. Take a timestamped backup before any production edit; stage/diff, syntax check, deploy with rollback and health proof. Never log/read out pairing keys or OAuth secrets. Live broker orders remain OFF. No Yahoo or silent provider fallback.
3. **Prove actual App↔Oracle contract** (not just repository source parity): running deployed route/method, authentication, schemas, quote freshness/collection age, three index prices, selected equities, 5m candles/history, option expiries/chain as entitlements allow, four factor/filter assessment, 429 cooldown and provider request pacing. Distinguish unavailable data from valid signals. Use existing GET-only collector and route audit scripts first. Avoid excessive Dhan probes.
4. **Close the complete regression suite** on exact intended release HEAD: zero unresolved failures and no source/test assertions stale from previous design. Check the current and latest eight runs by commit and job; append evidence to `docs/BOT_KING_WORK_LOG.md`.
5. **Build only after gates 1–4 are evidenced**, then bump **versionName and versionCode** (not one alone), ensure visible UI version and signed artifact checksum/certificate, and run APK test. CI build PASS is not Android device PASS; test real mobile Watchlist first refresh, NIFTY/BANKNIFTY/SENSEX, candles, scanner, Super Five, options, background/resume, Error Doctor and paper-only controls. Journal any remaining failure.
6. **Stop release if any blocking gate fails or is unknown.** Label the APK as candidate/unverified and return to fixes; never represent missing Oracle or phone evidence as PASS.

## Required journal fields per batch

- Date (IST), branch, exact commits/file deltas and purpose
- CI run/job/attempt, counts, outcomes; actual error lines and repair
- Oracle deployed source hash, backup hash/location, server env safe flags, live route/data readiness and Dhan limits; explicitly mark **NOT RUN** when unverified
- APK run, versionName, versionCode, signing and artifact; device observations separately
- Blocking defects, decision and the next minimum grouped actions

## Current hold — as of 2026-11-16

- Existing **v2.3.130 Build #645** was triggered *before* Oracle production data agreement. Let it complete for diagnostics; do not advertise it as fully corrected.
- Oracle Collector enablement, actual /v2/snapshot age/count and running nine API routes remain **NOT VERIFIED**. Source default collector OFF, nominal 90s/min60s is **not** the live Oracle setting without inspection.
- Four logical lanes and small phone-side caching are **not** a deployed four-lane Oracle data collector; 15–30 second fresh upstream data has **not** been demonstrated. More rapid mobile timer alone must not be used as proof.
- Next release must be blocked until all gates above are satisfied or an explicitly documented supported feature scope demonstrates a smaller verifiable acceptance contract; no silent exception.
