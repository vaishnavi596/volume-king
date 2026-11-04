# BOT KING: 2.0.2 preservation and next-release recheck

This records the earlier recheck. See [the final source audit](final-audit-v2.1.0.md) for the later selected-symbol improvements, current test count and release gates.

Date: 2026-11-04. This is a source/offline review, not a claim of device or real-order certification. No APK was built and no production server was changed for this review.

## Version scope

- 2.0.2 baseline: local commit `5734209`, published equivalent `5b25df10d9aec74709d6e3ad167c15876191ed6f`.
- 2.0.3 corrections: local commit `817536c`, published equivalent `2e96e5cf5db157976da7c79f5242dd9c952f6eef`.
- Next release is prepared as **2.1.0**, because it adds a separate real-order path. It includes the 2.0.3 corrections and retains the 2.0.2 functionality.
- Compare all baseline source files and functions, then run existing and new regression tests. No baseline main.py function was removed. This structural check supplements tests; it does not prove every device behavior.

## Preserved functions

| Area | Evidence and scope |
| --- | --- |
| Home, Options, Settings, Scanner | Existing navigation/control-uniqueness tests; all four pages remain |
| 50-stock selectors and custom symbols | Existing picker/search/restart tests retained |
| Chart provider, intervals, EMA, chart-state persistence | Existing chart tests retained; Android WebView rendering still needs device validation |
| Angel One login, server connection, Yahoo fallback | Existing gateway/session/authentication/provider tests retained |
| Option chain, expiry, lot sizes, OI/PCR/volume | Listed-contract mapping and missing/stale/partial data tests retained |
| Paper BUY/SELL/EXIT, risk limits, manual tick strategies | Existing paper-engine tests retained; no Paper button invokes a live-order endpoint |
| Settings, backups, restart cache, English/Hindi | Existing persistence, backup and language tests retained |
| Scanner filters, Super Five, news and combined status | Existing analysis tests retained; modeled premiums remain labeled simulation |

`analysis_quality.py`, `feed_health.py`, `help_content.py`, `i18n.py`, `market_feed.py`, `paper_engine.py`, `preference_store.py`, `scanner_engine.py`, `snapshot_store.py`, and `storage_paths.py` are unchanged from 2.0.2.

## Earlier screenshot audit: 19 items

| # | Finding | Current source status |
| --- | --- | --- |
| 1 | Incompatible signing keys | Mandatory permanent signing and certificate pin checks prepared; actual key setup remains blocked |
| 2 | Long labels overlap | Long labels moved above fields with wrapping |
| 3 | Lots field too narrow | 2.0.3 width correction retained |
| 4 | Help icons remain for hidden fields | Help wrappers follow field visibility |
| 5 | Option chart incorrectly blames Yahoo | 2.0.3 loading/error/selection-state correction retained |
| 6 | OI/volume formatting | Readable grouped numbers retained |
| 7 | Misleading initial broker status | Correct reconnect/login instructions |
| 8 | Invalid server address saved | HTTPS-origin validation before saving and connecting |
| 9 | Broker expiry label survives preview changes | Provenance reset when selection/provider changes |
| 10 | Old failed fetch overwrites new selection | Generation/context checks before publishing errors |
| 11 | Old option quotes marked available | Complete but old quotes marked STALE |
| 12 | Broken negation regex in news | Correct word-boundary matching; negated/uncertain examples cannot vote |
| 13 | Options Paper buttons always blocked | Current listed quote can populate a Paper entry; stale quote blocked |
| 14 | Manual Paper form disconnected from quoted lot/premium | Options entry copies exact strike, side, expiry, master lot size and current premium |
| 15 | Scanner premium candidates are simulated | Still a feature gap; no claim of real tradable ranking |
| 16 | Only EMA chart overlays | Still a feature gap |
| 17 | Drawing tools absent | Still a feature gap |
| 18 | No validated option trade-flow direction for combined signal | Still a feature gap; OI/volume alone do not become a directional vote |
| 19 | Live orders and automatic protection absent | Manual confirmed LIMIT-order path prepared and fake-broker tested; deployment/device/real-broker validation and automatic protection remain outstanding |

## Additional problems fixed during this recheck

1. A blocked new Options Paper entry could overwrite the existing Paper plan inputs. Position checks and copying now run under the same lock.
2. An in-flight arm response could restore an obsolete UI arm after background/reset. Generation checks discard it and attempt disarming the same session.
3. Editing a live form while its preview was loading could open a confirmation for an older selection. Changed forms invalidate the pending preview.
4. Switching the live form to Cash hid option inputs but left their help wrappers. Wrappers now follow the segment.
5. Some captions/help still claimed that all live orders were disabled. They now distinguish Paper controls from separately confirmed manual LIVE controls.

## Validation

- Baseline had 117 offline tests. They remain in the suite.
- Current recheck suite: **153 tests**, including stale quotes, live-arm/preview confirmation, durable duplicate-submit handling, concurrent duplicate confirmations, uncertain responses, order-book failure, Paper quote entry and page/state preservation.
- Python syntax compatibility checked for app Python 3.11 and gateway Python 3.9 grammar; installer checked with `bash -n`; `git diff --check` checked.
- Previous review commit `e108c3a2ce2f28e9633f9583d761502fb2901789` passed its 145-test GitHub job. This report's later changes require the new CI run; do not confuse the two revisions.
- No real order was submitted. Fake-broker tests cannot certify exchange acceptance, actual fills, broker-side stop orders or phone background behavior.

## Release blockers and remaining work

1. **Permanent signing setup:** GitHub preflight reports `SIGNING_NOT_CONFIGURED`; both `ANDROID_KEYSTORE_BASE64` and `ANDROID_KEYSTORE_PASSWORD` are absent. Generate/retain one private key, store these secrets, and pin its public certificate in `config/android-signing.sha256`. Never publish a replacement debug key or commit a private key. This is intentionally required before an APK release.
2. **Gateway deployment:** existing server stays unchanged. Deploy the reviewed live addon only when moving to the release/testing phase; verify broker permissions, session behavior and server access. A UI toggle alone does not enable server orders.
3. **Device and market-session checks:** after build, validate startup, chart rendering, broker login, exact contract/lot/premium, order review, acknowledgement versus fills, positions and cancellation. Install a subsequent higher-version APK with the same certificate to verify an in-place update. These checks have not been performed for 2.1.0.

Further feature work remains: live SL/target/trailing and unattended protection; actual quoted scanner candidates; additional overlays/drawing; validated three-source analysis; integrations for brokers other than Angel One. New LIVE controls also need fuller Hindi help/status coverage. These are not implemented by relabeling Paper features as live.

Manual LIVE scope currently prepared: INTRADAY LIMIT orders only, explicit arm and per-order confirmation, server risk caps, exact master contracts, fresh quote checks, durable request IDs, reconciliation, long-position SELL checks and cancellation. There is no automatic SL/target, AMO, automatic re-entry or always-on protection.
