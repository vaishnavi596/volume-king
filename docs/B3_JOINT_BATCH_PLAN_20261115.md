# BOT KING — GitHub Joint Batch Plan (15 Nov 2026)

Source of truth: `fix/botking-b3-option422-scope-20261115`, based on the existing B3 audit branch at `5f7573d`. The running Oracle backend is a separate deployment. **Never assume GitHub backend files are identical to production Oracle.**

| Batch | Scope | Files | Status / gate |
| --- | --- | --- | --- |
| B3-A | Dhan option 422 keyed retry suppression (5 min), distinct endpoint/underlying/expiry, bounded entries | `src/server_feed.py`, `tests/test_b3_option_422_negative_cache.py`, `.github/workflows/test-only.yml` | Committed; regression run #43730761831 PASS |
| B3-B | Ten movable scanner filters; remove returns filter to available pool; save/restored choices | `src/main.py`, `tests/test_central_filter_slots.py` | Committed; full regression gate pending |
| B3-C | Read-only `/v2/assessment/{symbol}` and `/v2/server-readiness` adapter; rejects unsafe signals/orders | `src/server_feed.py`, `tests/test_b3_shared_assessment_readonly.py` | Committed; full regression gate pending |
| B3-D | Wire guarded assessment display to Scanner / Watchlist / Super Five; symbol/timeframe isolation, cached/unknown status, five-engine consistency; 422 error diagnostics | `src/main.py`, `src/five_engine.py` (only if needed), `tests/test_b1_five_engine_dhan_shared_option.py`, new UI tests | Pending; do not fabricate 0–100 evidence |
| B3-E | Audit version name + Android versionCode, consolidated tests, release APK and phone tests | `pyproject.toml`, `.github/workflows/build.yml` (only if needed), release tests | Pending; APK build only after B3-D regression success |

## Compatibility and release guards
- Dhan-only runtime; no silent Yahoo or Angel fallback.
- Oracle S09 read-only audit passed 27/27, with real Futures, Options and Candle to Assessment HTTP tested separately.
- Oracle `/v2/assessment` returns five **filter values** and four **factor statuses**; percentages are intentionally null for unverified data. Android must not invent percentages.
- Current Oracle News is `feed_not_configured`; order gateway is not implemented, `live_orders_enabled=false`. App order submission stays disabled.
- Never overwrite local watchlists with the server's empty five-list initial store; migration, ownership and rollback are separate tasks.
- Show historical/unverified quote and candle states accurately. Use the cache, avoid extra broker calls to render a page.
- Do not label GitHub CI as Android device PASS. Check latest commit and workflow conclusion; after release, validate actual versionCode/versionName and install on device.

## Current status
B3-A CI PASS; B3-B and B3-C source/test commits made; final branch-tip regression still running when this plan was written. No release APK or Oracle deployment is part of these GitHub commits.
