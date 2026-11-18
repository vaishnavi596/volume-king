#!/usr/bin/env python3
"""T09 v2: isolated, SHA-pinned Oracle candle->Assessment candidate.

Only writes an AST-checked /tmp candidate. Never loads production code,
contacts Dhan, restarts the service, or sends orders. DO NOT DEPLOY
without real Oracle source review and authorized integration validation.
"""
import ast
import hashlib
import json
import sys
import tempfile
from pathlib import Path

PRODUCTION = Path("/opt/bot-king-server/server.py")
EXPECTED_SHA = "c9ee8a8d1baa8ebea8efc41d3ee4c6b42aea48f4add65ab79b9518a9fcb27bac"
RECORD_LINES = (955, 1033)
PERSIST_LINES = (965, 1041)
PUBLISH_RETURN_LINES = (966, 1042)
ALL_RETURNS = (928, 966, 1001, 1042)
RETURN_KEYS = ("symbol", "source", "interval", "bars", "freshness",
               "live_orders_enabled")
CACHE_RECORD_KEYS = {"bars", "from_date", "to_date", "observed_at"}
CANONICAL_FIELDS = ("bars", "observed_at", "interval", "freshness", "signal_eligible")


def function(tree, name):
    found = [x for x in ast.walk(tree)
             if isinstance(x, (ast.FunctionDef, ast.AsyncFunctionDef))
             and x.name == name]
    if len(found) != 1:
        raise ValueError("FUNCTION_COUNT_" + name)
    return found[0]


def literal_keys(node):
    if not isinstance(node, ast.Dict):
        return ()
    return tuple(k.value if isinstance(k, ast.Constant) and isinstance(k.value, str)
                 else None for k in node.keys)


def direct_publish(fn):
    return [x for x in ast.walk(fn) if isinstance(x, ast.Call)
            and isinstance(x.func, ast.Name) and x.func.id == "publish"]


def text_splice(raw, edits):
    offsets = [0]
    for line in raw.splitlines(keepends=True):
        offsets.append(offsets[-1] + len(line))

    def position(lineno, col):
        if lineno < 1 or lineno >= len(offsets):
            raise ValueError("LINE_OUT_OF_RANGE")
        return offsets[lineno-1] + col

    spans = [(position(n.lineno, n.col_offset),
              position(n.end_lineno, n.end_col_offset), prefix, suffix)
             for n, prefix, suffix in edits]
    spans.sort(key=lambda t: t[0], reverse=True)
    for start, end, prefix, suffix in spans:
        raw = raw[:end] + suffix + raw[end:]
        raw = raw[:start] + prefix + raw[start:]
    return raw


