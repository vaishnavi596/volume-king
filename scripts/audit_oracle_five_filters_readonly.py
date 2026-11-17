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


def _delegated_assessment(tree, directory):
    """Strict source-only evidence of delegation within the active app factory."""
    factories = [n for n in tree.body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name == "create_app"]
    factory = factories[0] if len(factories) == 1 else None
    registered = bool(factory) and any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "register_assessment_routes"
        for node in ast.walk(factory)
    )
    module = directory / "assessment_api.py"
    result = {"register_call_present": registered,
              "module_route_present": False,
              "module_syntax": "NOT_CHECKED",
              "module_sha256": None,
              "cache_read_wired": False,
              "expiry_check_present": None,
              "timeframe_requested": None}
    if not registered or not module.is_file() or module.is_symlink():
        return result
    data = module.read_bytes()
    module_tree = ast.parse(data.decode("utf-8"))
    registrars = [n for n in module_tree.body
                  if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                  and n.name == "register_assessment_routes"]
    functions = list(route_functions(registrars[0])) if len(registrars) == 1 else []
    if len(functions) == 1:
        route = functions[0]
        # Source-only indicators, never proof of correct expiry or live data.
        result["expiry_check_present"] = any(
            isinstance(node, ast.Compare)
            and any(isinstance(n, ast.Name) and "expiry" in n.id.lower()
                    for n in ast.walk(node))
            for node in ast.walk(route)
        )
        result["timeframe_requested"] = any(
            a.arg in ("interval", "timeframe")
            for a in route.args.args + route.args.kwonlyargs
        )
    result.update({
        "module_syntax": "PASS",
        "module_sha256": hashlib.sha256(data).hexdigest(),
        "module_route_present": len(functions) == 1,
        "cache_read_wired": (
            len(functions) == 1
            and any(isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                    and n.func.id == "read" for n in ast.walk(functions[0]))
        ),
    })
    return result


def _assessment_state_key_audit(state_tree):
    """Static store-key dimensions only; no runtime cache or values are read."""
    functions = [node for node in state_tree.body
                 if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name == "publish"]
    if len(functions) != 1:
        return {"write_key_dimensions": [], "timeframe_separated": None}
    dimensions = []
    for node in ast.walk(functions[0]):
        if not isinstance(node, (ast.Assign, ast.AnnAssign)):
            continue
        targets = node.targets if isinstance(node, ast.Assign) else [node.target]
        for target in targets:
            if not isinstance(target, ast.Subscript) or not isinstance(target.slice, ast.Tuple):
                continue
            parts = target.slice.elts
            if not all(isinstance(p, ast.Name) for p in parts):
                continue
            fields = [p.id for p in parts]
            if {"scope", "symbol", "kind"} <= set(fields):
                dimensions.append(fields)
    return {
        "write_key_dimensions": dimensions,
        "timeframe_separated": (
            all(any(field in ("timeframe", "interval") for field in dimensions_row)
                for dimensions_row in dimensions) if dimensions else None
        ),
    }


def _evidence_wiring(tree, directory):
    """Inspect static Oracle evidence paths; do not import/execute app modules."""
    writes = []
    candle_publish_lines = []
    five_minute_guard_lines = []
    option_publish_lines = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = node.targets if isinstance(node, ast.Assign) else [node.target]
            if any(isinstance(t, ast.Subscript) and isinstance(t.value, ast.Name)
                   and t.value.id == "candle_cache" for t in targets):
                writes.append(node.lineno)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "publish":
            kinds = {a.value for a in node.args if isinstance(a, ast.Constant)
                     and isinstance(a.value, str)}
            if "candle" in kinds:
                candle_publish_lines.append(node.lineno)
            if "options" in kinds:
                option_publish_lines.append(node.lineno)
        if isinstance(node, ast.If):
            condition = ast.unparse(node.test)
            if "interval" in condition and ("'5'" in condition or '"5"' in condition):
                if any(isinstance(c, ast.Call) and isinstance(c.func, ast.Name)
                       and c.func.id == "publish"
                       and any(isinstance(a, ast.Constant) and a.value == "candle"
                               for a in c.args) for n in node.body for c in ast.walk(n)):
                    five_minute_guard_lines.append(node.lineno)
    ttl = None
    state_key_evidence = {"write_key_dimensions": [], "timeframe_separated": None}
    state_file = directory / "assessment_state.py"
    state_present = state_file.is_file() and not state_file.is_symlink()
    if state_present:
        state_tree = ast.parse(state_file.read_text(encoding="utf-8"))
        state_key_evidence = _assessment_state_key_audit(state_tree)
        for node in state_tree.body:
            if isinstance(node, ast.Assign):
                if any(isinstance(target, ast.Name) and target.id == "_TTL"
                       for target in node.targets):
                    if isinstance(node.value, ast.Constant) and type(node.value.value) is int:
                        ttl = node.value.value
    return {
        "candle_cache_writer_lines": sorted(writes),
        "candle_publish_lines": sorted(candle_publish_lines),
        "five_minute_candle_publish_guard_lines": sorted(five_minute_guard_lines),
        "options_publish_lines": sorted(option_publish_lines),
        "assessment_state_source_present": state_present,
        "assessment_state_ttl_seconds": ttl,
        "assessment_state_key_evidence": state_key_evidence,
        "mapping_route_direct_in_server": (
            ("get", "/v2/option-underlying-status/{symbol}") in {
                (method, route) for method, route in _route_decorators(tree)
            }
        ),
        "runtime_evidence_verified": False,
        "production_changed": False,
    }


def _route_decorators(tree):
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                    and isinstance(dec.func.value, ast.Name)
                    and dec.func.value.id == "app" and dec.args
                    and isinstance(dec.args[0], ast.Constant)
                    and isinstance(dec.args[0].value, str)):
                yield dec.func.attr.lower(), dec.args[0].value


def audit(path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Expected regular non-symlink Oracle server.py")
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    routes = list(route_functions(tree))
    # AST expression strings are only source indicators, never running values.
    vals = _string_constants(routes[0]) if len(routes) == 1 else set()
    delegated = _delegated_assessment(tree, path.parent)
    evidence = _evidence_wiring(tree, path.parent)
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
        "delegated_assessment": delegated,
        "evidence_wiring": evidence,
        "effective_route_source_found": (
            len(routes) == 1 or
            (delegated["register_call_present"] and
             delegated["module_route_present"])
        ),
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
