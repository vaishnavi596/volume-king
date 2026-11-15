# BOT KING B1 joint five-engine data integration audit — 2026-11-15

Branch: `fix/botking-2399-candle-retry-20261114` after v2.3.119.

## Verified current architecture
- `src/five_engine.py` requires five independent typed engines and a minimum quorum of three source- and freshness-verified engines. Technical scanner votes must not be counted again as an independent candle engine.
- News headline keywords are contextual only, not a measured, source-verified bullish/bearish impact percentage.
- `futures_market_context` and `resolve_verified_futures_contract` validate futures fields and instrument-master mappings **only after independently verified data is supplied**. There is no read-only Dhan Futures backend acquisition route in the currently audited `backend/server.py`; futures therefore remain WAIT.
- Dhan `/dhan/option-chain` supports mapped NIFTY only. `calculate_option_metrics` calculates PCR as total Put OI / total Call OI and Max Pain from OI-weighted intrinsic payout. Its `signal_eligible=false` and unverified freshness are intentional. The 7-strike ATM window requires spot and seven valid listed contracts; missing fields are not zero.
- The app's five-engine snapshots are built from `scanner_snapshot(...)` technical votes only. Missing independent Candle, News, Futures and Options directional data cannot be activated by toggling settings.
- NIFTY option expiry + metrics were already fetched on Options, but not reliably from the Home/Scanner screens.

## B1 applied fixes
- Use one paced and shared `refresh_selected_options` from Home, Scanner and Options during the market session, if Dhan is connected and NIFTY option mapping is selected; maintain at least 60 seconds between attempts, and the expiry/option-chain pacing gate. No additional quote or candle-history fetch from this option loop.
- Publish the existing PCR/Max Pain/ATM availability in Super Five context and the O chip for NIFTY without calling it a bullish/bearish vote or 100% evidence.
- Display cached headline count as News context (N WAIT) rather than fake sentiment percentages.
- Add dedicated offline tests to guard no extra history polling, Dhan-only selection, safe gating, and Futures WAIT without verified mapping.

## Remaining release blockers for full five-engine functionality
1. Futures: verify authenticated Dhan instrument-master NFO contracts, expiry and quote/OI entitlements; implement a backend read-only futures quote endpoint and client adapter with rate limiting and provenance tests.
2. Candle: independent completed-bar, price-action-only evidence algorithm with exchange-time provenance so technical votes are not duplicated.
3. News: licensed, timestamped and issuer-tagged source plus a calibrated impact-confidence method. RSS keyword cues do not justify precise probabilities or market-direction percentages.
4. Options: verify current Oracle authenticated expiry, chain payload, seven-strike ATM window and provenance; only separately validated measured directional flow may create an Options engine vote.
5. Release: GitHub offline regression PASS, signed APK versionName/versionCode increase, hardware smoke tests for options and the five-engine UI.

## Safety
- Do not enable broker order routing, simulate missing quotes, promote last historical prices as verified live, or reactivate Yahoo Finance/Angel One.
- A GitHub green build validates local contract/tests, **not** current live Dhan Futures/OI entitlements.
