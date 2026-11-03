# BOT KING v1.8.0 audit

Validated locally with Flet 0.25.2: 52 offline tests passed; Python compilation passed for all source and test files.

Included changes:
- Persistent Hindi / English selector on all four pages. Display translations preserve dropdown keys, symbols, entered values and credentials.
- Reversible translation and dynamic status updates; technical symbols/provider names remain unchanged. Unknown source messages retain their original text rather than disappearing.
- Hindi and English contextual info dialogs for sections and field controls; validation and option freshness/coverage statuses are derived at click time. Credential values never appear in help.
- Analysis uses completed candles and rejects invalid OHLC/volume, future/duplicate/unordered timestamps, insufficient history and stale input. Indicator agreement remains explicitly distinct from success probability.
- Existing Auto/Yahoo/Angel read-only routing, paper controls, persistence, backup and generation guards retain regression coverage.

Limits:
- No Android device rendering or live Angel One login was performed in this audit.
- Analysis is rule based; no trained AI or profit guarantee is introduced.
- No live order placement, live automatic exit, push notification service or complete backtest engine is added.
- Data availability and polling latency remain dependent on the provider. Yahoo fallback does not supply verified NSE option-chain or option premium history in this adapter.