def stage_source(source):
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != EXPECTED_SHA:
        raise ValueError("SOURCE_SHA_MISMATCH")
    tree = ast.parse(source)
    route = function(tree, "dhan_intraday")
    canonical = function(tree, "cached_candles")
    function(tree, "_assessment_bars_completed")
    pubs = direct_publish(canonical)
    if len(pubs) != 1 or len(pubs[0].args) < 4:
        raise ValueError("CANONICAL_PUBLISH_CHANGED")
    if literal_keys(pubs[0].args[3]) != CANONICAL_FIELDS:
        raise ValueError("CANONICAL_PAYLOAD_MISMATCH")
    if direct_publish(route):
        raise ValueError("INTRADAY_ALREADY_PUBLISHING")
    returns = sorted((n for n in ast.walk(route)
                      if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict)),
                     key=lambda x: x.lineno)
    if tuple(x.lineno for x in returns) != ALL_RETURNS:
        raise ValueError("RETURN_LINE_DRIFT")
    if any(literal_keys(x.value) != RETURN_KEYS for x in returns):
        raise ValueError("RETURN_SCHEMA_DRIFT")

    dicts = [n for n in ast.walk(route)
             if isinstance(n, ast.Dict) and n.lineno in RECORD_LINES
             and CACHE_RECORD_KEYS.issubset(set(literal_keys(n)))]
    if tuple(sorted(n.lineno for n in dicts)) != RECORD_LINES:
        raise ValueError("CACHE_RECORD_BINDING_UNPROVEN")
    for n in dicts:
        names = literal_keys(n)
        timestamp = n.values[names.index("observed_at")]
        if not (isinstance(timestamp, ast.Call) and
                isinstance(timestamp.func, ast.Attribute) and
                timestamp.func.attr == "isoformat"):
            raise ValueError("OBSERVATION_NOT_ISOFORMAT")
    persist = sorted(x.lineno for x in ast.walk(route) if isinstance(x, ast.Call)
                     and isinstance(x.func, ast.Name)
                     and x.func.id == "persist_candle_cache")
    if tuple(persist) != PERSIST_LINES:
        raise ValueError("PERSIST_BRANCH_DRIFT")
    if not (RECORD_LINES[0] < PERSIST_LINES[0] < PUBLISH_RETURN_LINES[0]
            and RECORD_LINES[1] < PERSIST_LINES[1] < PUBLISH_RETURN_LINES[1]):
        raise ValueError("CACHE_TO_RETURN_ORDER_DRIFT")

    edit_nodes = [(n, b"_bk_t09_capture(", b")") for n in dicts]
    edit_nodes += [(n.value, b"_bk_t09_publish(", b")")
                   for n in returns if n.lineno in PUBLISH_RETURN_LINES]
    patched = text_splice(source.encode("utf-8"), edit_nodes)
    # Insert two helpers at start of dhan_intraday body. Preserve all original
    # return schemas; cached and empty-data paths are deliberately untouched.
    helper = '''
        _bk_t09_records = []

        def _bk_t09_capture(entry):
            # Capture exactly the record being prepared for the existing cache.
            if isinstance(entry, dict):
                _bk_t09_records.append(entry)
            return entry

        def _bk_t09_publish(response):
            if not isinstance(response, dict) or not _bk_t09_records:
                return response
            import logging
            try:
                from .assessment_state import publish
            except ImportError:
                from assessment_state import publish
            try:
                from .assessment_scope import current_scope
            except ImportError:
                from assessment_scope import current_scope
            try:
                if (response.get("source") != "dhan"
                        or response.get("freshness") != "historical_unverified"):
                    return response
                symbol = response.get("symbol")
                tf = str(response.get("interval"))
                rows = response.get("bars")
                record = _bk_t09_records[-1]
                observed_at = record.get("observed_at")
                records = record.get("bars")
                if (not isinstance(symbol, str) or not symbol
                        or tf not in ("1m", "3m", "5m", "1", "3", "5")
                        or not isinstance(rows, (list, tuple)) or len(rows) < 2
                        or not isinstance(records, (list, tuple))
                        or len(records) != len(rows)
                        or not isinstance(observed_at, str)):
                    return response
                # No external clock or invented timestamp: original entry only.
                from datetime import datetime
                datetime.fromisoformat(observed_at.replace("Z", "+00:00"))
                if [list(x) for x in records] != [list(x) for x in rows]:
                    return response
                minutes = int(tf.removesuffix("m"))
                if not _assessment_bars_completed(rows[-2:], minutes):
                    return response
                timeframe = str(minutes) + "m"
                publish(current_scope(pairing_key), symbol, "candle", {
                    "bars": [list(x) for x in rows],
                    "observed_at": observed_at,
                    "interval": timeframe,
                    "freshness": "historical_unverified",
                    "signal_eligible": False,
                }, timeframe=timeframe)
            except Exception as exc:
                # Preserve healthy Dhan history while retaining an audit trail.
                logging.getLogger("botking.t09").warning(
                    "T09_ASSESSMENT_CACHE_PUBLISH_FAILED type=%s",
                    type(exc).__name__)
            return response

'''
    altered = ast.parse(patched.decode("utf-8"))
    patched_route = function(altered, "dhan_intraday")
    start = patched_route.body[0].lineno
    byte_lines = patched.splitlines(keepends=True)
    offset = sum(len(line) for line in byte_lines[:start - 1])
    patched = patched[:offset] + helper.encode("utf-8") + patched[offset:]
    final_tree = ast.parse(patched.decode("utf-8"))
    final = function(final_tree, "dhan_intraday")
    if len([n for n in ast.walk(final) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "_bk_t09_capture"]) != 2:
        raise ValueError("CAPTURE_POSTCHECK")
    if len([n for n in ast.walk(final) if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Name)
            and n.func.id == "_bk_t09_publish"]) != 2:
        raise ValueError("PUBLISH_POSTCHECK")
    # Exclude nested helper function returns from counts.
    top_returns = [x for x in ast.walk(final) if isinstance(x, ast.Return)
                   and isinstance(x.value, ast.Call)
                   and isinstance(x.value.func, ast.Name)
                   and x.value.func.id == "_bk_t09_publish"]
    if len(top_returns) != 2:
        raise ValueError("RESPONSE_POSTCHECK")
    return patched.decode("utf-8")


def main():
    result = {"audit": "BOT_KING_T09_CANONICAL_JOINT_STAGE",
              "production_changed": False, "server_restarted": False,
              "dhan_requests": 0, "orders_sent": 0,
              "runtime_verified": False, "deployment_approved": False}
    try:
        if not PRODUCTION.is_file() or PRODUCTION.is_symlink():
            raise ValueError("PRODUCTION_NOT_REGULAR")
        candidate = stage_source(PRODUCTION.read_text(encoding="utf-8"))
        out = Path(tempfile.mkdtemp(prefix="botking-t09-v2-", dir="/tmp"))
        out.chmod(0o700)
        destination = out / "server.py"
        destination.write_text(candidate, encoding="utf-8")
        destination.chmod(0o600)
        result.update({"status": "ISOLATED_CANDIDATE_REVIEW_REQUIRED",
                       "candidate_path": str(destination),
                       "candidate_sha256": hashlib.sha256(candidate.encode()).hexdigest(),
                       "source_sha256": EXPECTED_SHA,
                       "record_lines": RECORD_LINES,
                       "published_return_lines": PUBLISH_RETURN_LINES})
    except (ValueError, SyntaxError, OSError, UnicodeError) as exc:
        result.update({"status": "HOLD_NO_STAGING",
                       "reason": str(exc) if isinstance(exc, ValueError)
                       else type(exc).__name__})
    print(json.dumps(result, sort_keys=True, indent=2))
    return 0 if result["status"] == "ISOLATED_CANDIDATE_REVIEW_REQUIRED" else 2


if __name__ == "__main__":
    sys.exit(main())
