# BOT KING V3 — DhanHQ Market Quote Empty-Segment Escalation

**Observed:** 24 November 2026 (India time), Oracle-hosted Clone gateway, DhanHQ API v2.

## What failed

Authenticated read-only POST to `https://api.dhan.co/v2/marketfeed/ltp` using the documented JSON shape:

```json
{"IDX_I":[13,25,51],"NSE_EQ":[2885]}
```

A successful response envelope was received (`status=success`), but `data.IDX_I={}` and `data.NSE_EQ={}`: NIFTY, BANKNIFTY, SENSEX and RELIANCE have **0/4** valid `last_price` objects. Independent `/v2/marketfeed/ohlc` also returned 0/3 index IDs. No `remarks` or `errorCode` was present in the sanitized LTP audit.

**Profile validation:** authenticated `GET /v2/profile` returned a matching Dhan Client ID and `dataPlan=active`. This proves profile/plan state, not that the Market Quote service is delivering data.

## Independent server evidence

- V1 and Clone services active; Nginx and token timer active
- V1 health HTTP 200; Clone health HTTP 200
- unauthenticated quote endpoint HTTP 403, as expected
- installed Clone source after guarded fix Git blob: `d90231e8cf8f18516c5cf2922acd7b9953d0da83`, verified directly on Oracle
- 24h sanitized diagnostic counts: `quotes.mapping.missing_security_id=24`, `quotes.provider.auth_unavailable=3`, `candles.provider.auth_unavailable=2`, `candles.provider.upstream_error=1`
- no raw tokens, account numbers, SSK, payload bodies, price values, or personal information included here.

## Question for Dhan API & Algo Support

Please review why authenticated Market Quote LTP and OHLC requests return a success envelope with empty segment objects despite active Data API subscription and valid account profile.

1. Are `IDX_I/13`, `IDX_I/25`, `IDX_I/51` and `NSE_EQ/2885` currently enabled for REST quotes on this account, including outside trading hours?
2. Is there a backend incident, entitlement mismatch or index/equity instrument mapping change? If there is a known service problem, please provide an incident reference and resolution.
3. Should the API return structured errors instead of `status=success` with `data.IDX_I={}` and `data.NSE_EQ={}`?
4. What is the supported procedure to verify Market Quote entitlement separately from `/v2/profile`'s `dataPlan=active`?
5. Is live WebSocket quote feed expected to remain available if REST Market Quote returns empty segments, and are there any distinct entitlements?

Please advise using your secure support channel for account-specific checks; do **not** request an access token in public.

## Implementation state

- Gateway correctly rejects unvalidated prices, with fixed `EMPTY_SEGMENTS` error stage and 30s bounded cooldown. Source installed on Oracle, V1 left unchanged.
- Phone B3 regression PASS on GitHub; phone still requires at least one genuine Dhan price to activate quote data.
- Trading orders and fake LIVE voting remain disabled.
- No workaround should be implemented by changing documented IDs, reusing stale HIST prices as LIVE, or masking the empty-response failure.

## Official cross-references

- [DhanHQ v2 Market Quote API](https://dhanhq.co/docs/v2/market-quote/)
- [Dhan API & Algo Support](https://dhan.co/support/platforms/dhanhq-api/)
- [Comparable public report: dhan-oss/DhanHQ-py issue #164](https://github.com/dhan-oss/DhanHQ-py/issues/164) (not proof of same cause)

**Security:** do not attach full request headers, secrets, raw account-specific broker profile responses, private IP addresses, or tokens to a public issue.
