#!/usr/bin/env python3
"""Read-only local Oracle Dhan smoke test; prints no pairing key or market prices.

Run on the Oracle host as opc: python3 backend/check-dhan-live.py
No orders, writes, external server changes, or fallback quotes.
"""
import datetime as dt
import json
import math
import pathlib
import sys
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8000"
KEY_FILE = pathlib.Path("/home/opc/bot-king-pairing-key.txt")


def request(path, key, payload=None):
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    headers = {"X-BotKing-Key": key, "Accept": "application/json"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers,
                                 method="GET" if data is None else "POST")
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return response.status, json.loads(response.read(2_000_001))
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (urllib.error.URLError, TimeoutError, ValueError, UnicodeError):
        return 0, None


def main():
    try:
        key = KEY_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        print("Pairing key: unavailable (contents not displayed)")
        return 2
    if len(key) < 32:
        print("Pairing key: invalid length")
        return 2
    code, status = request("/dhan/status", key)
    print("Dhan status HTTP:", code)
    if code != 200 or not isinstance(status, dict):
        return 2
    print("Consent authenticated:", status.get("authenticated") is True)
    print("Reauthentication required:", status.get("reauthentication_required") is True)
    print("Market-data configured:", status.get("market_data_configured") is True)
    print("Live orders disabled:", status.get("live_orders_enabled") is False)
    if status.get("live_orders_enabled") is not False:
        print("SAFETY FAILURE: live orders not confirmed disabled")
        return 2
    if status.get("market_data_configured") is not True:
        return 2
    code, quote = request("/dhan/ltp", key, {"symbol": "NIFTY"})
    valid_quote = (code == 200 and isinstance(quote, dict)
                   and quote.get("source") == "dhan"
                   and isinstance(quote.get("ltp"), (int, float))
                   and not isinstance(quote.get("ltp"), bool)
                   and quote["ltp"] > 0
                   and math.isfinite(quote["ltp"]))
    print("NIFTY LTP HTTP:", code, "valid:", valid_quote)
    code, batch = request("/dhan/ltp-batch", key, {})
    quotes = batch.get("quotes") if isinstance(batch, dict) else None
    unavailable = batch.get("unavailable") if isinstance(batch, dict) else None
    print("51-equity batch HTTP:", code,
          "quotes:", len(quotes) if isinstance(quotes, dict) else "invalid",
          "unavailable:", len(unavailable) if isinstance(unavailable, list) else "invalid")
    india_now = dt.datetime.now(dt.timezone(dt.timedelta(hours=5, minutes=30)))
    day = india_now.date() - dt.timedelta(days=1)
    while day.weekday() >= 5:
        day -= dt.timedelta(days=1)
    code, candles = request("/dhan/intraday", key, {
        "symbol": "NIFTY", "interval": 5,
        "from_date": day.isoformat(), "to_date": day.isoformat()})
    bars = candles.get("bars") if isinstance(candles, dict) else None
    print("NIFTY 5m candles HTTP:", code,
          "bars:", len(bars) if isinstance(bars, list) else "invalid",
          "(previous weekday; exchange holiday possible)")
    print("Quote freshness:", "UNVERIFIED (provider exchange timestamp not supplied)")
    print("Android UI: NOT tested by this server-only diagnostic")
    return 0 if valid_quote and isinstance(quotes, dict) and len(quotes) >= 1 and isinstance(bars, list) and len(bars) >= 1 else 2


if __name__ == "__main__":
    sys.exit(main())
