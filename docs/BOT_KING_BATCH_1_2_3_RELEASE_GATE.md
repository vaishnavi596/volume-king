# BOT KING — Batch 1–3 release gate tracker

Updated: 2026-11-14. This checklist is a release gate, not a claim that CI alone validates a phone or Oracle service. Checkboxes mean the stated evidence exists; unchecked items remain open. Never calculate completion percentages from guesses.

## Batch 1 — Dhan / Oracle / app LTP and refresh (1/5 end-to-end verified; user-confirmed auto-refresh partial evidence)
- [x] Independent NIFTY, BANKNIFTY and SENSEX LTP verified on Oracle and phone (all 3; no candle-as-LTP)
- [ ] 51 equity watchlist prices refresh on schedule without Yahoo/Angel fallback (user confirmed automatic refresh; 51/51 coverage and provider isolation still require evidence)
- [ ] Last valid price retained on failed refresh, with clear stale/unverified state
- [ ] Background/foreground recovery and provider-generation guards validated on device
- [ ] Dhan 429/cooldown, index fallback and Error Doctor tested end-to-end

## Batch 2 — Candles / historical scan (0/4 end-to-end verified)
- [ ] 5m history for all relevant watchlist equities and all 3 indices validated on Oracle and phone
- [ ] Missing/duplicate/invalid candle cases handled with WAIT and clear reason
- [ ] Dhan historical 429, retry, pacing and cache recovery verified under load
- [ ] Independent candle scan cannot overwrite LTP or trigger duplicate quote requests

## Batch 3 — Scanner / Super Five / signals (0/5 end-to-end verified)
- [ ] Indicator calculation and flat-candle/RSI/Supertrend safeguards regression and device verified
- [ ] Candle integrity, missing-bar, future-bar, duplicate-bar regressions and device verified
- [ ] Super Five vote agreement, freshness, deterministic tie-break and unverified-data exclusion verified
- [ ] All enabled filters audited for unavailable OI/options and misleading success-probability claims
- [ ] 51-symbol scan completes at acceptable speed; top-five and paper signals tested on device

## Evidence
- Offline CI success: 43590314217 (commit a783b410); 43590301814 (0e908caa); 43590169857 (3bc320c9).
- Previous APK 2.3.105 predates current Batch 3 fixes. No final APK has been built for these changes.
- Index Oracle-to-phone verification completed 2026-11-14; see evidence section below.

## Latest offline evidence (2026-11-14)
- Dashboard verified-ranking integration: CI run 43591138853, PASS, commit f570d0f.
- Dashboard ranking parity regression: CI run 43591146577, PASS, commit 3335f61.
- Source/offline checks only; Oracle and mobile release gates remain unchecked.

## Release gate
1. Complete remaining source/code audit and add regression tests for uncovered failures.
2. Run full offline CI on exact final commit, then check Oracle read-only endpoints without exposing secrets.
3. Bump versionName and versionCode, build signed APK once for combined Batches 1–3.
4. Install and run mobile smoke tests. Only mark a batch complete when its end-to-end checklist is verified.
5. Keep live order routing disabled. Do not proceed to other batches until the agreed release gate is satisfied.

## Cross-screen consistency gate (OPEN)
- [ ] Dashboard Super Five and Scanner use the same validated signal calculation and ranking rules.
- [ ] Watchlist and Dashboard reuse the same Dhan LTP state without turning historical candles into live quotes.
- [ ] Charts and Scanner share validated candle interpretation but keep timeframe-specific caches separate.
- [ ] Paper Bot receives only eligible verified signals; historical/unverified votes cannot trigger orders.
- [ ] Every screen shows consistent source, freshness, WAIT reason, and unavailable-filter status.

