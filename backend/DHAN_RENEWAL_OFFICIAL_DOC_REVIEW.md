# Dhan renewal eligibility and timezone: official documentation review (2026-11-09)

Source: https://dhanhq.co/docs/v2/authentication/ (reviewed 2026-11-09)
Secondary release notes: https://dhanhq.co/docs/v2/releases/

## Confirmed
- Dhan Web-generated access tokens have 24-hour validity.
- `GET /v2/RenewToken` is documented **only for active tokens generated from Dhan Web**. It invalidates the previous token and issues another 24-hour token. Expired tokens cannot be renewed.
- The individual API key + secret flow is **three-step interactive consent**: generate consent, browser-based login/2FA, consume consent. The documentation does not authorize treating these consent tokens as eligible for `RenewToken`.
- Dhan explicitly describes `expiryTime` in the **API key/secret consent response** as an ISO timestamp in **IST**. This resolves the consent-response timezone semantics in official docs; current fail-closed code still requires an explicit timezone-aware value and will reject a naive timestamp if persistence is enabled.
- `/v2/profile` documents `tokenValidity` as a date/time string but **does not explicitly state its timezone** on that field. Do not silently apply the consent field's IST rule to profile `tokenValidity`.
- Dhan documents a TOTP-enabled `POST /app/generateAccessToken` flow requiring client ID, PIN and TOTP. This is a different authentication path; no unattended automation of PIN/TOTP or storage of these secrets is authorized here.
- Dhan's API key/secret are documented as valid for 12 months, **not** as a 12-month access token.

## BOT KING decision
**NO-GO for automatic renewal on Oracle.** Existing BOT KING API key/secret consent path cannot safely be connected to `RenewToken` without provider confirmation. Do not send a real renewal request to test eligibility: it could invalidate the current token.

## Next safe steps
1. Confirm the actual production token's provenance without printing or disclosing credentials: Dhan Web-generated vs API key/secret consent.
2. For the consent callback, implement an **explicitly configured** IST interpretation of Dhan's documented offset-free `expiryTime`, with tests, before enabling persistence. Do not change production defaults.
3. Obtain Dhan support's written confirmation if any compliant unattended renewal method exists for the account and token provenance.
4. Keep manual interactive re-authentication as fallback, without promising uninterrupted 24/7 access.
5. Validate the `/v2/profile` timezone independently before enabling strict file-token selection.

No production Oracle changes, real renewal calls, credential rotation or live orders were made during this review.
