# Successful login followed by failed history: safe gateway diagnostics

Observed owner log on 2026-11-05: `/v1/login` returned 200 at 07:18:53 server time; `/v1/history` returned 502 and a second `/v1/history` returned 401 at 07:18:54. This proves accepted login and subsequent data/authentication failures. It does not prove that the 502 caused the 401, nor identify the underlying broker reason. Different index requests can fail independently.

The diagnostic patch emits only fixed event names, broker operation names, HTTP status, allowlisted AG/AB/AM four-digit error codes, exact-match counts and fixed internal reason categories. It never emits broker response bodies, raw exception messages, payloads, request headers, keys, client IDs, PINs, TOTP or JWT/session tokens. Unknown codes/reasons are UNCLASSIFIED/unclassified. Gateway authentication denial logs only session_missing/session_mismatch. Login logs acceptance without any account data.

HTTP 401/403 handling, session expiry/revocation and live order safeguards are intentionally unchanged pending actual upstream evidence. This is instrumentation, not a claim that live data or authentication is fixed. It requires only the existing server installer; no Android rebuild or reinstall. The installer backs up the existing service and clears its in-memory session on restart; the owner then logs in once and reads BOTKING diagnostic journal events.

The existing access logger may be disabled again by the installer. Diagnostic WARNING events remain visible in the systemd journal independently of HTTP access logging. Remove or lower the diagnostic events once the actual failure is resolved.
