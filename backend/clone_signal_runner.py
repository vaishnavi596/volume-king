#!/usr/bin/env python3
"""BOT KING Clone: server-side READ-ONLY signal runner (paper/analysis only).

Runs on Oracle next to the Clone gateway and keeps working when no phone is
connected. Every minute (regular NSE hours) it asks the LOCAL gateway for the
three index quotes and 1m/5m candles, qualifies the candles with the same
rules as the phone (v3_live_candle_bridge) and runs the same scanner filters.
Result is written atomically to a private JSON file. No orders, no broker
write endpoint, no credentials printed. Standard library only (Python 3.9).
"""
import csv
import hashlib
import io
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
from v3_m_forward import m_lean, m_leans, resolve_prediction  # noqa: E402

IST = timezone(timedelta(hours=5, minutes=30))
GATEWAY = os.environ.get("BOTKING_SIGNAL_GATEWAY", "http://127.0.0.1:8002")
SSK_FILE = Path(os.environ.get("BOTKING_SIGNAL_SSK", "/home/opc/botking-clone-v2-private/ssk"))
OUT_FILE = Path(os.environ.get("BOTKING_SIGNAL_OUT", "/home/opc/botking-clone-v2-private/signals-latest.json"))
JOURNAL_FILE = Path(os.environ.get("BOTKING_SIGNAL_JOURNAL", str(OUT_FILE.parent / "signals-journal.jsonl")))
JOURNAL_KEEP = 300
LEDGER_FILE = Path(os.environ.get("BOTKING_SIGNAL_LEDGER", str(OUT_FILE.parent / "m-ledger.json")))
LEDGER_EVERY_S = 300
LEDGER_HORIZON_S = 1200
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
                if interval == 1:
                    lean = m_lean(response.get("bars"))
                    ltp = (quotes.get(symbol) or {}).get("ltp")
                    if lean and type(ltp) in (int, float):
                        out.setdefault("m_lean", {})[symbol] = dict(lean, ltp=float(ltp))
                    if type(ltp) in (int, float):
                        for hz, hl in m_leans(response.get("bars")).items():
                            if hz != "20" and hl:
                                out.setdefault("m_horizons", {}).setdefault(symbol, {})[hz] = dict(hl, ltp=float(ltp))
                out["symbols"][symbol][frame] = evaluate(symbol, frame, response, quotes.get(symbol), now)
            except urllib.error.HTTPError as exc:
                out["symbols"][symbol][frame] = {"state": "ERROR", "reason": "HTTP %s" % exc.code}
            except Exception as exc:  # keep the loop alive; never print payloads
                out["symbols"][symbol][frame] = {"state": "ERROR", "reason": type(exc).__name__}
    return out


def change_events(previous, out, now):
    """Pure: bias/state changes between two cycles -> list of journal rows (B246)."""
    events = []
    if not isinstance(previous, dict) or not out.get("market_open"):
        return events
    for symbol, frames in (out.get("symbols") or {}).items():
        for frame, row in (frames or {}).items():
            old = ((previous.get("symbols") or {}).get(symbol) or {}).get(frame) or {}
            new_bias, old_bias = row.get("bias"), old.get("bias")
            if row.get("state") == "LIVE_VERIFIED" and new_bias and new_bias != old_bias:
                events.append({"t": int(now), "symbol": symbol, "frame": frame,
                               "event": "BIAS", "from": old_bias, "to": new_bias,
                               "bullish": row.get("bullish"), "bearish": row.get("bearish")})
    return events


def append_journal(events, path=None):
    path = path or JOURNAL_FILE
    if not events:
        return
    lines = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        pass
    lines.extend(json.dumps(e, separators=(",", ":")) for e in events)
    atomic_write(path, "\n".join(lines[-JOURNAL_KEEP:]) + "\n")


