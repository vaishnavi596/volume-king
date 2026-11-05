# 2.3.0: connection/data repair and functional controls

Authorized after the user's 31 phone screenshots and the 26-item audit. This is an update to the same Android package and permanent certificate. No broker credentials are persisted, no real orders are sent during build/test, and no production gateway restart is required for these client changes.

## Included

- Bottom navigation presents Home, Live, Scanner, Paper, Settings. Internal page IDs remain unchanged so saved page/scroll state and callbacks retain their meaning.
- One Broker & API Status card first on every page replaces conflicting Home API/status captions. Broker session, selected-symbol quote time, option-feed status and order permission remain distinct. Connected/disconnected use green/red. Expired arming is not displayed as current permission.
- Connected Settings hides login credentials, server key/address/trust form. Disconnect or a detected expired session restores login. Only the implemented Angel One adapter is selectable; unsupported brokers are no longer presented as working login options.
- Login queues one read-only selected/index, options, account and scanner refresh. It runs outside regular hours on demand, displaying last-session timestamps rather than calling them live. Option expiry errors no longer prevent saving an already fetched underlying quote.
- HTTPS requests queue locally for the single-owner gateway. Only read-only operations retry a busy 429, at most twice. Login, arm, preview, submit, cancel and logout are never automatically replayed. Queued requests detect a changed session epoch.
- Market quote refresh uses one concurrent instrument request; connection refresh is prioritized before the background watchlist cycle. Known adapter errors have fixed, secret-free explanations.
- Old non-Angel-One rankings and analysis snapshots are excluded. Real broker snapshots persist with source attribution.
- Option OI change compares a newer same-contract, same-session snapshot within one hour. It is labelled snapshot change, not daily OI change or evidence of buying/writing. Existing selected-window PCR remains explicitly up to nine strikes, not full-chain PCR.
- Candle direction is displayed independently from the conservative three-source agreement check. Missing validated options direction is never invented to satisfy that check.
- Paper offers a fresh broker-price mark button and optional 15-second API polling when the practice engine runs, the app is open and regular session hours apply. Cash uses broker history's actual quote. Options require the exact contract in the loaded window, matching lot size and timestamp at most 90 seconds old. Epoch/position/contract changes discard in-flight results. No real order endpoint is used. Background disables API practice polling; restart defaults it off.
- Unimplemented OI/Max Pain analysis filters, educational strategy-name-only buttons, inert scheduled square-off and preference-only Auto/Semi-Auto practice modes are removed from selectable/visible controls. Existing manual practice engine, risk limits, partial/trailing/re-entry, journal and backups remain. Legacy backup modes migrate to Paper without activating execution.
- Lifecycle events accept state or data; unknown events do not incorrectly pause the foreground app. Added Hindi labels cover the new connection/practice controls.

## Deliberate limits, not completed features

This release does not implement live automatic SL/target/trailing, unattended bot protection, order modification, Dhan/Zerodha adapters, full-chain PCR/Max Pain, validated options buy/sell flow, Greeks/depth-based premium suitability, trained AI probability or a dedicated News API. These are not exposed as working trade controls. Existing live manual confirmed INTRADAY LIMIT orders, cancellation and long-position closing guards remain unchanged. Funds are checked by the gateway at preview; a live balance dashboard is not added.

The three-source agreement can stay WAIT when options direction is unconfirmed; the separate candle-direction card remains usable with valid fresh candles. News is sourced RSS context with experimental headline matching. Market data is while-open polling, not tick streaming. No market holiday calendar is claimed.

## Validation and installation

Offline regressions cover connected-form hiding/restoration, reordered navigation with stable saved page IDs, underlying retention when expiry lookup fails, broker-only choices, unknown lifecycle events, fresh/stale API paper marks without real orders, same-session option snapshot deltas, queued reads and no submit retry. Full suite and CI must pass before signing. Final artifact provenance, packaged sources, version code, package name and permanent signer must be verified before delivery. Device installation, authenticated broker responses and real fills cannot be certified by offline tests.
