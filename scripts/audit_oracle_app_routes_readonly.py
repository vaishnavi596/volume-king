#!/usr/bin/env python3
"""Read-only BOT KING app/server API route parity probe for Oracle operators.

Inspects only Python syntax and known route decorators, NOT dotenv, OAuth,
pairing secrets, network, auth headers, broker APIs or process restarts.
A route in a source file is NOT proof it is running in Oracle's live process.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

EXPECTED = {
    ("/v2/snapshot", "GET"): "equity cache",
    ("/dhan/ltp-batch", "POST"): "bounded equity recovery",
    ("/dhan/index-ltp-batch", "POST"): "three index quote",
    ("/dhan/selected-ltp-batch", "POST"): "selected watchlist quote",
    ("/dhan/intraday", "POST"): "historical candle",
    ("/dhan/option-expiries", "POST"): "option expiry list",
    ("/dhan/option-chain", "POST"): "selected chain",
    ("/v2/server-readiness", "GET"): "collector safety/readiness",
    ("/v2/assessment/{symbol}", "GET"): "four-factor WAIT/assessment",
}


def route_decorators(source: str):
    tree = ast.parse(source, mode="exec")
    result = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            fn = decorator.func
            if not (isinstance(fn, ast.Attribute) and isinstance(fn.value, ast.Name)
                    and fn.value.id == "app" and fn.attr.lower() in {"get", "post"}):
                continue
            if len(decorator.args) >= 1 and isinstance(decorator.args[0], ast.Constant):
                uri = decorator.args[0].value
                if isinstance(uri, str):
                    result.add((uri, fn.attr.upper()))
    return result


def audit(path: Path):
    if not path.is_file() or path.is_symlink():
        raise ValueError("Expected a regular non-symlink server.py")
    data = path.read_bytes()
    # No echo of source, env values or secrets.
    found = route_decorators(data.decode("utf-8"))
    checks = [
        {"route": url, "method": method, "purpose": purpose,
         "source_present": (url, method) in found}
        for (url, method), purpose in EXPECTED.items()
    ]
    return {
        "source_file": str(path),
        "source_sha256": hashlib.sha256(data).hexdigest(),
        "syntax": "PASS",
        "expected_routes": len(EXPECTED),
        "source_present": sum(x["source_present"] for x in checks),
        "source_missing": [x["route"] for x in checks if not x["source_present"]],
        "route_checks": checks,
        "runtime_routes_verified": False,
        "collector_enabled_verified": False,
        "protected_quotes_verified": False,
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
