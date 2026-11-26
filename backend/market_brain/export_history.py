#!/usr/bin/env python3
"""Read-only Dhan 5m history export for the Market Brain (run on Oracle, stdlib only).

Uses the Clone V2 gateway on this host (127.0.0.1:8002), the same read-only route and
SSK key file the phone uses.
It never prints the key, prices or raw responses, sends no orders, and stops at the
first HTTP 401/403/429 or repeated transport failure. Resumable: finished windows are
recorded and skipped on the next run. Run when the market is closed.

  python3 backend/market_brain/export_history.py --symbols NIFTY,BANKNIFTY,SENSEX --days 365
"""
import argparse
import csv
import datetime as dt
import json
import math
import os
import pathlib
import time
import urllib.error
import urllib.request

BASE = "http://127.0.0.1:8002"
KEY_FILE = pathlib.Path(os.environ.get("BOTKING_CLONE_V2_SSK_FILE", "/home/opc/botking-clone-v2-private/ssk"))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
SPAN_DAYS = 5          # server rejects (to - from).days > 5


def windows(today, days):
    """Newest-first (from_date, to_date) pairs covering `days` calendar days, no overlap."""
    out, end, stop = [], today, today - dt.timedelta(days=days)
    while end > stop:
        start = max(end - dt.timedelta(days=SPAN_DAYS), stop)
        out.append((start, end))
        end = start - dt.timedelta(days=1)
    return out


def valid_rows(bars):
    good = []
    for r in bars if isinstance(bars, list) else []:
        if (isinstance(r, list) and len(r) == 6
                and all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v) for v in r)
                and r[0] > 0 and min(r[1:5]) > 0 and r[2] >= max(r[1], r[3], r[4]) and r[3] <= min(r[1], r[4])
                and r[5] >= 0):
            good.append(r)
    return good


def call(path, key, payload=None):
    data = None if payload is None else json.dumps(payload).encode()
    headers = {"X-BotKing-Key": key, "Accept": "application/json", "Cache-Control": "no-store"}
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(BASE + path, data=data, headers=headers, method="GET" if data is None else "POST")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=30) as resp:
            return resp.status, json.loads(resp.read(2_000_000).decode())
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return 0, None


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--symbols", required=True)
    ap.add_argument("--days", type=int, default=365)
    ap.add_argument("--out", default="brain_export")
    ap.add_argument("--pause", type=float, default=1.5)
    args = ap.parse_args(argv)
    if not 7 <= args.days <= 800 or args.pause < 1.0:
        raise SystemExit("days must be 7..800 and pause >= 1.0 second")
    symbols = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
    key = KEY_FILE.read_text().strip() if KEY_FILE.exists() else ""
    if not 32 <= len(key) <= 512:
        raise SystemExit("SSK key file unavailable; no requests made")
    code, status = call("/clone-v2/status", key)
    if code != 200 or not status or status.get("authenticated") is not True or status.get("live_orders_enabled") is not False:
        raise SystemExit("Clone gateway status check failed (HTTP %s); no history requests made" % code)
    out = pathlib.Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    progress_file = out / "progress.json"
    done = json.loads(progress_file.read_text()) if progress_file.exists() else {}
    today = dt.datetime.now(IST).date()
    plan = windows(today, args.days)
    for sym in symbols:
        part = out / (sym + "_5m.part.jsonl")
        finished = set(done.get(sym, []))
        fails = 0
        for i, (a, b) in enumerate(plan, 1):
            tag = a.isoformat()
            if tag in finished:
                continue
            code, res = call("/clone-v2/market/candles", key, {"symbol": sym, "interval": 5,
                                                      "from_date": a.isoformat(), "to_date": b.isoformat()})
            if code in (401, 403, 429, 502, 503):
                print("%s window %d/%d: HTTP %d, STOP (resume later)" % (sym, i, len(plan), code))
                progress_file.write_text(json.dumps(done))
                return 3
            if code == 0:
                fails += 1
                if fails >= 3:
                    print("%s: repeated transport failure, STOP" % sym)
                    progress_file.write_text(json.dumps(done))
                    return 2
                time.sleep(5)
                continue
            fails = 0
            rows = valid_rows(res.get("bars")) if code == 200 and isinstance(res, dict) else []
            with part.open("a") as fh:
                for r in rows:
                    fh.write(json.dumps(r) + "\n")
            finished.add(tag)
            done[sym] = sorted(finished)
            progress_file.write_text(json.dumps(done))
            time.sleep(args.pause)
        # merge: sort, drop duplicate timestamps
        seen, merged = set(), []
        if part.exists():
            for line in part.read_text().splitlines():
                r = json.loads(line)
                if r[0] not in seen:
                    seen.add(r[0])
                    merged.append(r)
        merged.sort()
        with (out / (sym + "_5m.csv")).open("w", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ts", "open", "high", "low", "close", "volume"])
            w.writerows(merged)
        print("%s: %d bars from %d windows" % (sym, len(merged), len(finished)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
