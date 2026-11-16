#!/usr/bin/env python3
"""Read-only AST preflight for the SHA-pinned Oracle route candidate.

Does not import or execute the server, read environment values, or print source.
A PASS means only static bindings are visible; runtime checks remain mandatory.
"""
import argparse
import ast
import hashlib
from pathlib import Path

REQUIRED = ("Header", "HTTPException", "hmac", "pairing_key")
EXPECTED_SHA = "c9577aafb00960a982e9782c9ab154ef2c944b39197740b53aac63d3cd81d625"


def inspect_source(raw: bytes) -> dict:
    sha = hashlib.sha256(raw).hexdigest()
    result = {"sha_matches": sha == EXPECTED_SHA, "factory_found": False,
              "bindings": {name: False for name in REQUIRED}, "static_pass": False}
    tree = ast.parse(raw.decode("utf-8"))
    factories = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and node.name == "create_app"]
    if len(factories) != 1:
        return result
    result["factory_found"] = True
    visible = set()
    def add_targets(target):
        if isinstance(target, ast.Name):
            visible.add(target.id)
        elif isinstance(target, (ast.Tuple, ast.List)):
            for item in target.elts:
                add_targets(item)
    # Only module bindings established before factory definition, and direct factory
    # bindings established before the snapshot insertion point, can qualify.
    # Later assignments must never produce a false PASS.
    factory = factories[0]
    anchors = [node for node in factory.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
               and any(isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                       and isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app"
                       and dec.func.attr == "get" and dec.args
                       and isinstance(dec.args[0], ast.Constant)
                       and dec.args[0].value == "/v2/snapshot" for dec in node.decorator_list)]
    if len(anchors) != 1:
        return result
    before_factory = [node for node in tree.body if node.lineno < factory.lineno]
    before_anchor = [node for node in factory.body if node.lineno < anchors[0].lineno]
    for node in before_factory + before_anchor:
        if isinstance(node, ast.Import):
            visible.update(alias.asname or alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            visible.update(alias.asname or alias.name for alias in node.names)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                add_targets(target)
        elif isinstance(node, (ast.AnnAssign, ast.NamedExpr)):
            add_targets(node.target)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            visible.add(node.name)
    visible.update(arg.arg for arg in factories[0].args.posonlyargs + factories[0].args.args
                   + factories[0].args.kwonlyargs)
    result["bindings"] = {name: name in visible for name in REQUIRED}
    result["static_pass"] = result["sha_matches"] and all(result["bindings"].values())
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=Path, required=True)
    args = parser.parse_args()
    if not args.server.is_file() or args.server.is_symlink():
        raise SystemExit("FAIL: source must be a regular non-symlink file")
    result = inspect_source(args.server.read_bytes())
    print("sha_matches=" + str(result["sha_matches"]).lower())
    print("factory_found=" + str(result["factory_found"]).lower())
    for name, found in result["bindings"].items():
        print("binding_" + name + "=" + ("present" if found else "unverified"))
    print("static_preflight=" + ("PASS" if result["static_pass"] else "HOLD"))
    print("runtime_verified=false; deployed=false")
    if not result["static_pass"]:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
