# BOT KING CLONE — 2026-11-20 continuation after prior chat

Scope: CLONE-only, active branch `pilot/v1-pure-original-clone-phone-20261120`. Preserve V1/V2 and Oracle runtime unchanged.

## Verified on continuation
- Branch tip `398a625e73f79f27ac2031586df03a4626e7c656` (documentation-only original V1 mapping comparison).
- Original V1 B1 index mapping and Clone source mapping agree: NIFTY IDX_I/13, BANKNIFTY IDX_I/25, SENSEX BSE_I/51 (instrument INDEX).
- Correct picker display order NIFTY > BANKNIFTY > SENSEX (FINNIFTY follows as optional); display order is NOT a provider quote fix.
- Run https://github.com/vaishnavi596/volume-king/actions/runs/44780583293 completed SUCCESS; artifact `BOT-KING-B3-INDEX-ORDER-2.3.136-PHONE-APK`, artifact id 14652786482, present and not expired at inspection. This supersedes earlier queued status in work log.
- Related targeted B1 #44780499732 SUCCESS; B2 #44780457773 SUCCESS; Adapter #44780457748 SUCCESS.
- No evidence yet that SENSEX quote/candle FeedError, Scanner request errors, unknown WebView control, or true mobile/Oracle end-to-end data reception are fixed. Do not mark as accepted.

## Next work / release gate
1. On phone, test signed 2.3.136 while preserving installed 2.3.135 until backup/update signing compatibility is checked.
2. Verify picker first three indices, Dashboard index prices and 1m candles, Watchlist 3m equity bars, Scanner selectable timeframe and successful data fetch, SENSEX independently.
3. Capture sanitized Clone Oracle index quote/candle request status and response shape to distinguish partial broker response, throttle 429, authentication/entitlement, or historical candle gap; never guess/modify BSE_I/51.
4. Review bounded, separate Index/Equity/Scanner retry semantics in Settings; existing Retry data does not retry index/equity paths according to previous source audit.
5. Only after evidenced runtime root cause, apply combined CLONE-only source fixes and targeted regression tests, record exact changed files + run IDs, and then publish fresh phone APK. Do not redeploy Oracle or generate unnecessary APKs.

Continuation inspection itself was read-only; no server calls or live Dhan requests were made.
