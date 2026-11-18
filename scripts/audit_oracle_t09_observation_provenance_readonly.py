#!/usr/bin/env python3
"""Oracle T09 cache observation provenance audit — SHA locked and read-only.

Parses source only. Never imports project modules, invokes network, reads
environment variables, prints source expressions, or changes application files.
"""
import ast
import hashlib
import json
from pathlib import Path

SERVER = Path("/opt/bot-king-server/server.py")
SERVER_SHA256 = "c9ee8a8d1baa8ebea8efc41d3ee4c6b42aea48f4add65ab79b9518a9fcb27bac"
CANDIDATE = Path("/tmp/botking-t09-candidate-2sv4fdqt/server.py")
CANDIDATE_SHA256 = "53f8b74522ad9c61bfee7059a4735e961dcaec298deb7a4bbdaf7fc9965d0a6e"
FIELDS = {"observed_at", "bars", "interval", "freshness", "signal_eligible"}
CACHE_FN = ("persist_candle_cache", "cached_candles", "dhan_intraday")


def named_function(tree, name):
    found = [n for n in ast.walk(tree)
             if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
             and n.name == name]
    if len(found) != 1:
        raise ValueError("FUNCTION_COUNT_" + name)
    return found[0]


def scan_function(fn):
    def expr_type(value):
        if isinstance(value, ast.Constant):
            if isinstance(value.value, bool):
                return "literal_bool_" + str(value.value).lower()
            if isinstance(value.value, str):
                return "literal_string"
        return type(value).__name__

    records = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Dict):
            for key, value in zip(n.keys, n.values):
                if isinstance(key, ast.Constant) and key.value in FIELDS:
                    records.append({"line": n.lineno, "field": key.value,
                                    "operation": "dict_value",
                                    "expression": expr_type(value)})
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute):
            if n.func.attr in {"get", "pop", "setdefault"} and n.args:
                first = n.args[0]
                if isinstance(first, ast.Constant) and first.value in FIELDS:
                    records.append({"line": n.lineno, "field": first.value,
                                    "operation": "lookup_" + n.func.attr,
                                    "receiver": type(n.func.value).__name__})
        if isinstance(n, ast.Assign):
            for target in n.targets:
                if isinstance(target, ast.Subscript) and isinstance(target.slice, ast.Constant):
                    if target.slice.value in FIELDS:
                        records.append({"line": n.lineno, "field": target.slice.value,
                                        "operation": "subscript_assignment",
                                        "expression": expr_type(n.value)})
    return sorted(records, key=lambda x: (x["line"], x["field"], x["operation"]))


def audit(root=SERVER, candidate=CANDIDATE, source_sha=SERVER_SHA256,
          candidate_sha=CANDIDATE_SHA256):
    for name, path, expected in (("server", root, source_sha),
                                  ("candidate", candidate, candidate_sha)):
        if not path.is_file() or path.is_symlink():
            raise ValueError(name.upper() + "_MISSING_OR_SYMLINK")
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != expected:
            raise ValueError(name.upper() + "_SHA_MISMATCH")
    tree = ast.parse(root.read_text(encoding="utf-8"))
    staged_tree = ast.parse(candidate.read_text(encoding="utf-8"))
    functions = {name: scan_function(named_function(tree, name)) for name in CACHE_FN}
    helper = named_function(staged_tree, "_bk_publish_completed_intraday")
    functions["staged_intraday_helper"] = scan_function(helper)
    return {"audit": "BOT_KING_T09_OBSERVATION_PROVENANCE",
            "status": "SOURCE_ONLY_PASS", "sha_verified": True,
            "production_changed": False, "server_restarted": False,
            "http_requests": 0, "dhan_requests": 0, "orders_sent": 0,
            "runtime_verified": False, "deployment_approved": False,
            "function_field_operations": functions,
            "decision": "NO_DEPLOY_REQUIRE_OBSERVED_AT_AND_KEY_PARITY"}


def main():
    try:
        result = audit()
    except (ValueError, OSError, SyntaxError, UnicodeError) as exc:
        result = {"audit": "BOT_KING_T09_OBSERVATION_PROVENANCE",
                  "status": "HOLD", "reason": str(exc) if isinstance(exc, ValueError)
                  else type(exc).__name__, "production_changed": False,
                  "http_requests": 0, "dhan_requests": 0, "orders_sent": 0,
                  "deployment_approved": False}
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "SOURCE_ONLY_PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
