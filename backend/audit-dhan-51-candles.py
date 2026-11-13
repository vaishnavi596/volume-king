#!/usr/bin/env python3
"""Read-only, sequential Oracle audit of 51 mapped Dhan equity candle feeds.

Run on the Oracle host: python3 backend/audit-dhan-51-candles.py
Never prints credentials, prices, raw responses, or broker payloads.
Requests one symbol at a time and stops on rate limiting.
"""
import datetime as dt
import pathlib
import sys
import time
from importlib.util import module_from_spec, spec_from_file_location

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from server_feed import DHAN_VERIFIED_SYMBOLS

spec = spec_from_file_location("dhan_live_check", pathlib.Path(__file__).with_name("check-dhan-live.py"))
module = module_from_spec(spec)
spec.loader.exec_module(module)

SYMBOLS = sorted(DHAN_VERIFIED_SYMBOLS - {"NIFTY"})
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


def main():
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
    day = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30))).date() - dt.timedelta(days=1)
    while day.weekday() >= 5:
        day -= dt.timedelta(days=1)
    print("Dhan 51-equity 5m historical audit | day:", day, "| symbols:", len(SYMBOLS))
    counts = {"valid": 0, "empty": 0, "invalid": 0, "http_error": 0}
    for i, symbol in enumerate(SYMBOLS, 1):
        code, result = module.request("/dhan/intraday", key, {
            "symbol": symbol, "interval": 5,
            "from_date": day.isoformat(), "to_date": day.isoformat()})
        if code == 429:
            print(f"{i:02d}/{len(SYMBOLS)} {symbol}: HTTP 429 RATE_LIMIT; STOP")
            return 3
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
        counts[outcome] += 1
        print(f"{i:02d}/{len(SYMBOLS)} {symbol}: {outcome.upper()} HTTP {code} bars {len(bars) if isinstance(bars, list) else 'invalid'}")
        if i < len(SYMBOLS):
            time.sleep(1.2)
    print("TOTAL", counts, "| no order endpoints called | timestamps not verified live")
    return 0 if counts["valid"] == len(SYMBOLS) else 1


if __name__ == "__main__":
    sys.exit(main())
