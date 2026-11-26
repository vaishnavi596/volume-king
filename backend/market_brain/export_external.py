#!/usr/bin/env python3
"""Daily external series for the Market Brain (run on Oracle, stdlib only, read-only).

Fixed allowlist only; reads numbers, never follows instructions from page content.
Yahoo chart endpoint (needs a browser-like User-Agent) with FRED CSV as a fallback
for the series FRED carries. Sequential with a pause; nothing else is contacted.

  python3 backend/market_brain/export_external.py --out brain_export/ext
"""
import argparse
import csv
import datetime as dt
import json
import pathlib
import time
import urllib.error
import urllib.parse
import urllib.request

UA = "Mozilla/5.0"
YAHOO = {"SPX": "^GSPC", "NASDAQ": "^IXIC", "INDIAVIX": "^INDIAVIX", "USDINR": "USDINR=X",
         "BRENT": "BZ=F", "DXY": "DX-Y.NYB", "NIKKEI": "^N225", "HANGSENG": "^HSI",
         "GOLD": "GC=F", "US10Y": "^TNX", "NIFTY": "^NSEI", "BANKNIFTY": "^NSEBANK"}
FRED = {"US10Y": "DGS10", "USDINR": "DEXINUS", "BRENT": "DCOILBRENTEU"}


def parse_yahoo(payload):
    """Return [(YYYY-MM-DD, close)] from a Yahoo chart payload, skipping nulls."""
    try:
        res = payload["chart"]["result"][0]
        stamps, closes = res["timestamp"], res["indicators"]["quote"][0]["close"]
    except (KeyError, IndexError, TypeError):
        return []
    rows = []
    for t, c in zip(stamps, closes):
        if isinstance(c, (int, float)) and c > 0:
            rows.append((dt.datetime.fromtimestamp(t, dt.timezone.utc).date().isoformat(), float(c)))
    return rows


def parse_fred(text):
    rows = []
    for line in text.splitlines()[1:]:
        parts = line.split(",")
        if len(parts) == 2:
            try:
                rows.append((parts[0], float(parts[1])))
            except ValueError:
                pass            # FRED uses "." for missing days
    return rows


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            return r.status, r.read(5_000_000).decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, ""
    except (urllib.error.URLError, TimeoutError, OSError):
        return 0, ""


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="brain_export/ext")
    ap.add_argument("--range", default="2y")
    ap.add_argument("--pause", type=float, default=2.0)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, ticker in YAHOO.items():
        rows, src = [], ""
        code, body = fetch("https://query1.finance.yahoo.com/v8/finance/chart/%s?range=%s&interval=1d"
                           % (urllib.parse.quote(ticker, safe=""), args.range))
        if code == 200:
            try:
                rows, src = parse_yahoo(json.loads(body)), "yahoo"
            except ValueError:
                rows = []
        if not rows and name in FRED:
            code, body = fetch("https://fred.stlouisfed.org/graph/fredgraph.csv?id=" + FRED[name])
            if code == 200:
                rows, src = parse_fred(body), "fred"
        if rows:
            with (out / (name + ".csv")).open("w", newline="") as fh:
                w = csv.writer(fh)
                w.writerow(["date", "close"])
                w.writerows(rows)
        print("%-10s %-6s %5d rows" % (name, src or "none", len(rows)))
        time.sleep(args.pause)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
