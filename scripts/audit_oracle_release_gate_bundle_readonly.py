#!/usr/bin/env python3
"""One bounded, read-only Oracle release-evidence bundle (NO Dhan API/orders).

Reads only deployed Python source, never imports it. Performs at most three
localhost GETs, with protected requests only when an operator securely
provides BOTKING_AUDIT_PAIRING_KEY. Does not inspect watchlist JSON or env.
This can collect evidence, not deploy code or attest exchange freshness.
"""
import json
import os
import sys
from pathlib import Path

# Allow both "python3 scripts/audit_oracle_release_gate_bundle_readonly.py"
# and "python3 -m scripts.audit_oracle_release_gate_bundle_readonly".
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from scripts.audit_oracle_app_routes_readonly import audit as routes_audit
from scripts.audit_oracle_five_filters_readonly import audit as filters_audit
from scripts.audit_oracle_watchlist_s18_readonly import audit as watchlist_audit
from scripts.audit_oracle_collector_runtime_readonly import PATHS, request_get, summarize

SERVER_PATH = Path("/opt/bot-king-server/server.py")
WATCHLIST_PATH = Path("/opt/bot-king-server/watchlist_store.py")


def _source_result(fn, path):
    try:
        return {"status": "SOURCE_INSPECTED", "details": fn(path)}
    except (OSError, ValueError, SyntaxError, UnicodeError) as exc:
        # Exception descriptions can contain source snippets; never echo them.
        return {"status": "UNAVAILABLE", "reason_class": type(exc).__name__}


def collect(*, pairing_key=None, server_path=SERVER_PATH,
            watchlist_path=WATCHLIST_PATH, http_get=request_get):
    routes = _source_result(routes_audit, server_path)
    filters = _source_result(filters_audit, server_path)
    watchlist = _source_result(watchlist_audit, watchlist_path)
    results = [http_get(path, pairing_key) for path in PATHS]
    runtime = summarize(results)
    return {
        "routes_source": routes,
        "assessment_source": filters,
        "watchlist_s18_source": watchlist,
        "runtime_readonly_get": runtime,
        "production_changed": False,
        "watchlist_saved_json_read": False,
        "orders_attempted": 0,
        "direct_dhan_api_requests": 0,
        "exchange_freshness_verified": False,
        "release_ready": False,
        "note": ("Source inspection and cached localhost GETs alone cannot "
                 "certify Dhan entitlement, 70-rule runtime behavior, "
                 "authenticated option chains, mobile device or signed APK."),
    }


def main():
    # Do not print, persist, or introspect the operator's pairing key.
    key = os.environ.get("BOTKING_AUDIT_PAIRING_KEY")
    print(json.dumps(collect(pairing_key=key), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
