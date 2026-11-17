# BOT KING — Deferred Feature & Data-Law Pipeline (17 Nov 2026)

Status: **PIPELINE ONLY — no implementation, no Oracle deployment, no APK release authorization**.
This file records owner decisions while current GitHub repair/testing continues. Super Five existing rules remain unchanged.

| ID | Future work | Gate before implementation |
| --- | --- | --- |
| P01 | Dhan-based Scalp Filter | Recover the exact earlier shortlisted rule; confirm Dhan data fields, entitlements, timestamp freshness, risk and six-month backtest. Read-only/paper analysis only. |
| P02 | Time-Based Movement / Reversal Filter | Six months of genuine intraday Dhan bars, 5m/15m/30m time-of-day volatility and reversal tests, Europe-open daylight-saving adjustment, chronological out-of-sample validation. No invented probabilities. |
| P03 | BK-DATA-LAW-01 Dhan → Oracle → BOT KING compatibility contract | Audit official provider API rate caps/response fields and entitlements; measure actual Oracle CPU/RAM/disk/network and cache behavior; prove source->server->app mapping, two-mobile shared-cache budgets, cooldown, retention, and fail-closed missing-source indicators. Confirm all limits again at implementation time. |
| P04 | Owner's third future filter idea | **Not yet specified**; add only after owner describes it. |

## Non-negotiable cross-cutting rules

1. One reusable per-symbol filter engine for current watchlist equities and future **global maximum 70 equities across five watchlists**; three indexes NIFTY/BANKNIFTY/SENSEX use index-specific data mappings, never invented equity option entitlement. Do not equate each index with an equity.
2. A filter may consume only verifiable licensed/authorized Dhan or independently verified feed fields. No Yahoo/Angel silent fallback and no fabricated News/Futures/Options/Time/Scalp directional percentages. When missing/unfresh use WAIT or STALE with timestamp.
3. Oracle is the serialized, rate-aware provider gateway and shared cache for both phones; preserve last-good data without claiming it is live; respect Dhan HTTP429 cooling and bounded backfill. Do not infer Oracle instance quotas from provider free-tier maxima.
4. No live orders. Do not change OAuth credentials or production Oracle without backup, operator authorization, staging parity and postflight checks.
5. Before any change inspect ten most recent commits/changed files and recent CI failures. Record exact evidence in `docs/BOT_KING_WORK_LOG.md`; CI PASS, Oracle deployed, live Dhan verified, signed APK and phone test are different milestones.

## Current release gate snapshot (not an APK approval)

- Working branch: `fix/botking-joint-audit-70-15-20261115`; verified HEAD before this documentation write: `b5a2e8c80f2e9caab4de9b1f41e8c0954ece128c`.
- Last ten branch commits and last fifteen branch workflows reviewed on 2026-11-17. Exact latest offline test: [run 44039501498](https://github.com/vaishnavi596/volume-king/actions/runs/44039501498), source SHA `879d71bdabc61c1d32d4a596090557dae4912358`, **SUCCESS**, syntax and full offline suite steps PASS.
- Previous complete five-job Joint Gate #5 [run 44037564321](https://github.com/vaishnavi596/volume-king/actions/runs/44037564321), SHA `72686853146d16974a2c132d1cd75965d03ef1c8`, **5/5 SUCCESS**, before the later T13 after-close one-symbol HIST changes.
- Intermediate T13 offline runs 44039156684, 44039294286, 44039444956 failed; 44039409270 cancelled; corrected run 44039501498 PASS. Historical failures are not erased.
- **NEXT GATES:** run a *new* no-APK five-scope Joint regression on current source, verify production Oracle read-only Dhan/collector routes + rate counts with authorized access, then exact SHA release tests and signed APK/mobile market-hours test. No Oracle SSH or on-device result was obtained in this review. `pyproject.toml` on branch reported v2.3.130. No APK should be claimed ready yet.
