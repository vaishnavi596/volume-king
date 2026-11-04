# BOT KING gateway v1 / app 2.0.2

The optional gateway routes Angel One market data through the owner's Oracle
server. Blank server address in Settings retains direct Angel One access.
No order placement, modification, cancellation, unattended execution, account
funds or portfolio endpoints are implemented.

## Connection

Settings accepts an HTTPS origin, a separate server access key and an explicit
trust checkbox. With server mode enabled, API key, client code, MPIN and current
TOTP travel over TLS to that server and then to Angel One. This changes the
previous direct-to-broker credential path, so the UI explains it before login.
Credentials are not saved in preferences, backups or server files. The app's
server access key is not persisted. Treat the server owner as trusted.

Server login requires `X-BotKing-Key`, generated on the server. It returns an
opaque session, never the Angel JWT/API key. One owner session is supported;
a new login attempt invalidates the previous session. Sessions expire after
30 minutes idle or 8 hours total, or earlier if Angel rejects the session.
An expiry sweeper clears in-memory broker credentials within about a minute.
Process restart clears all sessions. Logout attempts server revocation; when
the server cannot be reached the app clears its local token and explains the
remote session remains until timeout. Instrument catalog is refreshed on login.

## Protocol

- `GET /health`: public status and protocol version; no credentials.
- `POST /v1/login`: `{api_key, client_code, pin, totp}`, owner key header.
- `POST /v1/logout`: Bearer session, empty JSON.
- `POST /v1/history`: `{symbol, interval, period}`.
- `POST /v1/expiries`: `{symbol}`.
- `POST /v1/options`: `{symbol, expiry, spot}`.
- `POST /v1/option-history`: `{symbol, expiry, strike, side}`.

All data/logout endpoints require a Bearer session. Input and upstream errors
are sanitized. Login is limited to five paired attempts/minute; Nginx also
limits unpaired login requests. JSON body limit is 8 KiB. Sessions/data are not
cached by HTTP clients. App HTTPS transport refuses redirects and non-origin
URLs. The single-worker gateway serializes broker work and rejects concurrent
work with 429 instead of queueing many market requests on a 1 GiB VM.

## Oracle deployment

`backend/install-oracle.sh FULL_COMMIT_SHA` is run with sudo on the existing
Oracle Linux host. It downloads only files from that immutable revision,
installs pinned Python dependencies in the existing virtualenv, backs up the
server and Nginx files, and uses a systemd drop-in with one worker. It preserves
the existing TLS configuration and adds only `/v1/` routing. It generates a
root-only environment file and owner-readable pairing-key file, neither in git.
It validates Nginx, waits for protocol-1 health, and checks anonymous data access
returns 401. On an installation failure after backup it restores prior server,
drop-in and Nginx files. Python dependency upgrades are not rolled back.

Transfer `/home/opc/bot-king-pairing-key.txt` privately using SCP; do not send it
to chat or include it in screenshots. Enter its contents only in the new app's
Server access key field. Enter the endpoint without `/health`:
`https://botkingrajesh.duckdns.org`. Server-side installation and actual broker
login must be verified on the user's host before claiming end-to-end success.

Existing certificate renewal is still unverified: staging validation returned
intermittent DNS SERVFAIL, followed by Service busy. The valid production
certificate and enabled renewal timer are retained. This installer does not
retry ACME issuance or modify DNS/firewall rules.
