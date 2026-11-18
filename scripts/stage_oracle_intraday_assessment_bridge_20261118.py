#!/usr/bin/env python3
"""Stage a SHA-pinned Oracle /dhan/intraday -> Assessment candle bridge.

PRODUCTION READ ONLY. Candidate is written under /tmp; deployment NOT permitted.
No imports of Oracle code, secret access, HTTP, broker calls or service restart.
"""
import ast
import hashlib
import json
import sys
import tempfile
from pathlib import Path

PRODUCTION = Path("/opt/bot-king-server/server.py")
EXPECTED_SHA = "c9ee8a8d1baa8ebea8efc41d3ee4c6b42aea48f4add65ab79b9518a9fcb27bac"
EXPECTED_RETURNS = (928, 966, 1001, 1042)
EXPECTED_KEYS = ("symbol", "source", "interval", "bars", "freshness", "live_orders_enabled")


def named_function(tree, name):
    matches = [n for n in ast.walk(tree)
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name == name]
    if len(matches) != 1:
        raise ValueError("FUNCTION_MISSING_OR_AMBIGUOUS")
    return matches[0]


def direct_calls(fn, name):
    return [n for n in ast.walk(fn) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name) and n.func.id == name]


def response_returns(fn):
    return sorted((n for n in ast.walk(fn) if isinstance(n, ast.Return)
                   and isinstance(n.value, ast.Dict)), key=lambda n: n.lineno)


def safe_publisher_scope(candle, publication):
    if not publication.args:
        raise ValueError("PUBLISH_SCOPE_MISSING")
    scope = publication.args[0]
    local = {a.arg for a in candle.args.posonlyargs + candle.args.args
             + candle.args.kwonlyargs}
    local |= {n.id for n in ast.walk(candle)
              if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Store)}
    referenced = {n.id for n in ast.walk(scope)
                  if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)}
    if referenced & (local | {"entry", "cached", "bars", "interval", "symbol", "body"}):
        raise ValueError("PUBLISH_SCOPE_NEEDS_EXPLICIT_MAPPING")
    if not isinstance(scope, (ast.Name, ast.Call, ast.Constant, ast.Attribute)):
        raise ValueError("PUBLISH_SCOPE_EXPRESSION_UNSUPPORTED")
    return ast.unparse(scope)


