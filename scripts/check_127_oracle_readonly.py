"""BOT KING 127-B/D authenticated Oracle read-only acceptance probe.

Run on an authorized operator shell with BOTKING_URL and BOTKING_PAIRING_KEY
supplied through an existing safe secret mechanism. Never commit credentials.
This script does NOT modify Oracle or call Dhan/order APIs directly.
Expiry/chain uses broker-listed expiry, serial pacing, and NO retry storms.
Outputs only status/count diagnostics; prices and credentials are not logged.
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ALLOWED_OPTIONS = ("NIFTY", "BANKNIFTY", "SENSEX", "RELIANCE", "HDFCBANK")
SAFE_ROUTES = frozenset((
    "/dhan/status", "/v2/snapshot", "/dhan/index-ltp-batch",
    "/dhan/selected-ltp-batch", "/dhan/option-expiries", "/dhan/option-chain"))
class RejectRedirect(urllib.request.HTTPRedirectHandler):
    """Pairing credentials must never follow a redirect to another origin."""
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


HTTP_REASONS = {
    403: "pairing_rejected", 404: "not_deployed", 409: "expiry_cache_required",
    422: "symbol_or_expiry_not_listed", 429: "rate_limited",
    502: "provider_or_chain_unavailable", 503: "credentials_unavailable",
    504: "upstream_timeout",
}


def origin_checked(url):
    if not isinstance(url, str):
        raise ValueError("URL missing")
    parsed = urllib.parse.urlsplit(url.rstrip("/"))
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username
            or parsed.password or parsed.path or parsed.query or parsed.fragment
            or parsed.port not in (None, 443)):
        raise ValueError("Use a trusted HTTPS server origin only")
    return url.rstrip("/")


def request(origin, pairing_key, path, payload=None, opener=None):
    if path not in SAFE_ROUTES:
        raise ValueError("Non-read-only path rejected")
    if not isinstance(pairing_key, str) or len(pairing_key) < 32:
        raise ValueError("Pairing key missing")
    if not pairing_key.isascii() or any(ord(x) <= 32 or ord(x) >= 127 for x in pairing_key):
        raise ValueError("Invalid pairing key header")
    url = origin_checked(origin) + path
    headers = {"X-BotKing-Key": pairing_key, "Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload, allow_nan=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers,
                                 method="POST" if payload is not None else "GET")
    if opener is None:
        # Ignore machine-wide proxy variables when sending sensitive headers.
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), RejectRedirect())
    try:
        with opener.open(req, timeout=25) as response:
            raw = response.read(2_000_001)
            if len(raw) > 2_000_000:
                return {"http": 200, "error": "oversized_response"}, None
            item = json.loads(raw)
            if not isinstance(item, dict):
                return {"http": 200, "error": "invalid_json_contract"}, None
            if item.get("live_orders_enabled") is not False:
                return {"http": 200, "error": "read_only_safety_mismatch"}, None
            return {"http": response.status, "error": None}, item
    except urllib.error.HTTPError as exc:
        return {"http": exc.code, "error": HTTP_REASONS.get(exc.code, "http_rejected")}, None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, UnicodeError):
        return {"http": None, "error": "network_or_contract_error"}, None


def probe(origin, pairing_key, *, selected=(), option_symbols=("RELIANCE", "HDFCBANK"),
          requester=request, pause=time.sleep):
    summary = {"scope": "READ_ONLY", "live_orders_enabled": False, "status": {},
               "snapshot": {}, "indices": {}, "selected": {}, "options": {}}
    status, data = requester(origin, pairing_key, "/dhan/status")
    summary["status"] = {**status, "authenticated": data.get("authenticated") is True if data else False,
                         "market_data_configured": data.get("market_data_configured") is True if data else False}
    info, data = requester(origin, pairing_key, "/v2/snapshot")
    quotes = data.get("quotes") if data else None
    summary["snapshot"] = {
        **info, "source": data.get("source") if data else None,
        "count": len(quotes) if isinstance(quotes, dict) else None,
        "age_seconds": data.get("age_seconds") if data else None,
        "freshness": data.get("freshness") if data else None,
    }
    info, data = requester(origin, pairing_key, "/dhan/index-ltp-batch", {})
    quotes = data.get("quotes") if data else None
    summary["indices"] = {
        **info, "source": data.get("source") if data else None,
        "count": len(quotes) if isinstance(quotes, dict) else None,
        "unavailable_count": len(data.get("unavailable", [])) if data else None,
        "freshness": data.get("freshness") if data else None,
    }
    if selected:
        if len(selected) > 70 or len(selected) != len(set(selected)) or any(
                not s.isascii() or not s.replace("-", "").replace("_", "").replace("&", "").isalnum()
                for s in selected):
            raise ValueError("Invalid bounded selected-equity symbols")
        info, data = requester(origin, pairing_key, "/dhan/selected-ltp-batch",
                               {"symbols": list(selected)})
        rows = data.get("quotes") if data else None
        summary["selected"] = {**info, "count": len(rows) if isinstance(rows, dict) else None,
                               "requested": len(selected), "source": data.get("source") if data else None}
    # Validate selections *before* any authenticated outbound requests.
    if any(symbol not in ALLOWED_OPTIONS for symbol in option_symbols):
        raise ValueError("Options underlying must be allowlisted")
    if len(option_symbols) != len(set(option_symbols)):
        raise ValueError("Duplicate option underlying")
    if not summary["status"]["authenticated"] or not summary["status"]["market_data_configured"]:
        summary["options_status"] = "skipped_no_authenticated_market_data"
        return summary
    for i, symbol in enumerate(option_symbols):
        if i:
            pause(3.5)
        expiry_info, expiry_payload = requester(origin, pairing_key, "/dhan/option-expiries",
                                                {"symbol": symbol})
        dates = expiry_payload.get("expiries") if expiry_payload else None
        result = {"expiry_http": expiry_info["http"], "expiry_error": expiry_info["error"],
                  "expiry_count": len(dates) if isinstance(dates, list) else None,
                  "chain_http": None, "chain_error": "no_listed_expiry",
                  "atm_strike_count": None, "pcr_available": False,
                  "max_pain_available": False, "source": None}
        if isinstance(dates, list) and dates and all(isinstance(x, str) for x in dates):
            # One strictly listed expiry per symbol, no speculative date guessing.
            pause(3.5)
            chain_info, chain = requester(origin, pairing_key, "/dhan/option-chain",
                                          {"symbol": symbol, "expiry": dates[0]})
            result["chain_http"] = chain_info["http"]
            result["chain_error"] = chain_info["error"]
            if chain:
                window = chain.get("atm_window")
                rows = window.get("rows") if isinstance(window, dict) else None
                valid = (chain.get("symbol") == symbol and chain.get("expiry") == dates[0]
                         and chain.get("source") == "dhan"
                         and chain.get("freshness") == "unverified"
                         and chain.get("signal_eligible") is False)
                result["source"] = chain.get("source") if valid else "contract_invalid"
                result["atm_strike_count"] = len(rows) if valid and isinstance(rows, list) else None
                result["pcr_available"] = valid and type(chain.get("pcr")) in (int, float)
                result["max_pain_available"] = valid and type(chain.get("max_pain")) in (int, float)
        summary["options"][symbol] = result
        if result["expiry_http"] == 429 or result["chain_http"] == 429:
            summary["options_status"] = "rate_limited_remaining_skipped"
            break
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only BOT KING Oracle 127 probe")
    parser.add_argument("--options", nargs="*", choices=ALLOWED_OPTIONS,
                        default=["RELIANCE", "HDFCBANK"])
    parser.add_argument("--selected", nargs="*", default=[])
    args = parser.parse_args(argv)
    try:
        result = probe(os.environ.get("BOTKING_URL", ""),
                       os.environ.get("BOTKING_PAIRING_KEY", ""),
                       selected=tuple(args.selected), option_symbols=tuple(args.options))
    except (ValueError, TypeError):
        print(json.dumps({"error": "invalid_configuration", "live_orders_enabled": False}))
        return 2
    print(json.dumps(result, sort_keys=True, allow_nan=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
