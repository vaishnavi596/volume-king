# BOT KING A2 — Chart / Filter / Dhan Option Chain recovery

Date: 2026-11-15  
Base: `fix/botking-2399-candle-retry-20261114` / BOT KING 2.3.115  
Scope: mobile UI and offline regressions; **not a production server deployment**.

## User-reported failures
1. Scanner Lightweight chart sometimes remains white without candles.
2. Assessment/central filters show but Add/ON/Save appear unresponsive.
3. Dhan Option Chain and expiry-dependent fields do not refresh/display as expected.

## A2 changes applied
- Android WebView initialization now has a bounded recovery path followed by a native BOT KING OHLC candle renderer. Existing Dhan historical candles are reused; there is no Yahoo or Angel One fallback. Users can retry Lightweight from the native display.
- Filter Add/Remove callbacks no longer synchronously recompute the full (up to 51-symbol) watchlist, which could block Android taps. Saved 10-slot selections remain authoritative, and the local analysis loop picks up changes. Full 10/10 slots still require removing one filter first; unverified OI filters may be selected but MUST stay WAIT.
- Dhan Option Chain has an explicit visible Refresh control and clear disconnected feedback. Changing symbol or expiry initiates a new Dhan request when connected. Expiry lookup and option metrics remain paced, read-only, and NIFTY-only until mapping is verified.

## Commits in A2
- `a966a908` native chart fallback, Dhan Refresh, filter feedback
- `dfa6b16b` offline A2 regression guards
- `47521e91` expiry/symbol option auto-refresh
- `0350b865` extend option regression guard
- `d12b4548` avoid 51-symbol analysis inside Add/Remove callback

## Safety boundaries
- No orders enabled. No fabricated premiums, OI, missing candles, or live freshness.
- Dhan PCR / Max Pain / ATM rows are *unverified* and display-only; signals stay WAIT.
- Existing secured pairing key and Oracle token are not changed.
- The Flet app version remains **2.3.115** for source-only A2; release version AND Android versionCode must be advanced together before an installable release.

## Required acceptance gates (NOT yet all verified)
- [ ] Offline regression workflow **passes** (including all pre-existing mobile regression tests).
- [ ] Android: chart opens with valid Dhan candles, and WebView error switches to native candles rather than a blank white block.
- [ ] Android: remove 3 active filters, then add 3 from available pool; exactly 10 saved, settings survive app restart/upgrade.
- [ ] Android: OI Support, OI Resistance and Max Pain can be ON while unsupported votes remain WAIT.
- [ ] Oracle authenticated: `/dhan/status`, `/dhan/option-expiries`, `/dhan/option-chain` return valid Dhan-only responses, using the existing pairing header.
- [ ] Options page: manual Refresh plus symbol/expiry switches show consistent broker-listed expiry, PCR, Max Pain and ATM strike window; errors give a real status.
- [ ] Signed Android APK build passes and versionName/versionCode have **both advanced** after all quality gates.
- [ ] Phone install and 30-second foreground/background recovery smoke tests.

## Current status
**PATCHED IN GITHUB — NOT YET END-TO-END PASS.** Source commits and test guards are in the branch. GitHub Actions results, Oracle integration, signing and device confirmation are separate verification gates. Do not label this batch completed or ship the APK before those checks pass.
