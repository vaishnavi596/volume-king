# BOT KING — Batch 4 audited benchmark (2026-11-14)

## Purpose
Freeze a source-evidence baseline before further Batch 4 work. This is a benchmark/checklist, not a claim of latest CI success, Oracle deployment, or phone acceptance.

## Source baseline
Branch: `fix/botking-2399-candle-retry-20261114`.
Comparison against main at audit: 277 commits ahead, zero behind; main SHA b4496b5e152fb63c0330fb1377631a2b4a9f40ae.
Files inspected: `docs/BOT-KING-SIX-BATCH-WORK-REGISTER.md`, `docs/BOT_KING_BATCH_4_FOUR_ENGINE_DESIGN.md`, `src/five_engine.py`, `tests/test_five_engine.py`, `tests/test_batch4_five_engine_ui.py`.
This branch comparison is a snapshot, not a permanent count.

## Acceptance evidence and no-regression gates
| Scope | Existing evidence | Must not regress | Remaining acceptance |
| --- | --- | --- | --- |
| B1 Dhan LTP/index | Work register reports v2.3.102 phone observations of 51 equity quotes + NIFTY/BANKNIFTY/SENSEX; exchange timestamps unverified | 51 equity scan distinct from 3 index cards, last-good price, no Yahoo/Angel fallback | Current build, live session freshness, cadence, resume and Oracle verification |
| B2 candles | Historical votes and candle guards documented; 5m votes are NOT proof of plotted OHLC | No missing/future/compressed timestamp promotion, timeframe isolation, cooldown | 51 equities + 3 indexes actual OHLC and timeframes on phone |
| B3 scanner/Super Five | Previous 51/51 and ranking reports; scanner adapter exists | No duplicate filters, no partial scan presented as complete, no double-counted technical/candle votes | Current build scanner latency, ranking parity and paper-mode tests |
| B4 five engines | Pure `src/five_engine.py` contract, source tests and UI cache-only tests exist | No unverified/stale/mismatched-source vote; absent engine => WAIT, never 0% bearish | Independently sourced technical, candle, news, futures, options with timestamps and measured evidence; shared cache, CI and phone tests |
| B5 UI | Compact watchlist/Settings UI source and tests present | Five watchlists, indices, diagnostics, Dhan preference persistence | Device navigation, reboot, refresh/resume |
| B6 release | Historical v2.3.102 signed APK and regression PASS recorded | versionName AND versionCode increase, signing, live orders OFF | Latest workflow results and final end-to-end install |

## B4 source-level audit findings
1. `ENGINE_NAMES` = technical, candle, news, futures, options. `EngineEvidence` validates complementary integer percentages, timestamp and eligibility. `combine_evidence` requires 3 eligible engines and directional agreement; it is not a win probability.
2. `snapshot_for_display` rejects stale timestamps, future timestamps and source mismatch at render time. `scanner_snapshot` rejects duplicate filter names and invalid vote values; technical and candle are not double-counted.
3. `option_from_component` does NOT manufacture a percentage from a directional label or PCR. `news_from_headline_cues` leaves unverified RSS headline cues as WAIT. Futures evidence adapter/data path not verified in inspected files.
4. UI tests assert cached summary usage without per-engine network fanout; these are source assertions, not phone proof.
5. Source string convention differs: some scanner/technical fixtures use `source="dhan"` while render-time gate defaults to `expected_source="Dhan"`. Verify canonicalization at every adapter boundary before adding real evidence; do not loosen source verification blindly.
6. The older six-batch register contains historical QUEUED labels superseded by its refreshed v2.3.102 section; neither is current acceptance for this branch.

## Next grouped work, in order
- B4-A: Canonical provenance contract (source casing, freshness, timestamp and independent evidence) with targeted regression tests; no real orders.
- B4-B: Read-only News and Futures data availability audit; never invent strength or infer money flow from OI alone.
- B4-C: Options listed expiry and ATM +/-3 *listed strike levels*, premium/OI/volume fields only if verified; fail closed on 429, missing fields and unverified freshness.
- B4-D: Shared cached snapshot across Dashboard, Scanner, Watchlist and Super Five, with no duplicate polling; verify conflict/WAIT states.
- B4-E: Run focused and full offline regression, review GitHub Actions, signed APK version/signing and phone test before declaring PASS.

## Status
BENCHMARK DOCUMENTED; latest CI, Oracle deployment and Android end-to-end NOT VERIFIED in this audit. No change to live order routing.
