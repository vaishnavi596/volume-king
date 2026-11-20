# BOT KING Pure Clone — B2 SSK Connector, 2026-11-20

## Current owner direction and scope
- Work **only** on the pure clone branch `pilot/v1-pure-original-clone-phone-20261120`. The previous V2 pilot is dropped from the implementation path. Preserve original V1 production and the previously installed clone.
- The owner wants B2 first: simple Server Access Key (SSK) user experience, a **new clone-specific** Oracle pipeline, then B3–B6 and one APK before upgrading Super Five/timeframes/refresh. Do not borrow the old V2 pilot routes/data or silently substitute legacy V1 endpoints.
- The original six tabs, existing preferences, PAPER and preexisting Refresh/Scanner/Super Five are **not** changed as part of B2.

## Actual B2 source changes on pure clone branch
1. `src/clone_v2_gateway.py` added, commit `d20ff9bc3df45fe7bc8bc8d0cc6356877b10bafe`. New standalone key-based HTTPS read-only status handshake on **`GET /clone-v2/status`**. Uses original clone's hardened URL/key/TLS functions, sends `X-BotKing-Key` with no secrets stored in preferences. Requires explicit JSON protocol `botking-clone-v2`, `authenticated=true`, `read_only=true`, `live_orders_enabled=false`, `pipeline=dhan-oracle-clone`, `status=ready`. No legacy fallback. HTTP 404/401/403/429 fails closed, never calls market data and never claims LIVE.
2. `src/main.py` modified only to add clone-only connection object, new `Check Clone V2 Gateway (SSK)` Settings button, asynchronous probe and readable result, memory-only key disposal and local disconnect. Commit `055854eaa334f19b9a4b9a3b3ee0172bba1359b6`. Unchanged 6-tab navbar, old market transport, SUPER FIVE, all timeframe/candle paths and 429 logic. New B2 control does not overwrite the old V1 Connect/Check; that remains untouched until actual new data service and user phone proof.
3. `tests/test_clone_v2_gateway_b2.py` added, commit `5f4afbd39e17a7ec236d611c296c9505717d406c`; offline test cases for new-only URL, successful read-only status, 404 no fallback, 401/403/429 no auth, invalid protocol/permissions/rejected fake LIVE. **Test file committed, not yet executed by GitHub CI or an actual Android run.** No CI/APK triggered here.

## Required server contract, no fake readiness
New server operator-owned Clone V2 service must independently expose the authorized `GET /clone-v2/status` under the trusted HTTPS origin with SSK verification before this button can PASS. This route **does not currently exist or have verified deployment** on Oracle. Existing V1 `/dhan/*` and previous V2 `/v2-pilot/*` are explicitly not accepted as B2 Clone V2 status. The successful GitHub Audit #9 verified SSH and V1 health, not a deployed clone V2 gateway.

## Open B2 completion gates (must not claim complete)
- [x] Pure clone SSK gateway probe module and fail-closed protocol contract present in source.
- [x] Existing Settings UI can request isolated clone gateway check without changing market feed.
- [x] Offline regression test code added to clone.
- [ ] Execute focused offline tests and syntax check for touched files (no result yet recorded).
- [ ] Implement and review authenticated read-only **clone server** status plus new quote/index read routes, with budget and source evidence. Needs separate owner-approved Oracle deployment and private key provisioning; never post secrets in GitHub.
- [ ] Link authenticated new quote/index provider to the clone's canonical read-only market-feed boundary and ensure old provider polling is off **for new mode**, preserving all six pages.
- [ ] Confirm actual Oracle route 200 authorized / 403 invalid key, correct Dhan data source, signed TLS, and phone test.
- [ ] B2 completion requires real new pipeline phone acceptance. An HTTP status-only handshaking client is not an operational market-data pipeline.

## Hard constraints
No V1 server changes; no prior V2 pilot code/data; no key values committed or printed. No feature-refactor, LIVE label, APK, test PASS or server activation claimed without actual evidence. New client-only B2 groundwork is **PARTIAL**, B2 full production integration **OPEN**.
