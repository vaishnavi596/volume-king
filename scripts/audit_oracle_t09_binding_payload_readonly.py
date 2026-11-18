#!/usr/bin/env python3
"""Read-only, SHA-pinned Oracle T09 binding, candle and cache-key audit.

No runtime imports, HTTP, provider calls, secrets, application invocation,
file writes or service restarts. Reports AST shapes, not private values.
"""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path("/opt/bot-king-server")
SOURCE_HASHES = {
    "server.py": "c9ee8a8d1baa8ebea8efc41d3ee4c6b42aea48f4add65ab79b9518a9fcb27bac",
    "assessment_state.py": "ea2db1787be5cddc1ff2235db6592c7858519fc97b18d8c65c011ef9c7a3e3d2",
    "assessment_api.py": "f421292725adadd825cbfa2a2a14f358aa6d07f29e3d71c0aa073d4b2827a2a5",
}
CANDIDATE = Path("/tmp/botking-t09-candidate-2sv4fdqt/server.py")
CANDIDATE_HASH = "53f8b74522ad9c61bfee7059a4735e961dcaec298deb7a4bbdaf7fc9965d0a6e"
WATCHED = {"publish", "current_scope", "_assessment_bars_completed"}


def function(tree, name):
    matches = [n for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == name]
    if len(matches) != 1:
        raise ValueError("FUNCTION_COUNT_MISMATCH_" + name)
    return matches[0]


def call_name(fn):
    if isinstance(fn, ast.Name):
        return fn.id
    if isinstance(fn, ast.Attribute):
        return fn.attr
    return None


def binding_info(tree, function_name):
    """Conservatively report name resolution and direct assignment scope."""
    target = function(tree, function_name)
    ancestry = []

    def visit(node, parents):
        if node is target:
            ancestry.extend(parents)
            return
        for child in ast.iter_child_nodes(node):
            visit(child, parents + [node])

    visit(tree, [])
    visible = []
    for n in ancestry + [target]:
        if isinstance(n, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef)):
            scope_names = set()
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                scope_names.update(a.arg for a in n.args.posonlyargs + n.args.args + n.args.kwonlyargs)
            for sub in n.body:
                if isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    scope_names.add(sub.name)
                elif isinstance(sub, (ast.Import, ast.ImportFrom)):
                    for alias in sub.names:
                        scope_names.add(alias.asname or alias.name.split(".")[0])
                elif isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        if isinstance(t, ast.Name):
                            scope_names.add(t.id)
                elif isinstance(sub, ast.AnnAssign) and isinstance(sub.target, ast.Name):
                    scope_names.add(sub.target.id)
            visible.append({"scope": "module" if isinstance(n, ast.Module) else n.name,
                            "defines": sorted(WATCHED & scope_names)})
    usages = [x for x in ast.walk(target) if isinstance(x, ast.Call)
              and call_name(x.func) in WATCHED]
    return {"function_line": target.lineno, "visible_bindings": visible,
            "watched_calls": sorted([
                {"name": call_name(x.func), "line": x.lineno}
                for x in usages], key=lambda x: x["line"])}


def shape(node):
    if isinstance(node, ast.Dict):
        return {"kind": "dict", "keys": [k.value if isinstance(k, ast.Constant) and isinstance(k.value, str)
                                        else "computed" for k in node.keys]}
    if isinstance(node, ast.ListComp):
        return {"kind": "list_comp", "elt_type": type(node.elt).__name__,
                "call_names": sorted({call_name(x.func) for x in ast.walk(node)
                                      if isinstance(x, ast.Call) and call_name(x.func)})}
    if isinstance(node, ast.List):
        return {"kind": "list", "elements": len(node.elts)}
    if isinstance(node, ast.Name):
        return {"kind": "name", "name": node.id}
    if isinstance(node, ast.Call):
        return {"kind": "call", "callee": call_name(node.func)}
    if isinstance(node, ast.Subscript):
        return {"kind": "subscript", "base": type(node.value).__name__}
    return {"kind": type(node).__name__}


