# BOT KING G1 — active-path inventory (2026-11-12)

Status: **IN PROGRESS**. Evidence from GitHub branch `botking-snapshot-token-compat-20261112`. This is a code inventory, **not** a physical-device or production deployment pass. Master gate: issue #12.

| Surface | Active code / behavior | Centralization concern | Next verification |
| --- | --- | --- | --- |
| Android UI | `src/main.py` Flet UI and provider preferences | Three provider choices, Yahoo chart calls and Angel sessions still exist | Map each user-visible path and decide migration/feature gate |
| Dhan read-only | `src/server_feed.py` | Watchlist batch now reads `/v2/snapshot` on candidate branch; other LTP/index/candle paths still call server endpoints | Confirm all active paths and freshness labels |
| Oracle snapshots | `src/oracle_226_client.py`, `backend/server.py` | Pairing-key auth remains transitional; device Bearer path not production mounted | Verify server deployment and auth integration |
| Alternate providers | `src/market_feed.py`, `backend/provider_router.py` | Angel client and Yahoo paths still present; provider router can select fallback when explicitly called | Never silently relabel or combine Yahoo/Angel with Dhan |
| Local state | `src/preference_store.py`, `src/snapshot_store.py` | Preferences written to JSON and Flet client storage; must never hold pairing key, Dhan token or PIN | Audit every persisted field, restart and upgrade behavior |
| PIN/biometric | `src/android_device_auth_226.py`, `src/oracle_device_login_226.py`, `src/secure_credentials.py` | Native bridge missing and not wired into main app | Implement/test actual Android Keystore/OS authentication before claiming PIN unlock |
| Device API | `backend/device_auth_api_226.py` | Optional router intentionally not mounted; enrollment and abuse protections incomplete | Security review and owner-approved enrollment |
| CI | `.github/workflows/test-only.yml`, `.github/workflows/build.yml` | 411 offline tests passed on eb1a8f56; no APK/device verification | Add centralization contract tests, verify APK signature and installed package |

## G1 findings / defects
1. **G1-01:** Source-of-truth not yet unified: main UI has Yahoo Finance and Broker API options and direct provider logic. This is not proof of unwanted runtime fallback; trace before removal.
2. **G1-02:** `backend/provider_router.py` permits a verified alternative provider as fallback. For the intended Oracle+Dhan-only release, fallback policy must be explicit, never silent.
3. **G1-03:** PIN login is a planned feature, not implemented. Do not expose a cosmetic PIN screen or enable device-auth endpoints prematurely.
4. **G1-04:** `src/preference_store.py` writes local JSON. Verify persisted schema contains no secrets; do not mistake it for secure storage.
5. **G1-05:** Oracle snapshot freshness is `unverified`; it must not be displayed as exchange-confirmed live.
6. **G1-06:** `src/oracle_226_client.py` is a transitional client; the main Watchlist currently uses `ServerDhanReadOnly` and the new snapshot endpoint, while other UI flows require inspection.

## Acceptance
Complete function-by-function map of `src/main.py` network calls, UI pages and persistence; identify safe removal/isolation candidates; add regression tests for source isolation and auth safety. **No deletion, Oracle deployment, or APK release as part of G1.**
