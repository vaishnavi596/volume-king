#!/usr/bin/env python3
"""Read-only source-level B3 history single-flight preflight for Oracle.

Never imports/executes the target server, reads environment files, sends network
requests or prints source content. Source checks are NOT runtime/deploy proof.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def audit(server: Path):
    if not server.is_file() or server.is_symlink():
        raise ValueError("Expected regular non-symlink server.py")
    raw = server.read_bytes()
    source = raw.decode("utf-8")
    tree = ast.parse(source)
    handlers = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        route = False
        singleflight = False
        for deco in node.decorator_list:
            if isinstance(deco, ast.Name) and deco.id == "history_singleflight":
                singleflight = True
            if (isinstance(deco, ast.Call) and isinstance(deco.func, ast.Attribute)
                    and isinstance(deco.func.value, ast.Name)
                    and deco.func.value.id == "app"
                    and deco.func.attr.lower() == "post" and deco.args
                    and isinstance(deco.args[0], ast.Constant)
                    and deco.args[0].value == "/dhan/intraday"):
                route = True
        if route:
            handlers.append((node, singleflight))
    one_route = len(handlers) == 1
    body = ast.get_source_segment(source, handlers[0][0]) if one_route else ""
    checks = {
        "one_intraday_post_route": one_route,
        "route_guarded_by_history_singleflight": bool(one_route and handlers[0][1]),
        # These are conservative source indicators, not semantic/runtime guarantees.
        "route_checks_pairing": bool(body and "compare_digest" in body),
        "route_checks_date_window": bool(body and "body.to_date" in body
                                         and "body.from_date" in body),
        "route_rechecks_validated_cache": bool(body and "candle_cache.get" in body
                                               and "cached.get(\"bars\")" in body),
        "route_preserves_nonlive_provenance": bool(body and
                                                  '"live_orders_enabled": False' in body),
        "singleflight_lock_declaration": "history_miss_locks =" in source,
        "singleflight_guard_defined": "def history_singleflight(" in source,
    }
    return {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "syntax": "PASS",
        "source_checks": checks,
        "source_ready_for_manual_review": all(checks.values()),
        "runtime_verified": False,
        "oracle_deployed_verified": False,
        "production_changed": False,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=Path,
                        default=Path("/opt/bot-king-server/server.py"))
    args = parser.parse_args()
    print(json.dumps(audit(args.server), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
