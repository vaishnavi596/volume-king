# BOT KING V3 — Yahoo / Angel One deep active-path quarantine audit

Date: 2026-11-22. Target branch `pilot/v1-pure-original-clone-phone-20261120`. Scope: V3 Android runtime, Dhan Clone adapter, app background source guards, data and option UI, known legacy shared files. Reviewed GitHub source, not an installed APK or an Oracle deployment. No Dhan/Angel/Yahoo HTTP request, no orders, no V1/Oracle write in this audit.

## Confirmed active V3 surface before cleanup
- `src/main.py` had eagerly instantiated `ServerAngelFeed()` from `src/server_feed.py`, which imports real `AngelFeed` from `src/market_feed.py`. The latter contains actual Angel One endpoints. An unused/reachable definition is not proof that it had sent a request, but retaining its live object added an avoidable accidental invocation surface.
- `src/main.py` retained a **22K+ byte unreachable Angel connection callback** after an unconditional disabled `return`, old Angel credential form labels, and an unreachable legacy option historical premium fetch. Dhan-only source selection normally made them inactive, but leaving them obscured audits and invited brittle callback tests.
- `src/main.py:fetch_market_data_uncached` had unreachable `Yahoo Finance` and `Broker API` conditions after the Dhan-only hard guard. A historical `symbols_yahoo` map was unreferenced. Several background/source guards accepted strings `Yahoo Finance` and `Broker API` alongside Dhan even though current preferences are coerced to Dhan.
- Old cache labels and translations mention Angel/Yahoo; **text presence alone is not evidence of network calls**. Existing Dhan display caches enforce source matching.

## Applied removal/isolation in V3 only
1. New `src/v3_disabled_legacy_broker.py` supplies `V3DisabledLegacyBroker` with `connected=False`, no external HTTP imports or network-capable operations; old dynamic method calls fail closed with a non-sensitive error and no fabricated result.
2. `src/main.py` instantiates that quarantine instead of `ServerAngelFeed`; eliminates V3 import and eager construction of real Angel server transport. Replaced old 22KB login path with a disabled explanatory callback; eliminated Angel credential selection fields and Angel historical option premium fetch. Dhan-only option chain and paper data remain.
3. Deleted unused Yahoo map and removed unreachable Yahoo/Angel alternative history transport branches in the V3 market-data acquisition code. Enforced `prefs.source == Dhan` in background source selection checks, including early/late scans.
4. Added `tests/test_v3_legacy_provider_quarantine.py` to confirm the disabled broker never makes an HTTP request even when old methods are manually invoked, old callbacks cannot access Angel, and new guards are Dhan-only.
5. Updated *outdated static* B1 market status test to inspect the **active** Dhan quote status rather than a now-deleted unreachable login callback. Preserved the explicit disabled Angel login notification expected by existing `test_market_feed.py`.

## Files deliberately retained for compatibility (NOT active V3 Angel/Yahoo fetch)
- `src/server_feed.py` and `src/market_feed.py` contain old Angel class declarations because `ServerDhanReadOnly`, `FeedError`, `SessionExpired`, and server-origin helpers are shared with legacy tests. Their mere presence or import does not send requests. Removing them globally without extracting shared Dhan contracts would risk V1 and offline test consumers.
- `backend/server.py` and `backend/provider_router.py` are separate legacy V1/server facilities. **Never rewrite/delete V1 production backend based on V3 Android cleanup.**
- `src/i18n.py` legacy strings and archived source labels are not network endpoints. They can be cleaned in a separate presentation-only pass after confirmed UI impact, but do not prove interfering network traffic.
- `get_yahoo` in V3 is a safe fail-closed stub with no Yahoo fetch; retained by compatibility interfaces.
- **No evidence collected here proves Yahoo/Angel caused historical Dhan 429, repeated NIFTY 863 volume, or the five-engine WAIT.** Those retain their independently established root-cause gaps.

## Verification and release conditions
- B1/B2/Adapter audits recovered after stale-contract tests were reconciled. Final No-APK full regression, run [44977916921](https://github.com/vaishnavi596/volume-king/actions/runs/44977916921) was initiated after the last source+test cleanup; its final result must be checked before declaring PASS.
- This validates source and mocked offline behavior, not app binary or live network isolation. Existing B198 APK **does not contain** these changes; Oracle gateway not deployed; no physical Android network trace captured.
- Do not rebuild V3 until permanent signing, app data migration and verified release gates are configured. V1/Oracle unchanged.
