#!/usr/bin/env python3
"""READ-ONLY probe: what does Dhan /marketfeed/quote return for last_trade_time?

Run on Oracle:  sudo python3 clone_quote_timestamp_probe_20261127.py
Makes ONE market-data POST (NIFTY index + RELIANCE). Never prints the token,
client id or any credential; prints only field NAMES and the last_trade_time
text. No order endpoint is touched.
"""
import json
import os
import re
import urllib.request
from pathlib import Path

TOKEN = Path("/home/opc/botking-clone-v2-private/dhan-token")
ENV = Path("/etc/bot-king/clone-v2-dhan-client.env")


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


def client_id():
    for line in ENV.read_text().splitlines():
        if line.startswith("DHAN_CLIENT_ID="):
            return line.split("=", 1)[1].strip().strip("\"'")
    raise SystemExit("client id not found")


def main():
    if os.geteuid() != 0:
        raise SystemExit("run with sudo")
    token = TOKEN.read_text().strip()
    body = json.dumps({"IDX_I": [13], "NSE_EQ": [2885]}).encode()
    req = urllib.request.Request(
        "https://api.dhan.co/v2/marketfeed/quote", data=body, method="POST",
        headers={"access-token": token, "client-id": client_id(),
                 "Content-Type": "application/json", "Accept": "application/json"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    try:
        with opener.open(req, timeout=20) as resp:
            raw = resp.read(200000)
            status = resp.status
    except Exception as exc:
        print("PROBE_FAILED", type(exc).__name__, getattr(exc, "code", ""))
        return 1
    print("HTTP", status)
    data = json.loads(raw)
    print("top-level keys:", sorted(data.keys()))
    for seg, items in (data.get("data") or {}).items():
        for sid, rec in items.items():
            print(seg, sid, "fields:", sorted(rec.keys()))
            ltt = rec.get("last_trade_time")
            print("   last_trade_time repr:", repr(ltt), "type:", type(ltt).__name__)
            print("   last_price:", rec.get("last_price"))
            if isinstance(ltt, str):
                shape = re.sub(r"\d", "9", ltt)
                print("   shape:", shape)
    return 0


raise SystemExit(main())