def ledger_step(ledger, out, now):
    """Pure: record M predictions every 5 min, score them after 20 min. Mutates and returns ledger."""
    ledger.setdefault("pending", []); ledger.setdefault("stats", {}); ledger.setdefault("last_t", {})
    if not out.get("market_open"):
        return ledger
    for symbol, lean in (out.get("m_lean") or {}).items():
        if now - ledger["last_t"].get(symbol, 0) >= LEDGER_EVERY_S and lean.get("lean") in ("BULLISH", "BEARISH", "NEUTRAL"):
            ledger["pending"].append({"t": int(now), "symbol": symbol, "lean": lean["lean"], "entry": lean["ltp"]})
            ledger["last_t"][symbol] = int(now)
    for symbol, hz_map in (out.get("m_horizons") or {}).items():
        for hz, lean in (hz_map or {}).items():
            key = symbol + "@" + hz
            if now - ledger["last_t"].get(key, 0) >= LEDGER_EVERY_S and lean.get("lean") in ("BULLISH", "BEARISH", "NEUTRAL"):
                ledger["pending"].append({"t": int(now), "symbol": symbol, "lean": lean["lean"],
                                          "entry": lean["ltp"], "h": int(hz)})
                ledger["last_t"][key] = int(now)
    keep = []
    for row in ledger["pending"]:
        hz = row.get("h", LEDGER_HORIZON_S // 60)
        if now - row["t"] < hz * 60:
            keep.append(row); continue
        price = ((out.get("m_lean") or {}).get(row["symbol"]) or {}).get("ltp")
        hit = resolve_prediction(row["entry"], row["lean"], price) if price is not None else None
        if hit is None:
            continue  # neutral / flat / no price: not scored
        skey = row["symbol"] if "h" not in row else row["symbol"] + "@" + str(row["h"])
        st = ledger["stats"].setdefault(skey, {"n": 0, "hits": 0})
        st["n"] += 1; st["hits"] += int(bool(hit))
    ledger["pending"] = keep[-400:]
    return ledger


def ledger_summary(ledger):
    rows = {}
    for symbol, st in (ledger.get("stats") or {}).items():
        n = st.get("n", 0)
        rows[symbol] = {"n": n, "hits": st.get("hits", 0),
                        "hit_rate": round(100 * st.get("hits", 0) / n, 1) if n else None}
    return {"horizon_minutes": LEDGER_HORIZON_S // 60, "scored": rows,
            "note": "M is a forward lean; not a vote until a measured hit-rate is accepted by the owner"}


def summary(out):
    parts = []
    for symbol, frames in out.get("symbols", {}).items():
        for frame, row in frames.items():
            parts.append("%s %s %s %s" % (symbol, frame, row.get("state"),
                                          row.get("bias") or row.get("reason", "")[:30]))
    return "market_open=%s | %s" % (out.get("market_open"), " ; ".join(parts) or out.get("note", ""))


MASTER_URL = "https://images.dhan.co/api-data/api-scrip-master.csv"
LOT_FILE = Path(os.environ.get("BOTKING_LOT_FILE", str(OUT_FILE.parent / "lot-sizes.json")))
LOT_REFRESH_S = 12 * 3600


def parse_lot_sizes(lines):
    """Pure: Dhan scrip-master lines -> {"NIFTY": 65, ...} for index and stock options (first seen wins)."""
    lots = {}
    for row in csv.DictReader(lines):
        if row.get("SEM_INSTRUMENT_NAME") not in ("OPTIDX", "OPTSTK"):
            continue
        name = str(row.get("SEM_TRADING_SYMBOL", "")).split("-")[0].strip().upper()
        try:
            lot = int(float(row.get("SEM_LOT_UNITS")))
        except (TypeError, ValueError):
            continue
        if name and 0 < lot <= 100000 and name not in lots:
            lots[name] = lot
    return lots


CONTRACT_FILE = Path(os.environ.get("BOTKING_OPTION_CONTRACTS", str(OUT_FILE.parent / "option-contracts.json")))
CONTRACT_UNDERLYINGS = ("NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY")


def parse_option_contracts(lines, today_iso, keep_expiries=3):
    """Pure: scrip-master lines -> {"NIFTY|2026-12-02|24500|CE": [segment, security_id, lot]} for
    the nearest `keep_expiries` expiries of each index underlying. Never raises on bad rows."""
    per = {}
    for row in csv.DictReader(lines):
        if row.get("SEM_INSTRUMENT_NAME") != "OPTIDX":
            continue
        name = str(row.get("SEM_TRADING_SYMBOL", "")).split("-")[0].strip().upper()
        if name not in CONTRACT_UNDERLYINGS:
            continue
        side = str(row.get("SEM_OPTION_TYPE", "")).strip().upper()
        exch = str(row.get("SEM_EXM_EXCH_ID", "")).strip().upper()
        expiry = str(row.get("SEM_EXPIRY_DATE", ""))[:10]
        try:
            sid = int(row.get("SEM_SMST_SECURITY_ID"))
            lot = int(float(row.get("SEM_LOT_UNITS")))
            strike = float(row.get("SEM_STRIKE_PRICE"))
        except (TypeError, ValueError):
            continue
        if (side not in ("CE", "PE") or exch not in ("NSE", "BSE") or expiry < today_iso
                or lot <= 0 or strike <= 0 or len(expiry) != 10):
            continue
        per.setdefault(name, {}).setdefault(expiry, []).append(
            ("%s|%s|%g|%s" % (name, expiry, strike, side), [exch + "_FNO", sid, lot]))
    out = {}
    for name, by_exp in per.items():
        for expiry in sorted(by_exp)[:keep_expiries]:
            out.update(dict(by_exp[expiry]))
    return out


def lot_by_expiry(contracts):
    """{"NIFTY|2026-12-02": 65, ...}: exact lot per underlying+expiry (lots can differ by expiry)."""
    out = {}
    for key, row in (contracts or {}).items():
        parts = key.split("|")
        if len(parts) == 4 and isinstance(row, list) and len(row) == 3:
            out.setdefault(parts[0] + "|" + parts[1], row[2])
    return out


def load_lot_sizes(now):
    """Cached lot-size map; refreshed from Dhan's public scrip master at most every 12 h. Never raises."""
    try:
        cached = json.loads(LOT_FILE.read_text(encoding="utf-8")) if LOT_FILE.exists() else {}
    except (OSError, ValueError):
        cached = {}
    if not isinstance(cached, dict):
        cached = {}
    if (now - float(cached.get("fetched", 0) or 0) < LOT_REFRESH_S and cached.get("lots")
            and CONTRACT_FILE.exists()):
        return cached["lots"]
    try:
        with urllib.request.urlopen(MASTER_URL, timeout=180) as resp:
            raw = resp.read()
        text = raw.decode("utf-8", "replace")
        lots = parse_lot_sizes(io.StringIO(text, newline=""))
        if lots.get("NIFTY"):
            atomic_write(LOT_FILE, json.dumps({"fetched": int(now), "lots": lots}) + "\n")
            try:
                today = datetime.fromtimestamp(now, IST).date().isoformat()
                contracts = parse_option_contracts(io.StringIO(text, newline=""), today)
                if contracts:
                    atomic_write(CONTRACT_FILE, json.dumps({"fetched": int(now), "contracts": contracts},
                                                          separators=(",", ":")) + "\n")
            except Exception:
                pass  # contracts are best-effort
            return lots
    except Exception:
        pass
    return cached.get("lots") or {}


def main():
    key = SSK_FILE.read_bytes().strip().decode("ascii")
    once = "--once" in sys.argv
    previous, minute_index = None, 0
    while True:
        now = time.time()
        try:
            out = cycle(key, now, minute_index, previous)
            try:
                ledger = json.loads(LEDGER_FILE.read_text(encoding="utf-8")) if LEDGER_FILE.exists() else {}
                ledger = ledger_step(ledger if isinstance(ledger, dict) else {}, out, now)
                atomic_write(LEDGER_FILE, json.dumps(ledger) + "\n")
                out["m_ledger"] = ledger_summary(ledger)
            except Exception:
                pass  # ledger is best-effort; never stop the runner
            try:
                out["lot_sizes"] = load_lot_sizes(now)
                cdata = json.loads(CONTRACT_FILE.read_text(encoding="utf-8")) if CONTRACT_FILE.exists() else {}
                out["lot_by_expiry"] = lot_by_expiry(cdata.get("contracts") if isinstance(cdata, dict) else {})
            except Exception:
                pass  # lot sizes are best-effort
            atomic_write(OUT_FILE, json.dumps(out) + "\n")
            try:
                append_journal(change_events(previous, out, now))
            except Exception:
                pass  # journal is best-effort; never stop the runner
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
