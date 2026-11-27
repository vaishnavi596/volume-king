#!/usr/bin/env python3
"""BOT KING Clone: server-side READ-ONLY signal runner (paper/analysis only).

Runs on Oracle next to the Clone gateway and keeps working when no phone is
connected. Every minute (regular NSE hours) it asks the LOCAL gateway for the
three index quotes and 1m/5m candles, qualifies the candles with the same
rules as the phone (v3_live_candle_bridge) and runs the same scanner filters.
Result is written atomically to a private JSON file. No orders, no broker
write endpoint, no credentials printed. Standard library only (Python 3.9).
"""
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scanner_engine import analyze, DEFAULT_FILTERS  # noqa: E402
from v3_live_candle_bridge import completed_live_history  # noqa: E402
from v3_equity_session_calendar import regular_equity_hours  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
GATEWAY = os.environ.get("BOTKING_SIGNAL_GATEWAY", "http://127.0.0.1:8002")
SSK_FILE = Path(os.environ.get("BOTKING_SIGNAL_SSK", "/home/opc/botking-clone-v2-private/ssk"))
OUT_FILE = Path(os.environ.get("BOTKING_SIGNAL_OUT", "/home/opc/botking-clone-v2-private/signals-latest.json"))
SYMBOLS = ("NIFTY", "BANKNIFTY", "SENSEX")
FRAMES = (("1m", 1), ("5m", 5))


def post(path, body, key, timeout=25):
    req = urllib.request.Request(
        GATEWAY + path, data=json.dumps(body).encode(), method="POST",
        headers={"X-BotKing-Key": key, "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(req, timeout=timeout) as resp:
        return json.loads(resp.read(5_000_000))


def with_integrity(response):
    """Same transport-digest check the phone client performs."""
    digest = response.get("normalized_bars_sha256")
    bars = response.get("bars")
    if digest is None or not isinstance(bars, list):
        response["normalized_transport_integrity"] = "NOT_PROVIDED"
        return response
    expected = hashlib.sha256(json.dumps(
        bars, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
    response["normalized_transport_integrity"] = "SHA256_MATCH" if digest == expected else "MISMATCH"
    return response


def evaluate(symbol, frame, response, quote_item, now):
    """Pure function: one symbol/timeframe -> signal row (no I/O)."""
    row = {"state": "UNQUALIFIED", "bias": None, "bullish": None, "bearish": None,
           "directional": 0, "reason": ""}
    if not isinstance(response, dict) or not isinstance(quote_item, dict):
        row["reason"] = "missing candles or quote"
        return row
    stamp = quote_item.get("exchange_trade_timestamp")
    quote = {"source": "Dhan", "cached": False, "symbol": symbol,
             "timestamp_origin": quote_item.get("timestamp_origin"),
             "quote_timestamp": stamp}
    if isinstance(stamp, (int, float)):
        row["quote_age_s"] = round(now - stamp, 1)
    bars = response.get("bars")
    qualified = completed_live_history(response, bars, quote, symbol=symbol,
                                       timeframe=frame, now=now)
    if qualified is None:
        row["reason"] = "candles/quote did not meet live-qualification rules"
        return row
    result = analyze(qualified, selected=list(DEFAULT_FILTERS), timeframe=frame)
    votes = [v for v in result.get("votes", []) if v.get("vote") in (-1, 1)]
    bulls = sum(v["vote"] == 1 for v in votes)
    bears = sum(v["vote"] == -1 for v in votes)
    total = bulls + bears
    row.update(state="LIVE_VERIFIED", directional=total,
               last_candle_ist=datetime.fromtimestamp(qualified[-1][0], IST).strftime("%H:%M"),
               reason=result.get("reason", ""))
    if total >= 3:
        pct = round(100 * bulls / total)
        row.update(bullish=pct, bearish=100 - pct,
                   bias="BULLISH" if bulls > bears else "BEARISH" if bears > bulls else "NEUTRAL")
    else:
        row["reason"] = "fewer than 3 directional votes"
    return row


def atomic_write(path, text):
    fd, tmp = tempfile.mkstemp(prefix=".signals-", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, path)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def cycle(key, now, minute_index, previous):
    out = {"generated_utc": datetime.fromtimestamp(now, timezone.utc).isoformat(),
           "market_open": bool(regular_equity_hours(datetime.fromtimestamp(now, timezone.utc))),
           "live_orders_enabled": False, "mode": "READ_ONLY_ANALYSIS", "symbols": {}}
    if not out["market_open"]:
        out["note"] = "market closed; no provider requests"
        return out
    quotes = post("/clone-v2/market/quotes", {"symbols": list(SYMBOLS)}, key).get("quotes", {})
    today = datetime.fromtimestamp(now, IST).date().isoformat()
    for symbol in SYMBOLS:
        out["symbols"][symbol] = {}
        for frame, interval in FRAMES:
            if interval == 5 and minute_index % 5 != 0 and previous:
                kept = (previous.get("symbols", {}).get(symbol, {}) or {}).get(frame)
                if kept:
                    out["symbols"][symbol][frame] = kept
                    continue
            try:
                response = with_integrity(post("/clone-v2/market/candles", {
                    "symbol": symbol, "interval": interval,
                    "from_date": today, "to_date": today}, key))
                out["symbols"][symbol][frame] = evaluate(symbol, frame, response, quotes.get(symbol), now)
            except urllib.error.HTTPError as exc:
                out["symbols"][symbol][frame] = {"state": "ERROR", "reason": "HTTP %s" % exc.code}
            except Exception as exc:  # keep the loop alive; never print payloads
                out["symbols"][symbol][frame] = {"state": "ERROR", "reason": type(exc).__name__}
    return out


def summary(out):
    parts = []
    for symbol, frames in out.get("symbols", {}).items():
        for frame, row in frames.items():
            parts.append("%s %s %s %s" % (symbol, frame, row.get("state"),
                                          row.get("bias") or row.get("reason", "")[:30]))
    return "market_open=%s | %s" % (out.get("market_open"), " ; ".join(parts) or out.get("note", ""))


def main():
    key = SSK_FILE.read_bytes().strip().decode("ascii")
    once = "--once" in sys.argv
    previous, minute_index = None, 0
    while True:
        now = time.time()
        try:
            out = cycle(key, now, minute_index, previous)
            atomic_write(OUT_FILE, json.dumps(out) + "\n")
            previous = out
            print(summary(out), flush=True)
        except Exception as exc:
            print("CYCLE_FAILED", type(exc).__name__, flush=True)
        minute_index += 1
        if once:
            return 0
        time.sleep(max(5, 60 - (time.time() % 60) + 8))


if __name__ == "__main__":
    raise SystemExit(main())
