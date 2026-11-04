# BOT KING v1.9.0 monitoring audit

## Implemented in the APK
1. Separate execution-capability display: read-only market data, paper simulations and saved preferences are distinguished; live execution remains disabled.
2. Strict completed-candle freshness: 1m 150s, 3m 390s, 5m 630s; cached data cannot publish a new live signal.
3. Per-component health records: request/data/success timestamps, redacted errors, bounded broker retry backoff, session-expiry handling, manual retry.
4. Progressive Super Five: publish results as companies finish; show checked/valid/cached/failed counts and preserve the last successful five-row watch panel. The same fetched 5m/5d data is reused instead of requesting a second all-company batch.
5. Contextual help now shows the selected market/options/news/chart component's actual request state. Existing Hindi/English and public snapshot persistence remain.
6. Lifecycle handling: pause while-open poll loops when backgrounded, clear pending paper confirmation, refresh selected data on resume. This is not a foreground service and does not guarantee screen-off continuity.

## Evidence
- 73 offline regression tests passed using Flet 0.25.2.
- All source and test files compile.
- Tests cover obsolete responses, retry limits, secret redaction, token expiry, short-timeframe freshness, progressive five-row updates, neutral-data labeling, pause/resume scheduling, truthful execution capability state and option-specific errors.

## Still required before live auto trading
- Actual Angel One account login/session and contract validation on device.
- Live streaming with heartbeat/reconnection (the APK still uses polling).
- Real broker order creation/modification/cancellation and duplicate/partial-fill handling.
- Accepted broker-side protective orders and confirmation.
- Production averaging/re-entry/trailing rules with actual position and realized-loss limits.
- An always-on backend with secure session management and broker reconciliation.
- Push alert delivery and remote emergency control.
- End-to-end paper/forward testing, screen-lock/network-loss/server-restart scenarios, followed by any explicitly authorized limited live validation.

No Android device or live account was available during this audit. The above pending work is not advertised as completed. Default APK signing is retained as requested; no custom signing secrets are required, and future in-place update compatibility is not guaranteed.
