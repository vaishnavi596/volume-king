#!/usr/bin/env python3
"""Create-only, SHA-pinned Oracle missing-route candidate; NEVER deploy automatically."""
import argparse
import ast
import hashlib
import os
from pathlib import Path

EXPECTED_SHA = "c9577aafb00960a982e9782c9ab154ef2c944b39197740b53aac63d3cd81d625"
ANCHOR = '    @app.get("/v2/snapshot")\n'
BLOCK = '''
    @app.get("/v2/server-readiness")
    def botking_readiness_safe(x_botking_key: Optional[str] = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        # No claim of active collection without a verified producer.
        return {"protocol": 2, "service": "BOT KING",
                "collector": {"configured_enabled": False, "status": "unverified",
                              "interval_seconds": None, "last_success_age_seconds": None,
                              "equity_quote_count": 0},
                "orders": {"broker_submission_allowed": False, "live_orders_enabled": False},
                "live_orders_enabled": False}

    @app.get("/v2/assessment/{symbol}")
    def botking_assessment_safe(symbol: str, x_botking_key: Optional[str] = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        if not symbol or len(symbol) > 40 or any(
                not (c.isascii() and (c.isalnum() or c in "-&")) for c in symbol):
            raise HTTPException(422, "Invalid assessment symbol")
        ids = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")
        return {"protocol": 2, "symbol": symbol, "source": "dhan",
                "collection_status": "not_configured", "freshness": "unverified",
                "assessment_filters": [
                    {"id": name, "status": "unavailable",
                     "reason": "Independent Oracle assessment not configured"}
                    for name in ids],
                "factors": {name: {"status": "unavailable", "bullish": None, "bearish": None}
                            for name in ("news", "futures", "options", "candle")},
                "bullish_score": None, "bearish_score": None,
                "signal_eligible": False, "live_orders_enabled": False}

'''

def routes(tree):
    found = set()
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for dec in node.decorator_list:
            if (isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute)
                    and isinstance(dec.func.value, ast.Name) and dec.func.value.id == "app"
                    and dec.args and isinstance(dec.args[0], ast.Constant)):
                found.add((dec.func.attr.lower(), dec.args[0].value))
    return found

def prepare(raw):
    if hashlib.sha256(raw).hexdigest() != EXPECTED_SHA:
        raise ValueError("Oracle source SHA mismatch; refuse patch")
    source = raw.decode("utf-8")
    present = routes(ast.parse(source))
    if ("get", "/v2/snapshot") not in present:
        raise ValueError("Snapshot anchor route missing")
    if any(("get", path) in present for path in
           ("/v2/server-readiness", "/v2/assessment/{symbol}")):
        raise ValueError("Target route already present; refuse duplicate")
    # Oracle's customized server delegates both existing routes to modules.
    # A decorator-only scan misses those registrations. Never insert
    # competing placeholder routes on top of a working delegated handler.
    registered = {n.func.id for n in ast.walk(ast.parse(source))
                  if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
                  and n.func.id in ("register_assessment_routes",
                                    "register_readiness_routes")}
    if registered:
        raise ValueError("Delegated assessment/readiness route already registered; refuse duplicate")
    if source.count(ANCHOR) != 1:
        raise ValueError("Unique snapshot decorator anchor not found")
    # Ensure the insertion lands inside the active app factory, not another scope.
    factories = [n for n in ast.parse(source).body
                 if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                 and n.name == "create_app"]
    if len(factories) != 1 or not any(
        isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
        and any(isinstance(d, ast.Call) and isinstance(d.func, ast.Attribute)
                and isinstance(d.func.value, ast.Name) and d.func.value.id == "app"
                and d.func.attr == "get" and d.args
                and isinstance(d.args[0], ast.Constant)
                and d.args[0].value == "/v2/snapshot"
                for d in n.decorator_list)
        for n in factories[0].body
    ):
        raise ValueError("Snapshot route must be directly inside create_app")
    candidate = source.replace(ANCHOR, BLOCK + ANCHOR, 1)
    parsed = ast.parse(candidate)
    for path in ("/v2/server-readiness", "/v2/assessment/{symbol}"):
        if ("get", path) not in routes(parsed):
            raise ValueError("Candidate route verification failed")
    return candidate.encode("utf-8")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--server", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.server.resolve() == args.output.resolve() or args.output.exists() or args.output.is_symlink():
        raise SystemExit("Output must be new and separate from production")
    if not args.server.is_file() or args.server.is_symlink():
        raise SystemExit("Source must be regular non-symlink file")
    candidate = prepare(args.server.read_bytes())
    fd = os.open(args.output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as output:
        output.write(candidate)
    print("candidate_sha256=" + hashlib.sha256(candidate).hexdigest())
    print("candidate_only=true; deployed=false; filters_functional=false")

if __name__ == "__main__":
    main()
