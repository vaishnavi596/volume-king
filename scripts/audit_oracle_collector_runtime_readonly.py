#!/usr/bin/env python3
"""One bounded, read-only Oracle collector/runtime contract probe.

Run only on Oracle with BOTKING_AUDIT_PAIRING_KEY set by its operator.
Only GET /health, /v2/server-readiness and /v2/snapshot; never send Dhan
orders, batch quotes, historical requests, OAuth, or log credentials.

Example:
  BOTKING_AUDIT_PAIRING_KEY=<set securely in shell> python3 scripts/audit_oracle_collector_runtime_readonly.py
Output reports aggregate status/age/count only, no symbol prices or tokens.
"""
import json
import math
import os
import urllib.error
import urllib.request
from dataclasses import dataclass

ORIGIN = "http://127.0.0.1:8000"
PATHS = ("/health", "/v2/server-readiness", "/v2/snapshot")
MAX_BYTES = 1_000_000


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
    opener = opener or urllib.request.build_opener(urllib.request.ProxyHandler({}))
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


def summarize(results):
    by_route = {r.route: r for r in results}
    health = by_route.get("/health")
    readiness = by_route.get("/v2/server-readiness")
    snapshot = by_route.get("/v2/snapshot")
    collector = (readiness.body or {}).get("collector", {}) if readiness and readiness.http == 200 else {}
    data = snapshot.body or {} if snapshot and snapshot.http == 200 else {}
    if not isinstance(collector, dict):
        collector = {}
    if not isinstance(data, dict):
        data = {}
    quotes = data.get("quotes")
    unavailable = data.get("unavailable")
    safe_status = {"disabled", "not_collected", "upstream_error",
                   "recently_collected", "collection_overdue"}
    collection_status = data.get("collection_status")
    readiness_status = collector.get("status")
    return {
        "health_http": health.http if health else 0,
        "health_ok": bool(health and health.http == 200
                          and (health.body or {}).get("status") == "ok"),
        "readiness_http": readiness.http if readiness else 0,
        "readiness_route_available": bool(readiness and readiness.http == 200),
        "collector_enabled": collector.get("configured_enabled")
                            if type(collector.get("configured_enabled")) is bool else None,
        "collector_status": readiness_status if readiness_status in safe_status else "unknown",
        "collector_interval_seconds": scalar_number(collector.get("interval_seconds")),
        "collector_last_success_age_seconds": scalar_number(collector.get("last_success_age_seconds")),
        "snapshot_http": snapshot.http if snapshot else 0,
        "snapshot_protocol": data.get("protocol") if data.get("protocol") == 2 else None,
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
