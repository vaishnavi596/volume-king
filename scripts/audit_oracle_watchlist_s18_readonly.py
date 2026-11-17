#!/usr/bin/env python3
"""Read-only AST inspection of deployed Oracle S18 global WatchlistStore guards.

Does NOT import or execute the target, read saved watchlist JSON, access keys,
call HTTP/Dhan, or modify deployment. Source guards alone are NOT runtime proof.
"""
import argparse
import ast
import hashlib
import json
from pathlib import Path

DUPLICATE_MESSAGE = "Symbol already belongs to another watchlist"
LIMIT_MESSAGE = "Global limit: 70 symbols across all watchlists"


def audit(path: Path):
    path = Path(path)
    if not path.is_file() or path.is_symlink():
        raise ValueError("Expected regular non-symlink Oracle watchlist_store.py")
    raw = path.read_bytes()
    tree = ast.parse(raw.decode("utf-8"))
    classes = [node for node in ast.walk(tree)
               if isinstance(node, ast.ClassDef) and node.name == "WatchlistStore"]
    methods = ([node for node in classes[0].body
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == "replace"] if len(classes) == 1 else [])
    method = methods[0] if len(methods) == 1 else None
    constants = {node.value for node in ast.walk(method)
                 if isinstance(node, ast.Constant) and isinstance(node.value, str)} if method else set()
    identifiers = {node.id for node in ast.walk(method)
                   if isinstance(node, ast.Name)} if method else set()
    # These are source-signature diagnostics, NOT proof that guards enforce
    # all conditions on every runtime path. Fail closed on unfamiliar layouts.
    duplicate_source_signature = (
        DUPLICATE_MESSAGE in constants
        and {"other_symbols", "duplicated", "validated"} <= identifiers)
    global_limit_source_signature = (
        LIMIT_MESSAGE in constants
        and {"proposed_total", "previous_total", "other_symbols"} <= identifiers
        and any(isinstance(n, ast.Constant) and type(n.value) is int and n.value == 70
                for n in ast.walk(method)) if method else False)
    return {
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "syntax": "PASS",
        "watchlist_store_class_count": len(classes),
        "replace_method_count": len(methods),
        "cross_list_duplicate_source_signature": duplicate_source_signature,
        "global_70_source_signature": global_limit_source_signature,
        "runtime_enforcement_verified": False,
        "saved_watchlists_inspected": False,
        "production_changed": False,
        "dhan_requests_made": 0,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path,
                        default=Path("/opt/bot-king-server/watchlist_store.py"))
    args = parser.parse_args()
    print(json.dumps(audit(args.source), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
