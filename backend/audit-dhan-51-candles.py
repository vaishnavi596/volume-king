#!/usr/bin/env python3
"""Read-only, sequential Oracle audit of 51 mapped Dhan equity candle feeds.

Run on Oracle: python3 backend/audit-dhan-51-candles.py
Full coverage: add --all-symbols --date YYYY-MM-DD for a known past trading day.
Never prints credentials, prices, raw responses, or broker payloads.
Requests one symbol at a time and stops on rate limiting.
"""
import argparse
import datetime as dt
import pathlib
import sys
import time
from importlib.util import module_from_spec, spec_from_file_location

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import ast

# Extract the literal allowlist without importing the Android feed adapter,
# which depends on optional app-only modules absent on the Oracle host.
source = (ROOT / "src" / "server_feed.py").read_text(encoding="utf-8")
tree = ast.parse(source, filename="server_feed.py")
assignments = {
    target.id: node.value for node in tree.body if isinstance(node, ast.Assign)
    for target in node.targets if isinstance(target, ast.Name)
}
value = assignments.get("DHAN_VERIFIED_SYMBOLS")
if not (isinstance(value, ast.BinOp) and isinstance(value.op, ast.BitOr)
        and isinstance(value.left, ast.Name)
        and value.left.id == "DHAN_VERIFIED_EQUITY_SYMBOLS"
        and isinstance(value.right, ast.Name)
        and value.right.id == "DHAN_VERIFIED_INDEX_SYMBOLS"):
    raise RuntimeError("Unexpected Dhan 51+3 symbol union expression")

def literal_roster(name):
    expression = assignments.get(name)
    if not (isinstance(expression, ast.Call) and isinstance(expression.func, ast.Name)
            and expression.func.id == "frozenset" and len(expression.args) == 1
            and not expression.keywords):
        raise RuntimeError("Unexpected Dhan roster expression: " + name)
    result = frozenset(ast.literal_eval(expression.args[0]))
    if not result or not all(isinstance(x, str) and x for x in result):
        raise RuntimeError("Invalid Dhan roster: " + name)
    return result

EQUITY_SYMBOLS = literal_roster("DHAN_VERIFIED_EQUITY_SYMBOLS")
INDEX_SYMBOLS = literal_roster("DHAN_VERIFIED_INDEX_SYMBOLS")
if len(EQUITY_SYMBOLS) != 51 or len(INDEX_SYMBOLS) != 3 or EQUITY_SYMBOLS & INDEX_SYMBOLS:
    raise RuntimeError("Invalid Dhan disjoint 51+3 roster")
DHAN_VERIFIED_SYMBOLS = EQUITY_SYMBOLS | INDEX_SYMBOLS

spec = spec_from_file_location("dhan_live_check", pathlib.Path(__file__).with_name("check-dhan-live.py"))
module = module_from_spec(spec)
spec.loader.exec_module(module)



def audit_symbols(all_symbols=False):
    return sorted(DHAN_VERIFIED_SYMBOLS if all_symbols else DHAN_VERIFIED_SYMBOLS - INDEX_SYMBOLS)

SYMBOLS = audit_symbols()
from scanner_engine import analyze, DEFAULT_FILTERS
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def bars_match_requested_day(bars, day):
    """A structurally valid but cached/wrong-session response is not an audit pass."""
    if not isinstance(bars, list) or len(bars) < 30:
        return False
    try:
        return all(
            dt.datetime.fromtimestamp(row[0], IST).date() == day
            and dt.time(9, 15) <= dt.datetime.fromtimestamp(row[0], IST).time() < dt.time(15, 30)
            for row in bars
        )
    except (ValueError, OverflowError, OSError, TypeError, IndexError, KeyError):
        return False


def main(argv=None):
    parser = argparse.ArgumentParser(description="Read-only candle and filter audit; no orders")
    parser.add_argument("--all-symbols", action="store_true", help="Include all 51 equities and 3 indices")
    parser.add_argument("--date", type=dt.date.fromisoformat, help="Known completed trading day, YYYY-MM-DD")
    args = parser.parse_args(argv)
    symbols = audit_symbols(args.all_symbols)
    today = dt.datetime.now(IST).date()
    if args.date is not None and args.date >= today:
        parser.error("Choose a completed past trading day; holiday calendar is not verified")
    try:
        key = module.KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        print("Pairing key unavailable; no requests made")
        return 2
    if not 32 <= len(key) <= 512 or any(ord(ch) < 33 or ord(ch) > 126 for ch in key):
        print("Invalid pairing key format; no requests made")
        return 2
    code, status = module.request("/dhan/status", key)
    if (code != 200 or not isinstance(status, dict)
            or status.get("authenticated") is not True
            or status.get("market_data_configured") is not True
            or status.get("live_orders_enabled") is not False):
        print("Dhan read-only session unavailable; no candle requests made")
        return 2
    # Previous weekday avoids partial intraday session and uses a bounded window.
    day = args.date or today - dt.timedelta(days=1)
    if args.date is None:
        while day.weekday() >= 5:
            day -= dt.timedelta(days=1)
    print("Dhan 5m historical candle/filter audit | day:", day, "| symbols:", len(symbols))
    print("Holiday calendar not verified; empty data is not proof of a mapping error")
    counts = {"valid": 0, "empty": 0, "invalid": 0, "http_error": 0}
    for i, symbol in enumerate(symbols, 1):
        code, result = module.request("/dhan/intraday", key, {
            "symbol": symbol, "interval": 5,
            "from_date": day.isoformat(), "to_date": day.isoformat()})
        if code == 429:
            print(f"{i:02d}/{len(symbols)} {symbol}: HTTP 429 RATE_LIMIT; STOP")
            return 3
        if code in (401, 403):
            print(f"{i:02d}/{len(symbols)} {symbol}: HTTP {code} AUTHORIZATION_FAILURE; STOP")
            return 2
        if code == 0:
            print(f"{i:02d}/{len(symbols)} {symbol}: TRANSPORT_FAILURE; STOP")
            return 2
        bars = result.get("bars") if isinstance(result, dict) else None
        if code != 200:
            outcome = "http_error"
        elif not isinstance(bars, list) or not bars:
            outcome = "empty"
        elif (result.get("source") == "dhan"
              and result.get("symbol") == symbol
              and result.get("live_orders_enabled") is False
              and module.valid_candle_bars(code, bars)
              and bars_match_requested_day(bars, day)):
            outcome = "valid"
        else:
            outcome = "invalid"
        filter_count = 0
        available_filters = 0
        bias = "UNAVAILABLE"
        if outcome == "valid":
            analysis = analyze(bars, DEFAULT_FILTERS, "5m")
            filter_count = len(analysis.get("votes") or [])
            available_filters = sum(v.get("vote") is not None for v in analysis.get("votes", []))
            bias = analysis.get("bias", "WAIT")
            if filter_count != len(DEFAULT_FILTERS) or analysis.get("timestamp") is None:
                outcome = "invalid"
        counts[outcome] += 1
        print(f"{i:02d}/{len(symbols)} {symbol}: {outcome.upper()} HTTP {code} bars {len(bars) if isinstance(bars, list) else 'invalid'} filters {filter_count}/{len(DEFAULT_FILTERS)} available {available_filters} unavailable {filter_count-available_filters} bias {bias}")
        if i < len(symbols):
            time.sleep(1.5)
    print("TOTAL", counts, "| no order endpoints called | timestamps not verified live")
    return 0 if counts["valid"] == len(symbols) else 1


if __name__ == "__main__":
    sys.exit(main())
