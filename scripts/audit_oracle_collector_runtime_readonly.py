#!/usr/bin/env python3
"""One bounded, read-only Oracle collector/runtime contract probe.

Run only on Oracle with BOTKING_AUDIT_PAIRING_KEY set by its operator.
Only GET /health, /v2/server-readiness, /v2/snapshot, three cached
index assessments and three mapping-only index status routes; never send Dhan
orders, batch quotes, historical requests, OAuth, or log credentials.

Example:
  BOTKING_AUDIT_PAIRING_KEY=<set securely in shell> python3 scripts/audit_oracle_collector_runtime_readonly.py
Output reports aggregate status/age/count only, no symbol prices or tokens.
"""
from __future__ import annotations

import json
import math
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

ORIGIN = "http://127.0.0.1:8000"
INDEX_SYMBOLS = ("NIFTY", "BANKNIFTY", "SENSEX")
PATHS = ("/health", "/v2/server-readiness", "/v2/snapshot") + tuple(
    "/v2/assessment/" + symbol for symbol in INDEX_SYMBOLS
) + tuple(
    "/v2/option-underlying-status/" + symbol for symbol in INDEX_SYMBOLS
)
MAX_BYTES = 1_000_000


class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Never forward protected audit GET headers to another origin."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@dataclass(frozen=True)
class ProbeResult:
    route: str
    http: int
    body: dict | None


def request_get(path, pairing_key=None, *, opener=None):
    if path not in PATHS:
        raise ValueError("Unapproved read-only probe route")
    headers = {"Accept": "application/json"}
    if path != "/health":
        if not isinstance(pairing_key, str) or not pairing_key.strip():
            return ProbeResult(path, 0, None)
        headers["X-BotKing-Key"] = pairing_key
    req = urllib.request.Request(ORIGIN + path, headers=headers, method="GET")
    # Avoid leaking loopback bearer/pairing headers via proxy configuration.
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=5) as response:
            raw = response.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                return ProbeResult(path, 0, None)
            parsed = json.loads(raw)
            return ProbeResult(path, int(response.status), parsed if isinstance(parsed, dict) else None)
    except urllib.error.HTTPError as exc:
        return ProbeResult(path, int(exc.code), None)
    except (urllib.error.URLError, ValueError, OSError, json.JSONDecodeError):
        return ProbeResult(path, 0, None)


def scalar_number(value):
    if type(value) not in (int, float) or not math.isfinite(value) or value < 0:
        return None
    return round(float(value), 1)



def classify_snapshot_error(value):
    """Return only bounded diagnostic categories, never raw upstream text."""
    if value in (None, "not_collected"):
        return "NO_RECORDED_ERROR"
    if not isinstance(value, str):
        return "OTHER_ERROR"
    if value == "ingest_unavailable":
        return "INGEST_EXCEPTION"
    if value == "upstream_http_429":
        return "RATE_LIMIT_429"
    if value in ("upstream_http_401", "upstream_http_403"):
        return "UPSTREAM_ACCESS_DENIED"
    if value in ("upstream_http_502", "upstream_http_503", "upstream_http_504"):
        return "UPSTREAM_UNAVAILABLE"
    if value.startswith("upstream_http_") and len(value) == len("upstream_http_") + 3:
        suffix = value[-3:]
        if suffix.isascii() and suffix.isdecimal():
            return "UPSTREAM_HTTP_OTHER"
    return "OTHER_ERROR"


