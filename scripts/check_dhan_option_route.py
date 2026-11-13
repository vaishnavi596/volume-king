"""Read-only Oracle smoke check; never prints secrets or raw provider payloads.

Usage: BOTKING_URL=https://... BOTKING_PAIRING_KEY=... python3 scripts/check_dhan_option_route.py NIFTY 2026-11-19
Run only after deploying the corresponding backend code. No order endpoint is called.
"""
import datetime
import json
import os
import sys
import urllib.error
import urllib.request


def check(base_url, pairing_key, symbol, expiry, opener=urllib.request.urlopen):
    if not base_url.startswith("https://") and not base_url.startswith("http://127.0.0.1"):
        raise ValueError("HTTPS or local loopback required")
    if len(pairing_key) < 32:
        raise ValueError("Pairing key unavailable")
    if symbol != "NIFTY":
        raise ValueError("Only instrument-master-verified NIFTY is supported")
    expiry_date = datetime.date.fromisoformat(expiry)
    if expiry_date < datetime.date.today():
        raise ValueError("Expiry already passed")
    req = urllib.request.Request(
        base_url.rstrip("/") + "/dhan/option-chain",
        data=json.dumps({"symbol": symbol, "expiry": expiry}).encode(),
        headers={"Content-Type": "application/json", "X-BotKing-Key": pairing_key},
        method="POST",
    )
    try:
        with opener(req, timeout=15) as response:
            status = response.status
            data = json.load(response)
    except urllib.error.HTTPError as exc:
        return {"http": exc.code, "verified": False,
                "reason": {403: "pairing_rejected", 404: "route_not_deployed",
                           422: "mapping_or_expiry_rejected", 429: "rate_limited",
                           502: "provider_or_chain_unavailable",
                           503: "credentials_unavailable"}.get(exc.code, "request_failed")}
    except (urllib.error.URLError, TimeoutError, ValueError, OSError):
        return {"http": None, "verified": False, "reason": "connection_or_response_failed"}
    if status != 200 or not isinstance(data, dict):
        return {"http": status, "verified": False, "reason": "unexpected_response"}
    valid = (data.get("source") == "dhan" and data.get("symbol") == symbol
             and data.get("expiry") == expiry and data.get("freshness") == "unverified"
             and data.get("signal_eligible") is False
             and data.get("live_orders_enabled") is False
             and isinstance(data.get("pcr"), (int, float))
             and isinstance(data.get("max_pain"), (int, float)))
    return {"http": status, "verified": valid,
            "reason": "contract_valid_freshness_unverified" if valid else "contract_invalid",
            "strike_count": data.get("strike_count") if valid else None}


def main():
    if len(sys.argv) != 3:
        print("Usage: check_dhan_option_route.py NIFTY YYYY-MM-DD")
        return 2
    try:
        result = check(os.environ.get("BOTKING_URL", ""),
                       os.environ.get("BOTKING_PAIRING_KEY", ""),
                       sys.argv[1], sys.argv[2])
    except (ValueError, TypeError):
        result = {"verified": False, "reason": "invalid_configuration_or_expiry"}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["verified"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
