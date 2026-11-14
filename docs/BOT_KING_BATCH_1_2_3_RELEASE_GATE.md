# BOT KING — Batch 1–3 release gate tracker

Updated: 2026-11-14. This checklist is a release gate, not a claim that CI alone validates a phone or Oracle service. Checkboxes mean the stated evidence exists; unchecked items remain open. Never calculate completion percentages from guesses.

## Batch 1 — Dhan / Oracle / app LTP and refresh (0/5 end-to-end verified)
- [ ] Independent NIFTY, BANKNIFTY and SENSEX LTP verified on Oracle and phone (all 3; no candle-as-LTP)
- [ ] 51 equity watchlist prices refresh on schedule without Yahoo/Angel fallback
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
- Existing screenshots show partial index availability; BANKNIFTY/SENSEX Oracle-to-phone LTP verification is still outstanding.

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
`src/main.py::publish_partial_ranking` sorts candidates locally by historical/bias/score/timestamp, whereas `src/scanner_engine.py::rank_candidates` applies stricter vote verification and confirmation/recency tie-breaks. Therefore **the recent rank_candidates improvements are NOT yet proven to affect the displayed Dashboard Super Five**. Do not mark cross-screen consistency PASS or claim these changes are already reflected everywhere. Integrate a shared ranking policy with explicit historical-display mode (no promotion to live) and add cross-screen regression coverage before final build.
