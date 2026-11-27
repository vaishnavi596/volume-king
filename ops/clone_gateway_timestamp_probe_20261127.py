#!/usr/bin/env python3
"""READ-ONLY: does the LOCAL Clone gateway return exchange_trade_timestamp?

Run on Oracle:  sudo python3 clone_gateway_timestamp_probe_20261127.py
Reads the private SSK file only to authenticate to 127.0.0.1:8002 and NEVER
prints it. Prints only field names and timestamp values for two symbols.
"""
import json
import os
import urllib.request
from pathlib import Path

SSK = Path("/home/opc/botking-clone-v2-private/ssk")


def main():
    if os.geteuid() != 0:
        raise SystemExit("run with sudo")
    key = SSK.read_bytes().strip().decode("ascii")
    req = urllib.request.Request(
        "http://127.0.0.1:8002/clone-v2/market/quotes", method="POST",
        data=json.dumps({"symbols": ["RELIANCE", "NIFTY"]}).encode(),
        headers={"X-BotKing-Key": key, "Content-Type": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=20) as resp:
            data = json.loads(resp.read(200000))
            print("HTTP", resp.status)
    except Exception as exc:
        print("PROBE_FAILED", type(exc).__name__, getattr(exc, "code", ""))
        return 1
    print("top-level keys:", sorted(data.keys()))
    for name, item in (data.get("quotes") or {}).items():
        print(name, "fields:", sorted(item.keys()))
        print("   exchange_trade_timestamp:", item.get("exchange_trade_timestamp"),
              "origin:", item.get("timestamp_origin"))
    print("unavailable:", data.get("unavailable"))
    return 0


raise SystemExit(main())
