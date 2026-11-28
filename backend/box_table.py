"""B261 server box table: the same T / C / M / F / N / O numbers the phone shows, computed once on the server.

Pure functions, standard library only (Python 3.9). T and C reuse the phone's own helpers (scanner_engine,
analysis_quality, historical_session_window, five_engine, filter_wiring_audit), so the numbers match what the
phone computes from the same 1m candles. Server T uses the DEFAULT filter set; the phone may refine with the
owner's own filters later. Nothing here is a vote and nothing places an order.
"""
import json
import time

from scanner_engine import analyze, DEFAULT_FILTERS
from analysis_quality import quality_check
from historical_session_window import historical_regular_session_bars
from five_engine import completed_timeframe_candle_balance
from filter_wiring_audit import CANDLE_FILTERS
from v3_m_forward import m_lean

TABLE_VERSION = 1


def completed_session_bars(raw, now):
    """1m candles of the regular session that are fully closed; [] when nothing usable."""
    if not isinstance(raw, list):
        return []
    try:
        bars = historical_regular_session_bars(raw, "1m")
    except Exception:
        return []
    return [b for b in bars if isinstance(b, (list, tuple)) and len(b) >= 6 and b[0] + 60 <= now]


def tech_box(bars, now):
    """Phone rule: quality check, analyze with the filter set, canonical candle filters only, >= 1 directional vote."""
    if not bars:
        return None
    quality = quality_check(bars, 60, now=bars[-1][0] + 60)
    if not quality.get("usable"):
        return None
    result = analyze(quality["bars"], list(DEFAULT_FILTERS), "1m")
    bulls = bears = 0
    seen = set()
    for item in result.get("votes") or []:
        name = item.get("name") if isinstance(item, dict) else None
        if name not in CANDLE_FILTERS or name in seen:
            continue
        seen.add(name)
        vote = item.get("vote")
        if type(vote) is int and vote == 1:
            bulls += 1
        elif type(vote) is int and vote == -1:
            bears += 1
    total = bulls + bears
    if not total:
        return None
    return {"b": round(100 * bulls / total), "s": round(100 * bears / total), "n": total}


def candle_box(raw, now):
    out = completed_timeframe_candle_balance({"source": "Dhan", "_scanner_timeframe": "1m", "bars": raw}, "1m", now=now)
    if not isinstance(out, dict) or "bullish" not in out:
        return None
    return {"b": out["bullish"], "s": out["bearish"]}


def m_box(bars):
    row = {}
    for hz in (30, 60):
        lean = m_lean(bars, hz) if bars else None
        if lean:
            row["h%d" % hz] = {"b": lean["bullish"], "s": lean["bearish"], "lean": lean["lean"]}
    return row or None


def build_row(raw, now, fut=None, news=None, oi=None):
    """One symbol's row. Missing parts stay None (shown as WAIT with a reason by the phone)."""
    bars = completed_session_bars(raw, now)
    row = {"t": int(now), "bars": len(bars)}
    row["last_bar"] = int(bars[-1][0]) if bars else None
    try:
        row["T"] = tech_box(bars, now)
    except Exception:
        row["T"] = None
    try:
        row["C"] = candle_box(raw, now)
    except Exception:
        row["C"] = None
    try:
        row["M"] = m_box(bars)
    except Exception:
        row["M"] = None
    if isinstance(fut, dict) and type(fut.get("bullish")) in (int, float):
        row["F"] = {"b": fut["bullish"], "s": fut["bearish"], "buildup": fut.get("buildup"), "day": fut.get("day")}
    if isinstance(news, dict) and type(news.get("bullish")) in (int, float):
        row["N"] = {"b": news["bullish"], "s": news["bearish"], "n": news.get("n")}
    elif isinstance(news, dict) and news.get("n"):
        row["N"] = {"n": news.get("n"), "dir": None}
    if isinstance(oi, dict) and type(oi.get("bullish")) in (int, float):
        row["O"] = {"b": oi["bullish"], "s": oi["bearish"], "expiry": oi.get("expiry"), "pcr": oi.get("pcr")}
    return row


def assemble_table(rows, now, market_open, extra=None):
    out = {"v": TABLE_VERSION, "at": int(now), "market_open": bool(market_open), "box_base": "1m",
           "filters": "default", "count": len(rows), "rows": rows}
    if extra:
        out.update(extra)
    return out
