# BOT KING — Batch 7 Futures Integration (DEFERRED / BIN)

Status: PARKED. Do not implement, enable, or ship futures market-data integration during Batches 4, 5, or 6.

## Resume gate
Resume only after Batch 4, Batch 5, and Batch 6 each finish their planned changes, regression audit, and relevant APK validation. This file is a planning archive, not runtime configuration.

## Existing groundwork (retain, do not activate)
- Pure read-only contract resolver: `src/five_engine.py::resolve_verified_futures_contract`.
- Pure read-only market context normalizer: `src/five_engine.py::futures_market_context`.
- Regression guards: `tests/test_five_engine.py`.
- These helpers are not connected to a live Futures endpoint; do not mistake CI PASS for live broker entitlement.

## Batch 7 work queue
1. Obtain official Dhan instrument master and verify its schema, provenance and update cadence.
2. Normalize listed futures by underlying, exchange segment, instrument type, exact expiry and security ID; reject ambiguous or expired mappings.
3. Confirm actual Oracle token entitlement with a strictly read-only NSE_FNO quote request. Do not log tokens or change broker credentials.
4. Add rate-limited/cached futures quote support only after permission is verified; handle 401/403/429, stale data and missing OI/volume without fallback.
5. Validate exchange timestamps, contract mapping, price/volume/OI fields and limitations of directional inference; do not fabricate futures flow or trade-side information.
6. Integrate into five-engine UI behind an explicit verified-data gate; missing futures remains N/A / WAIT and must not cast a vote.
7. Run regression, server audit and end-to-end mobile tests before a separately versioned APK.

## Isolation rules
- No futures endpoints, subscriptions, order routing or automatic retries are enabled by this plan.
- Do not move or delete currently imported `src/five_engine.py` helpers or their tests: that would risk breaking Batches 4–6. This bin document parks the future integration work, not executable runtime modules.
- Keep Dhan-only sourcing, no Yahoo/Angel fallback, and live orders disabled.
