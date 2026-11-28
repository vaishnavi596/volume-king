#!/usr/bin/env python3
"""BOT KING Clone: closed-market REPLAY on real past 1m candles (analysis only, no orders).

Fetches the last closed trading days from the LOCAL gateway, replays the same M lean
and the same scanner filters minute-block by minute-block, and measures hit-rates
against what the price really did next. Writes replay-latest.json in the private dir.
Standard library only (Python 3.9). Safe to run any time the market is closed.
"""
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clone_signal_runner import post, with_integrity, atomic_write, SSK_FILE, OUT_FILE, SYMBOLS, IST  # noqa: E402
from scanner_engine import analyze, DEFAULT_FILTERS  # noqa: E402
from v3_m_forward import m_leans, m_context, resolve_prediction, window_of, min_move  # noqa: E402

REPLAY_FILE = Path(os.environ.get("BOTKING_REPLAY_OUT", str(OUT_FILE.parent / "replay-latest.json")))
STEP = 5
START_IDX = 60
HORIZONS = (20, 30, 60)


def split_days(bars):
    days = {}
    for b in bars or ():
        try:
            t = float(b[0]); float(b[4])
        except (TypeError, ValueError, IndexError):
            continue
        days.setdefault(datetime.fromtimestamp(t, IST).date().isoformat(), []).append(b)
    return {d: v for d, v in days.items() if len(v) >= 120}


def bump(group, key, hit, up=None):
    g = group.setdefault(key, {"n": 0, "hits": 0, "up": 0})
    g["n"] += 1
    g["hits"] += int(bool(hit))
    if up is not None:
        g["up"] += int(bool(up))


def replay_day(bars, report, prev_close=None):
    n = len(bars)
    for i in range(START_IDX, n, STEP):
        past = bars[:i]
        entry = float(past[-1][4])
        t = float(past[-1][0])
        try:
            res = analyze([list(b) for b in past], selected=list(DEFAULT_FILTERS), timeframe="1m")
            votes = [v for v in res.get("votes", []) if v.get("vote") in (-1, 1)]
            report["engine"]["calls"] += 1
        except Exception:
            report["engine"]["errors"] += 1
            votes = []
        bulls = sum(v["vote"] == 1 for v in votes)
        bears = sum(v["vote"] == -1 for v in votes)
        bias = None
        if bulls + bears >= 3:
            report["engine"]["directional_ge3"] += 1
            bias = "BULLISH" if bulls > bears else "BEARISH" if bears > bulls else None
        leans = m_leans(past)
        for hz in HORIZONS:
            j = i - 1 + hz
            if j >= n:
                continue
            after = float(bars[j][4])
            if bias:
                hit = resolve_prediction(entry, bias, after)
                if hit is not None and hz == 20:
                    bump(report["engine_dir"], "20m", hit)
            lean = leans.get(str(hz))
            if not lean:
                continue
            hit = resolve_prediction(entry, lean["lean"], after, min_move(past, entry, hz))
            if hit is None:
                report["flat"] = report.get("flat", 0) + 1
                continue
            bump(report["horizons"], "%dm" % hz, hit, after > entry)
            ctx = m_context(lean, past, [bias] if bias else None, t, None, prev_close) if lean["lean"] != "NEUTRAL" else None
            if hz == 30 and ctx:
                bump(report["windows"], ctx["window"], hit)
                bump(report["confluence"], "%d/%d" % (ctx["agree"], ctx["total"]), hit)


def finish(group):
    return {k: {"n": v["n"], "hit_rate": round(100 * v["hits"] / v["n"], 1) if v["n"] else None,
                "up_rate": round(100 * v.get("up", 0) / v["n"], 1) if v["n"] and k.endswith("m") else None}
            for k, v in sorted(group.items())}


def main():
    key = SSK_FILE.read_bytes().strip().decode("ascii")
    today = datetime.now(IST).date()
    report = {"horizons": {}, "windows": {}, "confluence": {}, "engine_dir": {},
              "engine": {"calls": 0, "errors": 0, "directional_ge3": 0}, "days": [], "symbols": {}}
    for symbol in SYMBOLS:
        try:
            resp = with_integrity(post("/clone-v2/market/candles", {
                "symbol": symbol, "interval": 1,
                "from_date": (today - timedelta(days=5)).isoformat(), "to_date": today.isoformat()}, key, timeout=60))
        except Exception as exc:
            report["symbols"][symbol] = "FETCH_FAILED " + type(exc).__name__
            continue
        days = split_days(resp.get("bars"))
        # the current day is excluded when the market may still be open
        days.pop(today.isoformat(), None) if datetime.now(IST).hour < 16 else None
        report["symbols"][symbol] = sorted(days)
        prev = None
        for d, bars in sorted(days.items()):
            replay_day(bars, report, prev)
            try:
                prev = float(bars[-1][4])
            except (TypeError, ValueError, IndexError):
                prev = None
            if d not in report["days"]:
                report["days"].append(d)
        time.sleep(1.2)
    report["days"].sort()
    out = {"at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"), "days": report["days"],
           "symbols": report["symbols"], "engine": report["engine"],
           "m_hit": finish(report["horizons"]), "m_by_window_30m": finish(report["windows"]),
           "m_by_confluence_30m": finish(report["confluence"]), "engine_dir_20m": finish(report["engine_dir"]),
           "note": "REPLAY on past real candles; analysis only; M is never a vote"}
    atomic_write(REPLAY_FILE, json.dumps(out) + "\n")
    print("REPLAY_OK days=%s calls=%d errors=%d" % (",".join(out["days"]), report["engine"]["calls"], report["engine"]["errors"]))


if __name__ == "__main__":
    main()
