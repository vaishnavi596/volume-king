# BOT KING — Mandatory last-eight CI/build preflight and error-loop reconciliation
Date 2026-11-16 IST. **Apply BEFORE every new batch of GitHub edits**; update after each commit/test/run.
This preflight accompanies, never replaces, `docs/BOT_KING_WORK_LOG.md` and `BOT_KING_HANDOFF.md`.

## Permanent working rule from owner
1. **Read last 7–8 relevant Actions runs**, newest first, on the SAME integration branch, including both Offline Regression Tests and Build APK. Read run/job outcome and the **failed step**; if failed obtain the exact job log, test method, assertion, exception and file/line. Never count a check as PASS simply because it was previously green on another commit.
2. Group failures by **distinct root cause**, not by number of red runs, test cases, candles or time elapsed. Record exact counts: runs inspected / failed; distinct failing test names; exact test assertions; total tests executed; grouped true code fault vs stale test expectation vs external/CI environment. If the cause is not proven, label UNKNOWN.
3. Before adding a new feature, **repair prior failing assertions** in the minimum joint code/test batch. Keep tests meaningful: a change in source expectations must be paired with safeguards that ensure no provider fanout, no invalid LIVE promotion, no cross-source history and no unsafe bypass.
4. Prefer one code patch plus targeted regression, then full offline suite, inspect newest red job logs again, *then* signed APK candidate. Only the latest complete job after all fixes can prove a clean regression. Do not trigger expensive APK on known-red branch.
5. Every command has an output contract: command, intended check, as-of timestamp/run, actual result and action. Batch 2–4 safe Oracle commands where applicable; never repeat proven nginx/TLS/socket/quote-gate stage commands without changed state. Keep Oracle source/stage/production and APK/mobile evidence separate.
6. After every source edit, test repair, CI lookup, Oracle smoke and deployment decision, append in category **TEST/CI**, **APP**, **ORACLE STAGING/PRODUCTION**, **APK**, **MOBILE** to the journal, with commit SHA + run/job IDs + precise PASS/FAIL/UNKNOWN.
7. Inspect **latest branch head** before each edit and ensure no newer red run appeared after the inspected sample; if it did, consume its failure before building anything else.

## User-provided and connector-verified red-run matrix (2026-11-16)
All six linked Actions runs were inspected using exact `fetch_workflow_run_jobs` + complete `fetch_workflow_job_logs`. These results are actual CI/job evidence:
| Run | Workflow | Job ID | Tests executed | Failures | Failing tests |
|---|---|---:|---:|---:|---|
| [#1536](https://github.com/vaishnavi596/volume-king/actions/runs/43809761171) | Offline | 133108551236 | 880 | 2 | JointSessionRepairTests closed market; MobileRegressionTests cached ranking |
| [#1537](https://github.com/vaishnavi596/volume-king/actions/runs/43809786139) | Offline | 133108630252 | 883 | 2 | same two |
| [Build #643](https://github.com/vaishnavi596/volume-king/actions/runs/43809908339) | Build APK | 133109037952 | 883 | 2 | same two; **offline regression step 16** failed; signing/package not reached |
| [#1538](https://github.com/vaishnavi596/volume-king/actions/runs/43812559883) | Offline | 133117255296 | 883 | 2 | same two |
| [#1539](https://github.com/vaishnavi596/volume-king/actions/runs/43812586100) | Offline | 133117335180 | 883 | 4 | same two + mobile 10s timer + watch incremental 10s timer |
| [#1540](https://github.com/vaishnavi596/volume-king/actions/runs/43812627770) | Offline | 133117469807 | 887 | 4 | same four |

**Four failing test names (not four distinct provider errors):**
- `tests/test_joint_bootstrap_options_127.py::test_closed_market_cached_top_five_requires_no_provider_call` asserted the local Super Five block must contain `dhan_feed.connected`. New source intentionally reads stored Dhan 5m candles as `HIST` when offline; no provider endpoint is called.
- `tests/test_mobile_regressions.py::test_super_five_cached_ranking_never_triggers_history_fetch` asserted direct `snapshot=quotes.get(sym) or {}`; new code reuses `shared_history(sym)` (with valid 30+ bars) to avoid losing signals when quote snapshot is partial.
- `tests/test_mobile_regressions.py::test_super_five_uses_independent_minute_cached_refresh` asserted hardcoded `await asyncio.sleep(10)`; local-only Super Five observation was changed to `SUPER_FIVE_LOCAL_TICK_SECONDS=2`.
- `tests/test_watch_countdown_incremental.py::test_super_five_reuses_cache_and_skips_unmodified_candles` asserted same hardcoded 10s; new 2s LOCAL check does **not** make any extra market API calls.

## Repair record (source committed, CI result still pending)
- [51321c92](https://github.com/vaishnavi596/volume-king/commit/51321c928d15efc22b53a5140b2a5e463d8b44ce): joint bootstrap regression now requires validated shared history and permits disconnected HIST display while still forbidding provider calls.
- [c08b7791](https://github.com/vaishnavi596/volume-king/commit/c08b77917d7077640e46c63cba69448eb583d4d2): mobile regression updated for shared-history and 2s local observation, continues asserting no network history call.
- [5ca1e8f0](https://github.com/vaishnavi596/volume-king/commit/5ca1e8f05659fa713eaa91174b20e626922c1510): watch incremental regression expects local 2s observation with shared cache and no quote provider call.

**Do not mark fixed until new full Offline Regression Tests run concludes PASS for SHA at or after 5ca1e8f0.** Previous failures identify incompatible assertions, not Android phone runtime proof. If the next job fails for a new reason, append it before any new features.

## Minimal test/run sequence
1. `python -m unittest tests.test_joint_bootstrap_options_127 tests.test_mobile_regressions tests.test_watch_countdown_incremental tests.test_mobile_feed_history_continuity_128 tests.test_four_lane_refresh_policy -v` (targeted, repo checked out, no Dhan).
2. `python -m unittest discover -s tests -v` (all offline; quote gate and UI integration).
3. Inspect newest GitHub job id/log and summarise exact number of PASS/FAIL, then only on clean branch consider signed APK release. Old #643 cannot produce 2.3.128 APK without a successful new build.
4. Oracle backend remains untouched in this batch; no reason to repeat previously passed nginx/443/8000/staging fake quotes.

**Note:** latest-eight requirement is a working preflight; only the six runs explicitly provided were available to this audit so far. The next preflight must collect the next two chronological runs or latest two available before declaring an eight-run pass, rather than fabricating them.