def summarize(results):
    by_route = {r.route: r for r in results}
    health = by_route.get("/health")
    readiness = by_route.get("/v2/server-readiness")
    snapshot = by_route.get("/v2/snapshot")
    readiness_body = (readiness.body if readiness and readiness.http == 200
                      and isinstance(readiness.body, dict) else {})
    collector_field = readiness_body.get("collector")
    collector = collector_field if isinstance(collector_field, dict) else {}
    data = (snapshot.body if snapshot and snapshot.http == 200
            and isinstance(snapshot.body, dict) else {})
    if not isinstance(data, dict):
        data = {}
    quotes = data.get("quotes")
    unavailable = data.get("unavailable")
    safe_status = {"disabled", "not_collected", "upstream_error",
                   "recently_collected", "collection_overdue"}
    collection_status = data.get("collection_status")
    readiness_status = collector.get("status")
    indices = {}
    for symbol in INDEX_SYMBOLS:
        probe = by_route.get("/v2/assessment/" + symbol)
        body = (probe.body if probe and probe.http == 200
                and isinstance(probe.body, dict) else {})
        factors = body.get("factors")
        filters = body.get("assessment_filters")
        factors = factors if isinstance(factors, dict) else {}
        filters = filters if isinstance(filters, list) else []
        allowed = {"available", "unavailable", "pending", "stale"}
        mapping_probe = by_route.get("/v2/option-underlying-status/" + symbol)
        mapping = (mapping_probe.body if mapping_probe and mapping_probe.http == 200
                   and isinstance(mapping_probe.body, dict) else {})
        indices[symbol] = {
            "mapping_http": mapping_probe.http if mapping_probe else 0,
            "mapping_status": mapping.get("status") if mapping.get("status") in
                              ("mapping_only", "unmapped", "invalid_symbol") else "unknown",
            "underlying_mapped": mapping.get("mapped") is True,
            "expiry_verified": mapping.get("expiry_verified") is True,
            "chain_verified": mapping.get("chain_verified") is True,
            "pcr_verified": mapping.get("pcr_verified") is True,
            "http": probe.http if probe else 0,
            "assessment_status": (body.get("status") if body.get("status") in
                                  ("complete", "incomplete", "unavailable") else "unknown"),
            "signal_eligible": body.get("signal_eligible") is True,
            "factor_statuses": {
                name: (factors[name].get("status") if isinstance(factors.get(name), dict)
                       and factors[name].get("status") in allowed else "unknown")
                for name in ("news", "futures", "options", "candle")
            },
            "filter_statuses": {
                name: next((
                    item.get("status") for item in filters
                    if isinstance(item, dict) and item.get("id") == name
                    and item.get("status") in allowed
                ), "unknown")
                for name in ("oi_support", "oi_resistance", "max_pain",
                             "pcr", "candle_trend")
            },
        }
    return {
        "index_assessments": indices,
        "health_http": health.http if health else 0,
        "health_ok": bool(health and health.http == 200
                          and isinstance(health.body, dict)
                          and health.body.get("status") == "ok"),
        "readiness_http": readiness.http if readiness else 0,
        "readiness_route_available": bool(readiness and readiness.http == 200),
        "readiness_collector_schema": "object" if isinstance(collector_field, dict) else "missing_or_other",
        "readiness_market_data_type": type(readiness_body.get("market_data")).__name__ if "market_data" in readiness_body else "missing",
        "collector_enabled": collector.get("configured_enabled")
                            if type(collector.get("configured_enabled")) is bool else None,
        "collector_status": readiness_status if readiness_status in safe_status else "unknown",
        "collector_interval_seconds": scalar_number(collector.get("interval_seconds")),
        "collector_last_success_age_seconds": scalar_number(collector.get("last_success_age_seconds")),
        "snapshot_http": snapshot.http if snapshot else 0,
        "snapshot_protocol": data.get("protocol") if data.get("protocol") == 2 else None,
        "snapshot_error_class": classify_snapshot_error(data.get("error")),
        "snapshot_status": collection_status if collection_status in
                           safe_status | {"awaiting_next_collection"} else "unknown",
        "snapshot_age_seconds": scalar_number(data.get("age_seconds")),
        "equity_quote_count": len(quotes) if isinstance(quotes, dict) else None,
        "unavailable_count": len(unavailable) if isinstance(unavailable, list) else None,
        "live_orders_enabled": data.get("live_orders_enabled")
                               if data.get("live_orders_enabled") is False else None,
        "oracle_production_changed": False,
        "dhan_api_calls_made": 0,
        "quote_freshness_exchange_verified": False,
    }


def main():
    pairing = os.environ.get("BOTKING_AUDIT_PAIRING_KEY")
    # Do not print whether a key is present, nor echo any secret on errors.
    results = [request_get(path, pairing) for path in PATHS]
    print(json.dumps(summarize(results), sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
