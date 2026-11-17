#!/usr/bin/env python3
"""Inspect Oracle's deployed server.py assessment ROUTE SOURCE without execution.

No imports from server.py, no HTTP, no Dhan, no key/env reads and no writes.
Source inspection cannot verify a running process, data freshness or eligibility.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

FILTER_IDS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")
FACTORS = ("news", "futures", "options", "candle")
ROUTE = "/v2/assessment/{symbol}"


def route_functions(tree):
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                    and isinstance(dec.func.value, ast.Name)
                    and dec.func.value.id == "app"
                    and dec.func.attr.lower() == "get" and dec.args
                    and isinstance(dec.args[0], ast.Constant)
                    and dec.args[0].value == ROUTE):
                yield node
                break


def _string_constants(node):
    return {n.value for n in ast.walk(node)
            if isinstance(n, ast.Constant) and isinstance(n.value, str)}


def audit(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Expected regular non-symlink Oracle server.py")
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    routes = list(route_functions(tree))
    # AST expression strings are only source indicators, never running values.
    vals = _string_constants(routes[0]) if len(routes) == 1 else set()
    # Accept both legacy explanatory text and the allowlisted UI reason code.
    # Require the explicit fail-closed status; source inspection is not runtime proof.
    placeholder = (len(routes) == 1 and
                   {"not_configured", "unavailable"} <= vals and
                   ("Independent Oracle assessment not configured" in vals or
                    "reason" in vals))
    return {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "syntax": "PASS",
        "assessment_route_source_count": len(routes),
        "five_filter_ids_in_route_source": len(routes) == 1 and set(FILTER_IDS) <= vals,
        "four_factor_ids_in_route_source": len(routes) == 1 and set(FACTORS) <= vals,
        "known_placeholder_detected": placeholder,
        "producer_proven_functional": False,
        "data_freshness_verified": False,
        "deployed_runtime_route_verified": False,
        "oracle_production_changed": False,
        "dhan_requests_made": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=Path,
                        default=Path("/opt/bot-king-server/server.py"))
    args = parser.parse_args()
    print(json.dumps(audit(args.server), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
