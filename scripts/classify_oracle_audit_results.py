#!/usr/bin/env python3
"""Classify *sanitized* Oracle audit JSON reports; never probe production.

Input files must be the output of:
audit_oracle_app_routes_readonly.py, audit_oracle_five_filters_readonly.py,
audit_oracle_collector_runtime_readonly.py.
No network, auth secrets, broker calls, deployment or side effects.
"""
import argparse
import json
from pathlib import Path

EXPECTED_ROUTES = 9


def classify(routes, filters, collector):
    """Return prioritized, evidence-scoped issues; unknown never becomes PASS."""
    if not all(isinstance(x, dict) for x in (routes, filters, collector)):
        raise ValueError("All three sanitized reports must be JSON objects")
    issues = []

    def add(code, scope, action):
        issues.append({"code": code, "scope": scope, "next_action": action})

    if routes.get("syntax") != "PASS" or routes.get("expected_routes") != EXPECTED_ROUTES:
        add("ROUTE_AUDIT_UNVERIFIED", "source", "Repeat nine-route AST audit on deployed server.py")
    elif routes.get("source_missing"):
        add("SOURCE_ROUTES_MISSING", "source", "Compare deployed routes with GitHub; backup before patch")
    elif routes.get("source_present") != EXPECTED_ROUTES:
        add("ROUTE_SOURCE_COUNT_UNKNOWN", "source", "Inspect exact missing route checks")
    else:
        add("SOURCE_ROUTES_ONLY", "source", "Route declarations do not prove live HTTP availability")

    if filters.get("syntax") != "PASS" or filters.get("assessment_route_source_count") != 1:
        add("ASSESSMENT_ROUTE_MISSING_OR_DUPLICATE", "source", "Inspect Oracle assessment decorators and backup-first parity")
    elif filters.get("known_placeholder_detected") is True:
        add("FIVE_FILTER_PLACEHOLDER", "source", "Implement verified timestamped producer only after Oracle input audit")
    else:
        add("ASSESSMENT_IMPLEMENTATION_UNKNOWN", "source", "Inspect sanitized source, schema and freshness; do not assert working filters")

    for route, field in (("/health", "health_http"),
                         ("/v2/server-readiness", "readiness_http"),
                         ("/v2/snapshot", "snapshot_http")):
        http = collector.get(field)
        if type(http) is not int or http == 0:
            add("RUNTIME_NOT_VERIFIED", route, "Confirm local service or audit pairing-key availability without logging secrets")
        elif http in (401, 403):
            add("AUTH_DENIED", route, "Verify operator-provided pairing key safely; do not rotate without cause")
        elif http == 404:
            add("LIVE_ROUTE_MISSING", route, "Compare running deployment to declared source")
        elif http == 429:
            add("RATE_LIMIT", route, "Respect Retry-After and 30-second broker cooldown; avoid retries storm")
        elif http != 200:
            add("HTTP_ERROR", route, "Inspect sanitized service error classification")
    if collector.get("health_http") == 200 and collector.get("health_ok") is not True:
        add("HEALTH_PAYLOAD_UNVERIFIED", "runtime", "Check exact health contract before calling healthy")
    if collector.get("readiness_http") == 200:
        enabled = collector.get("collector_enabled")
        if enabled is False:
            add("COLLECTOR_DISABLED", "runtime", "Inspect deployment configuration without logging credentials")
        elif enabled is not True:
            add("COLLECTOR_STATE_UNKNOWN", "runtime", "Inspect sanitized collector enablement")
        status = collector.get("collector_status")
        if status in ("upstream_error", "collection_overdue", "not_collected"):
            add("COLLECTOR_UNHEALTHY", "runtime", "Inspect collector cooldown, last success age and 429 history")
        elif status not in ("recently_collected", "disabled"):
            add("COLLECTOR_FRESHNESS_UNKNOWN", "runtime", "Require timestamped collection evidence")
    if collector.get("snapshot_http") == 200:
        if collector.get("snapshot_protocol") != 2:
            add("SNAPSHOT_CONTRACT_UNKNOWN", "runtime", "Check protocol-2 response")
        if collector.get("snapshot_status") != "recently_collected":
            add("SNAPSHOT_NOT_CURRENTLY_COLLECTED", "runtime", "Check last successful collection age before quote claims")
        if collector.get("live_orders_enabled") is not False:
            add("PAPER_ONLY_NOT_VERIFIED", "runtime", "Do not promote deployment without explicit live_orders_enabled=false")

    return {
        "audit": "ORACLE-FILTER-AUDIT-03",
        "issues": issues,
        "source_audit_complete": (routes.get("syntax") == "PASS"
                                  and routes.get("expected_routes") == EXPECTED_ROUTES
                                  and routes.get("source_present") == EXPECTED_ROUTES
                                  and routes.get("source_missing") == []
                                  and filters.get("syntax") == "PASS"
                                  and filters.get("assessment_route_source_count") == 1),
        "runtime_five_filters_proven": False,
        "equity_pcr_entitlement_proven": False,
        "oracle_production_changed": False,
        "orders_sent": 0,
        "apk_release_allowed": False,
    }


def read_report(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 100_000:
        raise ValueError("Expected a small regular non-symlink sanitized JSON report")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Expected JSON object")
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--routes", required=True)
    p.add_argument("--filters", required=True)
    p.add_argument("--collector", required=True)
    a = p.parse_args()
    print(json.dumps(classify(read_report(a.routes), read_report(a.filters),
                              read_report(a.collector)), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