def state_keys(tree, func_name):
    fn = function(tree, func_name)
    # Never dump source expressions: report structural variable names and
    # indexing count only. Nested comprehensions are still examined.
    accesses = []
    for x in ast.walk(fn):
        if isinstance(x, ast.Subscript):
            accesses.append({"line": x.lineno, "shape": shape(x),
                             "names": sorted({n.id for n in ast.walk(x)
                                              if isinstance(n, ast.Name)
                                              and n.id in {"scope","symbol","kind","timeframe","expiry","key"}})})
    return {"line": fn.lineno, "key_subscripts": accesses[:18]}


def inspect(root=ROOT, candidate=CANDIDATE, expected=SOURCE_HASHES,
            candidate_hash=CANDIDATE_HASH):
    trees = {}
    for name, sha in expected.items():
        p = root / name
        if not p.is_file() or p.is_symlink():
            raise ValueError("SOURCE_MISSING_OR_SYMLINK_" + name)
        raw = p.read_bytes()
        if hashlib.sha256(raw).hexdigest() != sha:
            raise ValueError("SOURCE_SHA_MISMATCH_" + name)
        trees[name] = ast.parse(raw.decode("utf-8"))
    if not candidate.is_file() or candidate.is_symlink():
        raise ValueError("CANDIDATE_MISSING_OR_SYMLINK")
    raw = candidate.read_bytes()
    if hashlib.sha256(raw).hexdigest() != candidate_hash:
        raise ValueError("CANDIDATE_SHA_MISMATCH")
    staged = ast.parse(raw.decode("utf-8"))
    server = trees["server.py"]
    cached = function(server, "cached_candles")
    route = function(server, "dhan_intraday")
    cpubl = [x for x in ast.walk(cached) if isinstance(x, ast.Call) and call_name(x.func) == "publish"]
    helper = function(staged, "_bk_publish_completed_intraday")
    hp = [x for x in ast.walk(helper) if isinstance(x, ast.Call) and call_name(x.func) == "publish"]
    if len(cpubl) != 1 or len(hp) != 1:
        raise ValueError("PUBLISH_CALL_COUNT")
    rows = []
    for n in ast.walk(route):
        if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict):
            vals = {}
            for key, val in zip(n.value.keys, n.value.values):
                if isinstance(key, ast.Constant) and key.value in ("bars", "freshness", "interval"):
                    vals[key.value] = shape(val)
            rows.append({"line": n.lineno, "fields": vals})
    state = trees["assessment_state.py"]
    return {
        "audit": "BOT_KING_T09_BINDING_AND_PAYLOAD_REVIEW",
        "source_sha_verified": True,
        "candidate_sha_verified": True,
        "production_changed": False,
        "http_requests": 0, "dhan_requests": 0, "orders_sent": 0,
        "binding": {
            "cached_candles": binding_info(server, "cached_candles"),
            "dhan_intraday": binding_info(server, "dhan_intraday"),
            "candidate_helper": binding_info(staged, "_bk_publish_completed_intraday")
        },
        "payload": {
            "canonical": shape(cpubl[0].args[3]) if len(cpubl[0].args) > 3 else {"kind": "missing"},
            "staged": shape(hp[0].args[3]) if len(hp[0].args) > 3 else {"kind": "missing"},
            "original_return_shapes": sorted(rows, key=lambda x: x["line"]),
        },
        "state_keys": {"publish": state_keys(state, "publish"),
                       "read": state_keys(state, "read")},
        "deployment_approved": False, "runtime_verified": False,
        "status": "SOURCE_INSPECTION_ONLY"
    }


def main():
    try:
        result = inspect()
    except (ValueError, OSError, UnicodeError, SyntaxError) as exc:
        result = {"audit": "BOT_KING_T09_BINDING_AND_PAYLOAD_REVIEW",
                  "status": "HOLD", "reason": str(exc) if isinstance(exc, ValueError)
                  else type(exc).__name__,
                  "production_changed": False, "http_requests": 0,
                  "dhan_requests": 0, "orders_sent": 0,
                  "deployment_approved": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "SOURCE_INSPECTION_ONLY" else 2


if __name__ == "__main__":
    raise SystemExit(main())