### Audit finding (2026-11-14)
**Resolved in source, not yet device-verified:** `src/main.py::publish_partial_ranking` now calls `src/scanner_engine.py::rank_candidates` for verified Dashboard candidates (f570d0f). Historical fallback remains WAIT-only. Source parity regression passed CI 43591146577; functional Dhan freshness/vote-integrity tests passed CI 43591479340 (ba96572). Keep cross-screen release checkbox OPEN pending Oracle and phone verification.

### Paper Bot source audit (2026-11-14)
- `src/main.py` Paper Bot uses a manual tick engine; Start and Process mark do not consume Scanner/Super Five candidate rows and do not place broker orders.
- Therefore cross-screen Paper Bot signal eligibility remains OPEN: the present manual-only behavior is safe from unverified automatic entry, but an automatic verified-signal handoff has not been implemented or device-validated.
- Watchlist Dhan candle freshness gate added at feb36617, regression at 4bbdfcf; offline CI runs 43591303233 and 43591310296 passed. This does not establish Oracle/mobile freshness.

## Oracle and Android evidence — 2026-11-14
- Authenticated Oracle `/dhan/index-ltp-batch` returned `source=dhan`, NIFTY 25144.30, BANKNIFTY 61034.10, SENSEX 81592.45 in one successful batch request. The Android v2.3.105 Watchlist screenshot displayed exactly those three LTPs with exchange timestamp unverified; the index Oracle-to-phone mapping is verified.
- User explicitly confirmed both automatic refresh mechanisms work on device. Screenshot displayed `Next 34s`; retain this as user-confirmed refresh evidence, not proof of a newly timestamped exchange quote. The 51-equity end-to-end coverage checkbox remains open until all symbols are checked.
- Screenshots displayed RELIANCE 1339.70, HDFCBANK 804.00, ICICIBANK 1583.60 and historical 5m votes labeled NOT live. Historical candles dated 13 Nov 2026 15:10 IST; no claim of verified live signals.
- Existing evidence line above referring to outstanding BANKNIFTY/SENSEX verification is superseded by this section. Remaining Batch 1 gates: all 51 equities, failed-refresh last-price recovery, background resume, and 429/Error Doctor end-to-end. Do not deliberately cause 429 to test.

### Oracle 5m candle coverage — 2026-11-14 (read-only run)
- User ran `backend/audit-dhan-51-candles.py` on Oracle for 2026-11-13: **53/53 VALID**, empty 0, invalid 0, HTTP errors 0; no 429 observed and no order endpoints called.
- The 53 tested mappings comprise **51 equities plus BANKNIFTY and SENSEX**; NIFTY is explicitly excluded by the audit script's `DHAN_VERIFIED_SYMBOLS - {"NIFTY"}` selection. Therefore this does **not** establish all-three-index candle coverage.
- Most instruments returned 71 bars; BANKNIFTY, SENSEX and TMCV returned 74. The script checked requested-day/session and structural validity, not verified live timestamps or full app rendering.
- Batch 2 first checkbox remains OPEN until NIFTY 5m candles and phone coverage are verified. Historical 429 recovery and device cache isolation are separate OPEN gates. No need to rerun the 53-symbol audit without a new reason.
- NIFTY chart redundant LTP removal c38a6e3 passed offline CI 43593479881; regression guard 939e1b0 passed CI 43593602141.

### NIFTY completes Oracle historical coverage — 2026-11-14
- User executed one read-only authenticated `/dhan/intraday` NIFTY request for 2026-11-13 at 5-minute interval: HTTP 200, 74 bars, `HISTORICAL VALID: True`, `LIVE VERIFIED: NO`.
- Combined with prior 53/53 valid audit: **54/54 mapped instruments on Oracle** (51 equities + NIFTY, BANKNIFTY, SENSEX) have valid historical 5-minute data for the tested session; no observed HTTP errors or 429 in these tests.
- This closes **Oracle historical coverage only**, not the Batch 2 end-to-end checkbox: mobile rendering, invalid/partial recovery and historical 429 behavior remain open. Do not conflate historical coverage with exchange-timestamp-verified live prices or signals.
