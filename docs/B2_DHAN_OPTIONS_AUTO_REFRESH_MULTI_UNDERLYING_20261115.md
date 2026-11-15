# BOT KING B2 — Dhan Option Chain automatic refresh and multi-underlying audit
Date: 2026-11-15

## Report from installed v2.3.120
- Options manual Refresh was required; NIFTY alone supplied data.
- Scanner OI Support, OI Resistance, OI Profile and Max Pain showed **No matching Dhan expiry snapshot**.
- News headline counts were visible but unclassified; Technical was historical and other engines WAIT.
- A successful historical price signal does not confirm options, live timestamps or futures integration.

## Root causes found in GitHub source
- `src/server_feed.py` rejected every options underlying except NIFTY before requesting any API.
- `src/main.py` rejected non-NIFTY in `refresh_selected_options` and the automatic poll selected NIFTY only.
- `backend/server.py` offered `/dhan/option-chain` but had no matching `/dhan/option-expiries` route in this branch; option-chain validation restricted to IDX_I.
- Dhan API officially supports expiry lists and option chain for mapped underlying IDs and segments; stock underlyings use their cash security ID. A mapped underlying is **not** proof that derivatives are listed or that the account has Dhan data entitlement.

## B2 code changes
- Implemented a Dhan-only authenticated `/dhan/option-expiries` endpoint in the repository backend. It queries Dhan `/v2/optionchain/expirylist`, checks returned dates, rejects missing listings, and discloses no credentials.
- Expanded backend `/dhan/option-chain` to **mapped** IDX_I, BSE_I and NSE_EQ underlyings; provider rejection or incomplete chain still gives 4xx/5xx. No fabricated CE/PE premiums.
- Android client now accepts broker-mapped index/equity underlyings, including NIFTY, BANKNIFTY, SENSEX, RELIANCE and HDFCBANK. It must still verify listed expiry and entitlement at request time.
- Symbol/expiry selection triggers automatic fetch; a selection during an existing request is queued. Replay is paced to honor Dhan's >=3-second option quota.
- Removed manual option-refresh buttons, removed calculated calendar expiries from the Dhan Options display, and changed old 'press Refresh' captions to loading, connection or error status.
- Shared option data is still read-only and unverified for trading; scanner OI and five-engine Options directional votes remain WAIT until independently verified evidence is available. Futures integration is a separate missing provider feed.

## Release and deployment gates
- The existing Oracle deployment at `/opt/bot-king-server/server.py` is **not automatically modified** by GitHub commits. Need to compare actual deployed endpoints and backing implementation, back up production, then deploy compatible endpoints before treating multi-symbol auto-refresh as working end to end. The repository's `backend/server.py` is not proof of the contents of the running Oracle service.
- GitHub offline test PASS and APK packaging are not equivalent to Oracle provider entitlement checks.
- Mandatory Oracle tests (authenticated with existing key, never exposing token): GET /dhan/status, POST /dhan/option-expiries for NIFTY/BANKNIFTY/SENSEX/HDFCBANK, POST /dhan/option-chain for one broker-listed expiry per underlying; check 422/429/502 and PCR/Max Pain/ATM-window shapes.
- Required Android tests: change Options symbol quickly twice, confirm automatic loading and no NIFTY bleed-through, check 15 saved filters, ensure historical technical remains HIST and unverified OI remains WAIT, confirm live orders OFF.

Status: SOURCE PATCHED; successful Oracle live checks and mobile install are separate gates.
