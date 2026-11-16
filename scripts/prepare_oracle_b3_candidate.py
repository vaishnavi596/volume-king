#!/usr/bin/env python3
"""Prepare (NEVER apply) an Oracle B3 single-flight patch, pinned to operator SHA.

Reads server.py; writes a candidate to an explicit DIFFERENT path. No network,
imports of target, credentials, service actions or production writes.
"""
import argparse
import ast
import hashlib
from pathlib import Path

EXPECTED_SHA = "b26902b26bfd1b74a013f962f39f35f70725bd1820a61e040401925524ce1e9b"
LOCK_BLOCK = '''
    # B3: worker-local reentrant single-flight; recursive 3m/30m calls need RLock.
    from functools import wraps as _b3_wraps
    history_miss_locks = tuple(threading.RLock() for _ in range(32))

    def history_singleflight(handler):
        @_b3_wraps(handler)
        def guarded(body: DhanIntradayRequest,
                    x_botking_key: Optional[str] = Header(default=None)):
            if (not x_botking_key or not
                    hmac.compare_digest(x_botking_key.encode(), pairing_key.encode())):
                raise HTTPException(403, "Server access denied")
            lane = hash((body.symbol, body.interval)) % len(history_miss_locks)
            with history_miss_locks[lane]:
                # Existing handler rechecks validated 180s cache inside lane.
                return handler(body, x_botking_key=x_botking_key)
        return guarded

'''
CACHE_ANCHOR = '    # Historical candles are cached only after provider validation succeeds.\n'
ROUTE_ANCHOR = '    @app.post("/dhan/intraday")\n    def dhan_intraday('


def prepare(raw: bytes) -> bytes:
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
        raise ValueError("Oracle server.py SHA mismatch: refuse to patch")
    source = raw.decode("utf-8")
    if source.count(CACHE_ANCHOR) != 1 or source.count(ROUTE_ANCHOR) != 1:
        raise ValueError("Expected unique cache/route anchors not found")
    if "history_singleflight" in source or "history_miss_locks" in source:
        raise ValueError("Single-flight source already present: manual review required")
    if "import threading" not in source:
        raise ValueError("threading import not verified: manual review required")
    tree = ast.parse(source)
    routes = [
        node for node in ast.walk(tree)
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "dhan_intraday"
    ]
    if len(routes) != 1 or not any(
        isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
        and d.func.attr == "post" and d.args
        and isinstance(d.args[0], ast.Constant)
        and d.args[0].value == "/dhan/intraday"
        for d in routes[0].decorator_list
    ):
        raise ValueError("History route AST mismatch")
    # Keep existing Oracle cache/persistence/provider/429 paths byte-for-byte.
    source = source.replace(CACHE_ANCHOR, LOCK_BLOCK + CACHE_ANCHOR, 1)
    source = source.replace(ROUTE_ANCHOR,
                            '    @app.post("/dhan/intraday")\n'
                            '    @history_singleflight\n'
                            '    def dhan_intraday(', 1)
    ast.parse(source)
    return source.encode("utf-8")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--server", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.server.resolve() == args.output.resolve():
        raise SystemExit("Output MUST differ from production input")
    if args.output.exists() or args.output.is_symlink():
        raise SystemExit("Output already exists: refuse overwrite")
    if not args.server.is_file() or args.server.is_symlink():
        raise SystemExit("Source must be a regular non-symlink file")
    candidate = prepare(args.server.read_bytes())
    # Create-only, private permissions; never write into the production path.
    fd = args.output.open("xb")
    try:
        import os
        os.chmod(args.output, 0o600)
        fd.write(candidate)
    finally:
        fd.close()
    print("candidate_sha256=" + hashlib.sha256(candidate).hexdigest())
    print("candidate_only=true; deployed=false; requires independent review")


if __name__ == "__main__":
    main()
