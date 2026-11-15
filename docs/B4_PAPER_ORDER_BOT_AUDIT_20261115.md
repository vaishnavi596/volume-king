# BOT KING — Paper Order / Paper Bot / Live-Readiness Audit
Date: 2026-11-15
Scope: GitHub `fix/botking-b3-option422-scope-20261115` app source. **Read-only static/code audit plus offline regression**, no phone/device or Oracle order execution.

## Current architecture and audit finding
The app has **three distinct** paper interfaces; they are not one synchronized execution ledger.

1. **Chart/Dashboard paper positions**: `src/main.py` near `chart_paper_trade`, `exit_paper`, `dashboard_positions`. Expects recent `quote_timestamp` (<=90s) and current-provider source. Dhan LTP adapter currently returns `quote_timestamp=None`, so this path often blocks entry and its P&L is unavailable. Positions are stored under `paper_positions`, history under `paper_history`.
2. **Quick Paper BUY/SELL**: `paper_trade` uses a recent quote, keeps `paper_position` only in memory; does not use the bot's persisted `bot_position` or unified journal. It is not an executable broker order.
3. **Paper Bot**: `bot_paper_action` supports BUY/SELL/EXIT from **manually entered** premium/share price and manually confirmed contract, with `paper_engine.py` deterministic stop/target/trailing/partial/add decisions on `paper_tick` manual mark. Position saved in `bot_position`, event/journal in `bot_paper_events` and `paper_journal`. Bot loop is deliberately NOT continuously live; on restart the bot is stopped.

The **Options page** `option_paper_action` currently rejects CE/PE paper orders because verified premium, listed strike and lot size are not all supplied. Broker-listed Dhan option chain being visible does not automatically authorize this action.

## Code evidence and current gaps (priority)
| Priority | Issue / observation | Required production-grade change |
| --- | --- | --- |
| P0 | No end-to-end measured 1s/2s/3s Dhan quote-to-signal-to-order-to-ack path; pure local compute speed is irrelevant to external order SLA | Instrument separate quote timestamp, transport, decision, risk check, enqueue, broker ACK, fill, persistence p50/p95/p99; test with simulation and failure injection, no live submit |
| P0 | Manual mark drives Paper Bot. Running `paper_run` does NOT subscribe to Dhan marks or process ticks automatically | Build single serialized, source-validated paper market-event ingress; Dhan refresh pace and exchange timestamp/freshness controls; freeze on missing/stale data |
| P0 | Quick-paper `paper_position`, chart `paper_positions` and bot `bot_position` are separate ledgers | One portfolio/order state machine, unique client/order IDs, atomic event journal, restart reconciliation and duplicate suppression |
| P0 | `paper_trade` is ephemeral; `chart_paper_trade` requires quote_timestamp not available from Dhan LTP; marking/exit may be unavailable | Align paper entry and marks to a single evidence contract, explicit simulated manual-price override; distinguish unavailable vs stale vs live verified |
| P0 | `exit_paper` removes chart position before durable persistence success, with no rollback; paper-bot updates position before testing `save()` | Crash-safe transactional journal, fsync/ack, rollback/reconcile on failure; never report a confirmed exit until saved |
| P0 | Code only enforces paper-mode local guard. No safe real order gateway, authenticated broker order API, two-phase risk validation or exchange order reconciliation | Implement separate server execution service in future, default disabled, scoped auth, risk checks, limits, expiry and entitlement validation, idempotency, reconciliation, kill switch and paper/live isolation |
| P1 | Paper Bot options expiry can be a **calendar preview**, and lot size/strike/entry premium are user-supplied | Paper-only label retained; future live orders must use broker-listed contract master + lot size + expiry + permitted product |
| P1 | Paper `PARTIAL` books a journal P&L, but full cumulative realized profit and open risk are not reconciled in one unified ledger | Test cumulative partial/full P&L, fees, repeated partials, risk released on partial and no double count |
| P1 | Risk checks apply to initial bot entries/ADD, including notional and stop risk, but `Stop new actions` does not close open positions, emergency stop blocks new entries, and auto-protection uses manual marks | Separate *halt new orders*, *cancel pending*, and *flatten position* controls; define disconnect/crash/timeout behavior |
| P1 | Assisted timeout `protection_clock` checks once per second but acts only on a prior manual mark <=60s; not a real-time market-data guarantee | Measure actual timer scheduling delay and state freshness; no claims of 1s broker action |
| P1 | Paper stops are threshold checks on discrete manual marks, not guaranteed fills. Price gaps, slippage and charges are not generally incorporated in every path | Simulated fill model and slippage/fees/taxes, partial fills, rejected orders, gaps, buy/sell consistency |
| P2 | Periodic preference save includes disk fsync plus native bridge, may block callback or fail | Track save latency, failure-injection tests, display durable vs in-memory state |
| P2 | `paper_engine.py` computes levels, P&L, stop, target, trailing, partial and averages locally; deterministic unittest coverage exists | Extend state-machine tests and replay multi-session sequences on a fake clock |

## Current auditable assertions
- `src/paper_engine.py` is CPU-only and has no order/network APIs.
- Dhan live orders remain disabled in Oracle/readiness; S09 read-only audit earlier reported 27/27 PASS. This does not prove a live gateway.
- Existing `tests/test_paper_engine.py` covers cash SELL exit with charges, stop/target/partial/trailing, emergency blocking additions, paper restart stopped, and re-entry cooldown.
- New `tests/test_b4_paper_execution_audit.py` adds pure compute and risk checks, with a CPU-only microbenchmark. **CPU benchmark must not be called API/network/mobile response latency.**
- Full GitHub offline CI is evidence for Python behavior in runner, not Android device performance or Dhan broker timings.

## Performance test protocol (required before future live-readiness)
Run with synthetic/fake broker first. Instrument monotonic timestamps for app input, market event received, quote freshness, risk evaluation, ledger append, UI confirmation, server ingress and broker mock acknowledgement. Report count, success/error, p50/p95/p99 and max for at least 100 representative events across healthy, slow, duplicate, stale, disconnected and restart modes. Then independently measure read-only Dhan quotes with allowed rate limits. Do not introduce broker execution or make real orders during this audit.

## Recommended next batch
**B4-A** unified paper order/position ledger, persistent state and idempotent BUY/SELL/EXIT + fees. **B4-B** manual vs Dhan-backed paper pricing and freshness with cross-screen consistent status. **B4-C** continuous *paper-only* risk/profit/stop simulation with bounded serialized tick ingress, explicit session/offline behavior. **B4-D** deterministic replay and latency benchmarks, scenario matrix and device smoke. **B4-E (future, separate authorization)** live gateway design/security review, never auto-enable.
