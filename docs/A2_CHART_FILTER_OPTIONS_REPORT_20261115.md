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

## Device screenshots received 15 Nov 2026 — follow-up findings

Six screenshots distinguish two installed builds: four images labeled **2.3.115** and two historical screenshots labeled **2.3.110**. These are observations from installed APKs, not confirmation that A2 patches have been installed.

- 2.3.115 shows NIFTY option strikes unavailable; ATM window 'Not yet verified'; OI/PCR/Max Pain boxes show missing metrics. Selected expiry and Oracle response are not visible; root cause remains unconfirmed.
- 2.3.115 option chart incorrectly demanded Angel One sign-in in Dhan-only mode. Follow-up commit 15af1e95 removes that legacy UI and does not fabricate option premium history.
- 2.3.115 scanner OI Support, OI Resistance, OI Profile and Max Pain show UNAVAILABLE. They can be selected/saved, but cannot vote BULLISH/BEARISH without validated directional evidence.
- Historical 2.3.110 showed 51/51 quotes and candles; exchange-live timestamps were explicitly unverified. Other historical diagnostic events included dhan_connect_http, chart, and watchlist_dhan_batch FeedError.
- Regression guard for the legacy option chart prompt: 7ddbaaea.

**Pending before release:** Verify authenticated Oracle Dhan option-expiries and option-chain responses and whether ATM seven-strike data is present, run offline CI and Android device tests, and bump both app versionName and versionCode for a new signed APK. Do not claim Dhan historical CE/PE premium candles until a verified route exists.

## 15 Nov — user-confirmed filter baseline and A2 extension

The user confirmed the existing 10-slot remove-three/add-three behavior works; **do not change or regress it**. Keep maximum ten active, ordered and saved. Additional feature work is separated from the APK acceptance gate.

- News Headlines is now a selectable context filter, not an eleventh default slot; selecting it requires a free slot. It reports cached headline counts/cautious headline cues without manufacturing directional votes (commit 713706d2).
- OI Support, OI Resistance, OI Profile and Max Pain are selectable/savable. For matching NIFTY expiry, scanner details show Dhan read-only option-chain context (highest PE/CE OI strike in seven-row ATM window, seven-strike profile availability, Max Pain). Unverified chain context is never a BULLISH/BEARISH scanner vote (commit 70a9541a).
- Offline regression guards for ten-slot cap and news/OI context were added (commit 01346b15).
- Futures expansion and other new features are deferred; existing Dhan Option Chain and white-chart fixes stay in A2 scope.

**Release is still blocked** until offline CI PASS, confirmed Oracle authenticated option-chain payload, Android verification and signed APK/versionName/versionCode checks. Do not assume a GitHub commit produces an APK.

## Release candidate 2.3.116 — joint commit 15 Nov 2026

User confirmed the ten-slot remove/add feature already works and must remain unchanged. New optional News Headlines and four OI contexts are read-only and count against the same maximum ten slots, never an eleventh automatic filter.

Latest code commits: 713706d2 (news selectable), 70a9541a (read-only Dhan OI and cached news details), 01346b15 (regression guards), 422b72c9 (report), b61674f9 (release version bump / CI build trigger).

Expected release versionName: 2.3.116. GitHub build workflow computes versionCode from run number and validates aapt output. **At report update time no passing APK build or downloadable artifact has been verified.**

Keep entire A2 package subject to actual Android chart, filter persistence, NIFTY expiry/chain read-only response checks, unit regression and signed build gates. The Dhan-only option historical premium chart cannot be enabled without a validated Dhan route.