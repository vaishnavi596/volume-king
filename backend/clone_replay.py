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
try:
    from v3_heavyweights import heavy_lean, constituents  # noqa: E402
except ImportError:
    heavy_lean = constituents = None
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


def body_balance(past, n=8):
    """Same body-only balance as five_engine.historical_candle_balance (bull/bear share of the last n candles)."""
    bulls = bears = 0
    for b in past[-n:]:
        try:
            o, c = float(b[1]), float(b[4])
        except (TypeError, ValueError, IndexError):
            return None
        bulls += c > o; bears += c < o
    if bulls + bears < 5:
        return None
    share = round(bulls * 100 / (bulls + bears))
    return "BULLISH" if share >= 60 else "BEARISH" if share <= 40 else None


def replay_day(bars, report, prev_close=None, symbol=None, heavy_day=None):
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
        c_bias = body_balance(past)
        h_bias = None
        if heavy_day and heavy_lean and symbol:
            sub = {k: [b for b in v if b[0] <= t] for k, v in heavy_day.items() if v}
            hl = heavy_lean(symbol, sub)
            if hl:
                h_bias = "BULLISH" if hl["bullish"] >= 60 else "BEARISH" if hl["bullish"] <= 40 else None
        for hz in HORIZONS:
            j = i - 1 + hz
            if j >= n:
                continue
            after = float(bars[j][4])
            mv = min_move(past, entry, hz)
            for box, bx in (("T", bias), ("C", c_bias), ("H", h_bias)):
                if bx:
                    bh = resolve_prediction(entry, bx, after, mv)
                    if bh is not None:
                        bump(report.setdefault("box", {}).setdefault(box, {}), "%dm" % hz, bh, after > entry)
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


INTRADAY_WINDOWS = 4


def next_day_score(bars, lookback=5, min_move_pct=0.1):
    """Daily trend lean (close vs mean of previous `lookback` closes) scored on the NEXT day's close-to-close move.
    Moves under min_move_pct are flat (not counted). Returns n, hit_rate, up_rate, days (read-only analysis)."""
    try:
        closes = [float(b[4]) for b in bars or []]
    except (TypeError, ValueError, IndexError):
        return None
    n = hits = up = 0
    for i in range(lookback, len(closes) - 1):
        base = sum(closes[i - lookback:i]) / lookback
        lean = closes[i] - base
        move = closes[i + 1] - closes[i]
        if closes[i] <= 0 or abs(move) / closes[i] * 100 < min_move_pct or lean == 0:
            continue
        n += 1
        hits += (lean > 0) == (move > 0)
        up += move > 0
    if not n:
        return None
    return {"n": n, "hit_rate": round(100 * hits / n, 1), "up_rate": round(100 * up / n, 1), "days": len(closes)}


def finish(group):
    return {k: {"n": v["n"], "hit_rate": round(100 * v["hits"] / v["n"], 1) if v["n"] else None,
                "up_rate": round(100 * v.get("up", 0) / v["n"], 1) if v["n"] and k.endswith("m") else None}
            for k, v in sorted(group.items())}


def main():
    key = SSK_FILE.read_bytes().strip().decode("ascii")
    today = datetime.now(IST).date()
    report = {"horizons": {}, "windows": {}, "confluence": {}, "engine_dir": {}, "box": {},
              "engine": {"calls": 0, "errors": 0, "directional_ge3": 0}, "days": [], "symbols": {}}
    heavy_days = {}
    next_day = {}
    if constituents:
        for name in sorted({c for s_ in SYMBOLS for c in constituents(s_)}):
            try:
                r_ = with_integrity(post("/clone-v2/market/candles", {
                    "symbol": name, "interval": 1,
                    "from_date": (today - timedelta(days=5)).isoformat(), "to_date": today.isoformat()}, key, timeout=60))
                heavy_days[name] = split_days(r_.get("bars"))
            except Exception:
                heavy_days[name] = {}
            time.sleep(1.2)
    for symbol in SYMBOLS:
        all_bars, failure = [], None
        for w in range(INTRADAY_WINDOWS):   # B255: 5-day windows going back (gateway cap), ~4 weeks in total
            hi = today - timedelta(days=5 * w + (0 if w == 0 else 1))
            lo = hi - timedelta(days=5 if w == 0 else 4)
            try:
                r_ = with_integrity(post("/clone-v2/market/candles", {
                    "symbol": symbol, "interval": 1,
                    "from_date": lo.isoformat(), "to_date": hi.isoformat()}, key, timeout=60))
                all_bars.extend(r_.get("bars") or [])
            except Exception as exc:
                failure = failure or type(exc).__name__
            time.sleep(1.2)
        if not all_bars:
            report["symbols"][symbol] = "FETCH_FAILED " + (failure or "NoBars")
            continue
        seen_ts, merged = set(), []
        for b in sorted(all_bars, key=lambda x: x[0]):
            if b[0] not in seen_ts:
                seen_ts.add(b[0]); merged.append(b)
        days = split_days(merged)
        # the current day is excluded when the market may still be open
        days.pop(today.isoformat(), None) if datetime.now(IST).hour < 16 else None
        report["symbols"][symbol] = sorted(days)
        prev = None
        for d, bars in sorted(days.items()):
            hd = {c: (heavy_days.get(c) or {}).get(d) for c in (constituents(symbol) if constituents else ())}
            replay_day(bars, report, prev, symbol, hd)
            try:
                prev = float(bars[-1][4])
            except (TypeError, ValueError, IndexError):
                prev = None
            if d not in report["days"]:
                report["days"].append(d)
        try:
            d_ = with_integrity(post("/clone-v2/market/daily", {
                "symbol": symbol, "interval": 1,
                "from_date": (today - timedelta(days=380)).isoformat(), "to_date": today.isoformat()}, key, timeout=60))
            nd = next_day_score(d_.get("bars"))
            if nd:
                next_day[symbol] = nd
        except Exception as exc:
            next_day[symbol] = {"error": type(exc).__name__}
        time.sleep(1.2)
    report["days"].sort()
    out = {"at": datetime.now(IST).strftime("%Y-%m-%d %H:%M IST"), "days": report["days"],
           "symbols": report["symbols"], "engine": report["engine"],
           "m_hit": finish(report["horizons"]), "m_by_window_30m": finish(report["windows"]),
           "m_by_confluence_30m": finish(report["confluence"]), "engine_dir_20m": finish(report["engine_dir"]),
           "box_hit": {k: finish(v) for k, v in sorted(report["box"].items())},
           "flat_moves": report.get("flat", 0), "next_day": next_day,
           "note": "REPLAY on past real candles; analysis only; M is never a vote"}
    atomic_write(REPLAY_FILE, json.dumps(out) + "\n")
    print("REPLAY_OK days=%s calls=%d errors=%d" % (",".join(out["days"]), report["engine"]["calls"], report["engine"]["errors"]))


if __name__ == "__main__":
    main()
