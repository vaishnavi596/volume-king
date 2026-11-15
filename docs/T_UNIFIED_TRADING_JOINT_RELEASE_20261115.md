# BOT KING Unified Trading Page — joint paper-bot release audit (2026-11-15)

Branch: `fix/botking-unified-paper-trading-20261115`; previous verified APK version: `2.3.122`. This branch is *not* a production Oracle deployment.

## Implemented, testable in Android
- Options/Trading page now contains **one Paper Bot control area**: BUY, SELL, EXIT, manual mark processor, Paper Start/Pause/Stop, contract/lot/quantity, entry, stop loss, target, charges, risk limits, advanced trailing/partial/protection controls, journal and disabled Live BUY/SELL controls. App Settings no longer owns the trading configuration controls.
- **Five independent paper-bot profiles** (Bot 1 to Bot 5): instrument, side, strike, expiry, quantity, mode, fees/break-even options and each open position save independently. Legacy single `bot_position` migrates to Bot 1. A profile change stops the running *local* paper bot; existing paper positions remain available for later manual operation.
- Read-only Dhan historical 5m mini-candle renderer and the existing shared five-engine/Oracle assessment status are displayed in Trading; no new per-render broker fan-out. Selected paper symbol is included in the bounded assessment poll (max three selected contexts).
- Paper profit presets 25%, 50%, 75% configure partial quantity; 100% is explicit EXIT. **None of these presets executes automatically without a user-supplied manual mark.** Stop/target/trailing and partial profit are evaluated only when manually processing a price mark.
- Optional paper break-even after a user-selected favorable percentage, with estimated round-trip fee buffer; old engine behavior unchanged when option disabled.
- Partial exits deduct manually entered estimated charges and update realized paper profit/loss. Local portfolio journal records tagged `kind=paper_simulation` with a 300-event bound. Each profile has a realized net paper P&L summary.
- Trading page displays **local callback time** for paper BUY/SELL/EXIT and manually processed marks. This is **not** Dhan network, market-event-to-order, Android UI-delivery or fill latency. No 1-second/2-second/3-second end-to-end service-level claim.
- Live broker BUY/SELL buttons are **disabled**. No live order gateway is enabled; the Oracle readiness endpoint is read-only and cannot execute trades.

## Critical remaining limitations (never claim these are solved)
1. Dhan option contract-specific CE/PE premium, authenticated instrument master, trading lot/strike validation, order placement and execution receipts are not implemented in the app. The older option-chain Paper BUY/SELL buttons still correctly reject missing verified option premium and lot size.
2. Multi-profile paper positions can coexist, but only the **selected profile** runs a manual-mark bot. There is no unattended, always-running, broker-priced strategy engine for multiple symbols, and no phone-lock continuity claim.
3. Legacy Quick Paper and Chart Paper state paths are still separate; *new* trading workflows should use Trading Center's portfolio profiles. A future cross-path migration and transactional reconciliation is required before any live trading.
4. Per-profile portfolio journal is simulation-only, not a broker fill ledger or durable cloud order book. App preference write failure and uninstall/data-clear can lose records. Do not rely on paper P&L for tax reporting or actual profit.
5. 25%/50%/75% are settings for the existing single partial-booking rule, not a four-stage unattended scale-out. Fees are entered manually and not verified against a broker contract note.
6. Live mode, emergency flatten, market-feed freshness, actual order acknowledgement, broker margin, server-side risk checks, 1–3 second latency and order-id reconciliation all require a **separate future implementation and authorization**.

## Release gate
- Run full GitHub offline regression on final source commit, not earlier failed runs.
- New `pyproject.toml` version must differ from 2.3.122; APK workflow uses increasing Android `--build-number`, verifies versionName/versionCode and signing certificate.
- Android installation, candle rendering, multi-profile position persistence, P&L and live-button lock **must be tested on device** after build.
- No production Oracle restart or order request in this branch.
