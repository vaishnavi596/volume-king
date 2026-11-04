# Page-wise layout and execution audit — requested 2026-11-04

Report only: no app source, APK or production server was changed for this audit. The phone is showing the installed 2.1.0 release. The five-page 2.2.0 preparation exists only as source; it has not been built or installed.

## Main finding

Separate three independent facts: market-data freshness, permission to send real orders, and order/position protection. A broker login is not proof of fresh quotes, and fresh quotes do not mean real orders are armed. Moving controls to a new page does not implement live SL/target or automatic Paper marking.

## Home

- Keep selected candle analysis, the candle/options/news combination, Super Five, market overview, API/session status and news/events.
- Replace the large `EXECUTION CAPABILITIES` card with a compact status banner: actual source, quote/candle time, data age, broker session, and separately whether real-order access is disabled/disarmed/armed. Put long operational explanations behind an information control.
- Replace `My Positions • Paper Only` with a read-only summary of actual broker positions, filled quantity, available P&L and order status, with a link to the Live page. Missing or failed broker data must show unavailable, not a fabricated zero or flat account.
- The `TODAY'S PAPER RISK` caption describes a useful Paper metric, but its full controls/data belong to the separate Paper page. If Home later shows a live-risk card, it must be derived from the real journal/positions and explicitly distinguish entry limits/planned exposure from actual P&L or stop protection.
- Do not put trading forms, Paper strategy controls, or duplicate general settings on Home.

Prepared 2.2.0 already removes Paper positions/risk from Home and provides a link to the live account page. The large capabilities card still exists, and the desired real-position summary is not yet implemented there.

## Live / Options — one scrolling page

Keep symbol, exact listed expiry, option chain, strike/CE/PE selection, current premium and time, verified lot size, quantity, editable LIMIT price, order review/confirmation, actual order records, positions and cancellation together. Keep option chart and OI/PCR/activity metrics on this page.

All real-order strategy settings should belong to this page. Stop loss, targets, trailing, averaging, re-entry, partial exits and execution mode must only be available where the corresponding real-order behavior is implemented and verified. Display planned values separately from an actually acknowledged protective broker order. Do not reuse Paper-only switches as real automation.

The current real-money acknowledgement/arming form is an order permission control. It belongs here, rather than being repeated under general Settings. Enabling permission must remain separate from confirming an individual order. Disarming is not cancelling an order or closing a position.

Prepared 2.2.0 already combines option selection and manual real-order controls, with order/position lists in one page. Exact contract selection is linked; changing symbol/expiry invalidates old price/confirmation. Automatic LIVE SL/target and unattended bot protection remain unimplemented; server deployment and actual broker testing remain outstanding.

## Settings — general connections and preferences

Keep broker/API login, server address/access, data provider, session status, language, common signal threshold, backup/restore and diagnostics. Remove the duplicate large capabilities card and all option-entry, Paper strategy and Paper risk forms.

If a general trading-mode preference remains here, label what it actually controls. A LIVE/Paper selection may choose which workflow to open; it must not silently arm real orders. Do not offer apparently functional LIVE Auto/Semi-Auto modes when those engines are unavailable. Detailed LIVE strategy settings belong on Live; detailed Paper strategy settings belong on Paper.

Prepared 2.2.0 already removes the capabilities card and moves the Paper and real-order forms out of Settings. The general trading-mode presentation requested by the user still needs a precise, non-duplicated implementation; the existing `mode` control is a Paper/saved-preference control, not a live execution engine.

## Scanner

Retain selected symbol/timeframe analysis, chart, ten filters, filter coverage/counts, and separate higher-timeframe context. Use Broker API mode for strict broker data. Show stale/failed data as historical or WAIT. Keep simulated premium scenarios visibly separate from actual listed option quotes; do not call simulations live option recommendations.

The selected-symbol caption and coverage checks already exist. No new scanner feature was implemented during this report.

## Paper — fifth page, separate strategy state

Keep Paper contract selection, lots, entry/exit, Paper capital/risk, simulated SL/target/trailing, re-entry/averaging/partial-profit controls, practice positions/history and educational strategy previews here.

The user's additional requirement is **Paper execution driven by real broker prices**. This is not complete. Existing Paper entry can copy a fresh verified option quote, but the running strategy and protection demonstrations still require manually supplied marks.

Needed behavior: resolve the Paper position's own exact symbol/expiry/strike/side, use verified master lot size and a timestamped broker quote, and apply simulated strategy/SL/target decisions only on new valid quote updates. Keep Paper selection and ledger independent of the Live form while sharing the authenticated data connection. Missing/stale quotes must pause automatic evaluation and show the reason. Manual-price practice can remain as an explicitly selected fallback. No Paper action may call a live order endpoint.

## Outstanding work before the requested layout is complete

1. Compact Home status plus a genuine broker-position summary; clarify data LIVE versus trading permission.
2. Complete the requested Paper bot connection to real-time broker marks with its own independent contract state.
3. Implement and validate any requested LIVE SL/target/bot automation; moving widgets is insufficient.
4. Finalize the general mode preference and page-specific strategy placement without duplicate or misleading controls.
5. Deploy/check the manual LIVE server addon, verify broker behavior and test the eventual authorized APK on the phone. These are release checks, not completed by a source-layout audit.

The prepared five-page relocation had 174 passing offline tests before this report. Those tests cover the existing prepared scope; they do not certify the pending real-time Paper engine, LIVE automatic protection or device behavior. No new test run was necessary for this report-only change.