def stage_source(source):
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != EXPECTED_SHA:
        raise ValueError("SOURCE_SHA_MISMATCH")
    tree = ast.parse(source)
    route = named_function(tree, "dhan_intraday")
    candle = named_function(tree, "cached_candles")
    helper = named_function(tree, "_assessment_bars_completed")
    if helper.decorator_list:
        raise ValueError("COMPLETION_GUARD_DECORATOR_MISMATCH")
    returns = response_returns(route)
    if tuple(n.lineno for n in returns) != EXPECTED_RETURNS:
        raise ValueError("RETURN_LOCATIONS_CHANGED")
    if any(tuple(k.value if isinstance(k, ast.Constant) else None
                 for k in n.value.keys) != EXPECTED_KEYS for n in returns):
        raise ValueError("RETURN_SCHEMA_CHANGED")
    if direct_calls(route, "publish"):
        raise ValueError("INTRADAY_PUBLISH_ALREADY_PRESENT")
    publishers = direct_calls(candle, "publish")
    if len(publishers) != 1 or len(publishers[0].args) < 4:
        raise ValueError("CANONICAL_CANDLE_PUBLISH_CHANGED")
    call = publishers[0]
    if not any(isinstance(x, ast.Constant) and x.value == "candle"
               for x in call.args):
        raise ValueError("CANONICAL_CANDLE_KIND_CHANGED")
    if "timeframe" not in {x.arg for x in call.keywords}:
        raise ValueError("CANONICAL_TIMEFRAME_MISSING")
    scope_expression = safe_publisher_scope(candle, call)
    # A local import in cached_candles is not visible to dhan_intraday.
    # Reject the old helper's implicit global-name assumption. Do not use
    # broad exception suppression as evidence that the cache write works.
    def local_imported(fn, name):
        return any(
            isinstance(n, (ast.ImportFrom, ast.Import))
            and any((a.asname or a.name.split(".")[0]) == name
                    for a in n.names)
            for n in ast.walk(fn)
        )
    if (any(local_imported(candle, name) for name in ("publish", "current_scope"))
            and not all(local_imported(route, name)
                        for name in ("publish", "current_scope"))):
        raise ValueError("INTRADAY_PUBLISH_BINDINGS_UNAVAILABLE")
    # The real Oracle canonical candle publisher carries a five-field
    # Assessment payload. A wrapper that publishes only {"bars": rows}
    # would silently lose observed_at, interval, freshness and eligibility.
    # Never stage such a candidate until a source-compatible payload
    # normalization is independently mapped and regression-tested.
    canonical_payload = call.args[3]
    if not isinstance(canonical_payload, ast.Dict):
        raise ValueError("CANONICAL_PAYLOAD_SHAPE_UNSUPPORTED")
    canonical_keys = tuple(
        k.value if isinstance(k, ast.Constant) and isinstance(k.value, str)
        else None for k in canonical_payload.keys
    )
    if any(k is None for k in canonical_keys):
        raise ValueError("CANONICAL_PAYLOAD_KEYS_DYNAMIC")
    if tuple(canonical_keys) != ("bars",):
        raise ValueError("CANONICAL_PAYLOAD_PARITY_UNIMPLEMENTED")

    # Wrap all four existing response dictionaries, preserving their keys and values.
    lines = source.splitlines(keepends=True)
    offsets = [0]
    for line in lines:
        offsets.append(offsets[-1] + len(line))
    edits = []
    for ret in returns:
        value = ret.value
        start = offsets[value.lineno - 1] + value.col_offset
        end = offsets[value.end_lineno - 1] + value.end_col_offset
        edits.extend(((start, "_bk_publish_completed_intraday("), (end, ")")))
    for position, insert in sorted(edits, reverse=True):
        source = source[:position] + insert + source[position:]

    # Nested helper deliberately uses existing scope calculation and completion gate.
    first = route.body[0]
    insert_before = (first.end_lineno + 1 if isinstance(first, ast.Expr)
                     and isinstance(first.value, ast.Constant)
                     and isinstance(first.value.value, str)
                     else first.lineno)
    insertion = (
        '        def _bk_publish_completed_intraday(response):\n'
        '            """Do not alter the historical response or fetch extra Dhan data."""\n'
        '            if not isinstance(response, dict):\n'
        '                return response\n'
        '            rows = response.get("bars")\n'
        '            tf = str(response.get("interval"))\n'
        '            symbol = response.get("symbol")\n'
        '            if (response.get("source") != "dhan"\n'
        '                    or response.get("freshness") != "historical_unverified"\n'
        '                    or not isinstance(symbol, str) or not symbol\n'
        '                    or tf not in ("1", "3", "5", "1m", "3m", "5m")\n'
        '                    or not isinstance(rows, (list, tuple)) or len(rows) < 2):\n'
        '                return response\n'
        '            minutes = int(tf.removesuffix("m"))\n'
        '            try:\n'
        '                if _assessment_bars_completed(rows[-2:], minutes):\n'
        '                    publish(' + scope_expression +
        ', symbol, "candle", {"bars": rows}, timeframe=str(minutes) + "m")\n'
        '            except Exception:\n'
        '                # Assessment is informational; never blank a good chart.\n'
        '                pass\n'
        '            return response\n\n'
    )
    parts = source.splitlines(keepends=True)
    source = "".join(parts[:insert_before - 1]) + insertion + "".join(parts[insert_before - 1:])
    updated = ast.parse(source)
    patched = named_function(updated, "dhan_intraday")
    nested = named_function(patched, "_bk_publish_completed_intraday")
    if len(direct_calls(nested, "publish")) != 1:
        raise ValueError("PUBLISH_POSTCHECK_FAILED")
    if len(direct_calls(patched, "_bk_publish_completed_intraday")) != 4:
        raise ValueError("FOUR_RETURN_POSTCHECK_FAILED")
    return source


def main():
    result = {"audit": "BOT_KING_T09_INTRADAY_BRIDGE_STAGE",
              "production_changed": False, "server_restarted": False,
              "direct_dhan_requests": 0, "http_requests": 0, "orders_sent": 0,
              "deployment_approved": False}
    try:
        if not PRODUCTION.is_file() or PRODUCTION.is_symlink():
            raise ValueError("PRODUCTION_SOURCE_NOT_REGULAR")
        original = PRODUCTION.read_text(encoding="utf-8")
        candidate = stage_source(original)
        out = Path(tempfile.mkdtemp(prefix="botking-t09-candidate-", dir="/tmp"))
        out.chmod(0o700)
        target = out / "server.py"
        target.write_text(candidate, encoding="utf-8")
        target.chmod(0o600)
        result.update({"status": "STAGED_REVIEW_REQUIRED",
                       "candidate_path": str(target),
                       "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
                       "source_sha256": EXPECTED_SHA,
                       "verification": "AST_ONLY_NO_DEPLOY"})
    except (ValueError, OSError, SyntaxError, UnicodeError) as exc:
        result.update({"status": "HOLD_NO_STAGING",
                       "reason": str(exc) if isinstance(exc, ValueError)
                       else type(exc).__name__})
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] == "STAGED_REVIEW_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
