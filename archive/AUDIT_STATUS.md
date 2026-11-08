# BOT KING repository and Dhan audit — 2026-11-08

## Scope and limitations

This is a **partial, evidence-based audit**, not a clean bill of health. The full recursive repository tree, Android runtime, Oracle service state and live Dhan responses have **not** been verified. Do not archive files based on age or name alone.

## Verified active paths

- `pyproject.toml`: Flet entry point `src/main.py`, project version `2.3.56`.
- `src/main.py`: imports `market_feed`, `server_feed`, `scanner_engine`, `snapshot_store`, `preference_store`, `storage_paths`, `analysis_quality`, `chart_indicators`, `paper_engine`, `feed_health`, `i18n`, `help_content`.
- `src/server_feed.py`: Dhan read-only client, HTTPS pairing-key transport; `connected` means origin and key held in memory, not proven ongoing feed health.
- `backend/server.py`: Dhan status, quote, batch quote, intraday endpoints.
- `backend/dhan_feed.py`: upstream Dhan adapter.
- `.github/workflows/build.yml`: version guard, offline tests, pinned signing verification, APK build. Build workflow can trigger on changes to `pyproject.toml` or workflow itself; do not change these during audit without intent to build.

## Findings

1. `src/main.py` restores cached market data and source-matched historical rankings on startup. While Dhan is disconnected, restored Super Five directional rankings are now hidden by commit `3d570e7d5a6b4b50ae7f5d53be8e34029644230f`. Regression test is pending.
2. `src/preference_store.py` can restore preferences from local disk or native client storage. The origin of settings seen after an uninstall is unproven; Android backup/restore settings and packaged defaults need inspection.
3. `src/server_feed.py` sets Dhan quote timestamps to `None` and freshness to `unverified`; successful connectivity does not prove exchange freshness.
4. `backend/server.py` Dhan status reports `market_data_configured` based on client ID and a nonempty token file. Actual quote and candle endpoints must be checked separately; token presence is not proof of validity.
5. The existing `backend/DHAN_INTEGRATION_AUDIT.md` contains historical draft-branch blockers. Some statements are obsolete (current Android source includes Dhan). Reconcile it with current code before relying on it for deployment.
6. `backend/server.py` and Android Dhan client agree on `/dhan/status`, `/dhan/ltp`, `/dhan/ltp-batch`, `/dhan/intraday` paths. This is a static code check, not a network integration test.

## Safe retirement gate

For each candidate file, record: original path, purpose, all static/dynamic imports, workflow and deployment references, test references, replacement, rollback instructions and test evidence. Move only verified unused files to `archive/retired/`. Ensure packaging and deployment exclude archive content. **No candidate is approved for retirement yet.**

## Release gates before APK

- Complete recursive repository inventory and reference graph.
- Confirm backend import/deployment parity with Oracle and verify Dhan status, LTP, batch, intraday using sanitized diagnostics.
- Add offline regression for disconnected Super Five and cold-start cache behavior.
- Verify historical candles and scanner counts for the mapped 51 equities; no false live claims.
- Run tests and inspect workflow result, signing identity, package ID and monotonic build number.

**APK build not authorized by this report.**

## 2026-11-08 verified follow-up

- Recursive GitHub tree retrieval was complete (not truncated); this supersedes the older tree-unverified note above.
- Backend CI run #38: SUCCESS: https://github.com/vaishnavi596/volume-king/actions/runs/42487944824
- Backend CI run #39: SUCCESS: https://github.com/vaishnavi596/volume-king/actions/runs/42488104908
- Dhan interactive consent tokens now feed market-data endpoints after strict offset-aware expiry validation; mocked tests pass. Provisioned token fallback remains. The older token-file-only finding above is superseded.
- Legacy new-version/bot_app.py was archived as archive/retired/bot_app_legacy_gateway.py.txt before original removal. Other candidates remain unapproved.
- Oracle read-only audit script was added but has NOT been run on Oracle. Real Dhan entitlement, fresh quotes, candles and Android runtime remain unverified.
- No APK was built; maintain signing and version continuity until runtime validation.
