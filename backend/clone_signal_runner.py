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
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

from scanner_engine import analyze, DEFAULT_FILTERS  # noqa: E402
from v3_live_candle_bridge import completed_live_history  # noqa: E402
from v3_equity_session_calendar import regular_equity_hours  # noqa: E402
try:
    from v3_fut_buildup import futures_buildup
    from v3_heavyweights import heavy_lean, constituents
except ImportError:   # older installs: features stay off
    futures_buildup = heavy_lean = constituents = None
from v3_m_forward import m_lean, m_leans, m_context, resolve_prediction, min_move, wilson_low, strength_band, window_of  # noqa: E402
try:
    import v3_news_cue  # noqa: E402
except ImportError:  # older server install: server headline cue stays off
    v3_news_cue = None
try:
    from v3_option_oi_flow import window_oi_change  # noqa: E402
except ImportError:  # older server install without the OI module: OI lean simply stays off
    window_oi_change = None

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
OI_EXPIRY_CACHE = {}
NEWS_STATE = {"at": 0.0, "cue": {}}
NEWS_EVERY_S = 600


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


SIGNAL_MAX_BYTES = 60000   # gateway cuts signals-latest.json at 65536 bytes (invalid JSON -> every server lean lost)


def cap_signal_size(out, limit=SIGNAL_MAX_BYTES):
    """JSON text of `out` guaranteed under `limit` bytes: heaviest informational parts are dropped first."""
    text = json.dumps(out)
    for key in ("replay", "autoupdate", "m_ledger", "m_horizons"):
        if len(text.encode("utf-8")) <= limit:
            break
        out = {k: v for k, v in out.items() if k != key}
        out["trimmed"] = sorted(set(out.get("trimmed", [])) | {key})
        text = json.dumps(out)
    return text


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


def fut_snapshot(key, symbol, today_iso, futures, idx_bars):
    """Index-future price lean + premium (basis) trend from today's 1m futures candles. Read-only; None on any problem."""
    row = futures.get(symbol)
    if not row or not idx_bars:
        return None
    resp = post("/clone-v2/market/futures/candles", {"underlying": symbol, "interval": 1,
                                                    "from_date": today_iso, "to_date": today_iso}, key)
    bars = resp.get("bars")
    lean = m_lean(bars, 30)
    if not lean:
        return None
    spot_by_t = {int(b[0]): float(b[4]) for b in idx_bars}
    basis = [(int(b[0]), float(b[4]) - spot_by_t[int(b[0])]) for b in bars if int(b[0]) in spot_by_t]
    out = {"expiry": row[3], "bullish": lean["bullish"], "bearish": lean["bearish"], "lean": lean["lean"],
           "strength": lean["strength"]}
    bu = futures_buildup(bars, resp.get("oi")) if futures_buildup else None
    if bu:   # B253: price + open-interest build-up; agrees -> small boost, disagrees -> halve the tilt
        out["buildup"] = bu["state"]; out["oi_change_pct"] = bu["oi_change_pct"]
        sign = 1 if bu["direction"] == "BULLISH" else -1
        tilt = out["bullish"] - 50
        if tilt != 0 and (tilt > 0) == (sign == 1):
            out["bullish"] = max(0, min(100, round(50 + tilt * (1 + 0.25 * bu["weight"]))))
        elif tilt != 0:
            out["bullish"] = round(50 + tilt / 2)
        out["bearish"] = 100 - out["bullish"]
    if len(basis) >= 31:
        change = basis[-1][1] - basis[-31][1]
        out["basis"] = round(basis[-1][1], 2)
        out["basis_change_30m"] = round(change, 2)
        if (change > 0) != (lean["bullish"] > 50) and change != 0:
            out["bullish"] = round((out["bullish"] + 50) / 2)       # premium trend disagrees: halve the tilt
            out["bearish"] = 100 - out["bullish"]
            out["basis_agrees"] = False
        else:
            out["basis_agrees"] = True
    return out


def oi_snapshot(key, symbol, today_iso, expiry_cache):
    """Nearest-expiry option-chain OI-change lean for one index (read-only). None on any problem."""
    if window_oi_change is None:
        return None
    exp = expiry_cache.get(symbol)
    if not exp or exp[0] != today_iso:
        dates = post("/clone-v2/market/options/expiries", {"symbol": symbol}, key).get("expiries") or []
        nxt = next((d for d in dates if isinstance(d, str) and d >= today_iso), None)
        if not nxt:
            return None
        exp = (today_iso, nxt)
        expiry_cache[symbol] = exp
    metrics = post("/clone-v2/market/options/chain", {"symbol": symbol, "expiry": exp[1]}, key)
    share, reason = window_oi_change(metrics)
    row = {"expiry": exp[1], "pcr": metrics.get("pcr"), "max_pain": metrics.get("max_pain"), "reason": reason}
    if share:
        row.update(bullish=share[0], bearish=share[1])
    return row


def news_refresh(now, opener=None):
    """Every 10 min: Google News RSS headline cue for the 3 indices. Read-only, display + ledger only."""
    if v3_news_cue is None or now - NEWS_STATE["at"] < NEWS_EVERY_S:
        return NEWS_STATE["cue"]
    NEWS_STATE["at"] = now
    cue = {}
    opener = opener or urllib.request.build_opener()
    for sym, query in v3_news_cue.NEWS_QUERIES.items():
        try:
            url = "https://news.google.com/rss/search?" + urllib.parse.urlencode(
                {"q": query + " when:1d", "hl": "en-IN", "gl": "IN", "ceid": "IN:en"})
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 BOT KING personal headline reader"})
            with opener.open(req, timeout=8) as resp:
                raw = resp.read(262_145)
            if len(raw) > 262_144:
                continue
            items = v3_news_cue.parse_news_rss(raw, "Google News RSS", now)
            row = v3_news_cue.headline_signal(items)
            row["t"] = int(now)
            cue[sym] = row
        except Exception:
            continue  # one feed failing never stops the runner
    if cue:
        NEWS_STATE["cue"] = cue
    return NEWS_STATE["cue"]


def oi_morning_step(ledger, out, now, field="oi_lean", book_key="oi_morning", stat_key="oi_stats"):
    """Pure: record the first decisive OI lean after 09:20 IST per index, score it vs the close (>=15:20 IST).

    Scored only when the lean was decisive (|bullish-50| >= 10); balanced readings are not scored.
    """
    ist = datetime.fromtimestamp(now, IST)
    day, hm = ist.date().isoformat(), ist.hour * 60 + ist.minute
    book = ledger.setdefault(book_key, {})
    stats = ledger.setdefault(stat_key, {})
    for old in [d for d in book if d != day]:
        if old < day:
            book.pop(old, None)
    today = book.setdefault(day, {})
    for symbol in sorted(set(out.get(field) or {}) | set(today)):
        row = (out.get(field) or {}).get(symbol) or {}
        spot = (out.get("spot") or {}).get(symbol)
        if (symbol not in today and 560 <= hm < 700 and type(spot) in (int, float)
                and type(row.get("bullish")) in (int, float)):
            today[symbol] = {"bullish": row["bullish"], "spot": float(spot), "at": int(now)}
        rec = today.get(symbol)
        if rec and not rec.get("scored") and hm >= 920 and type(spot) in (int, float):
            rec["scored"] = True
            if abs(rec["bullish"] - 50) >= 10 and spot != rec["spot"]:
                st = stats.setdefault(symbol, {"n": 0, "hits": 0})
                st["n"] += 1
                st["hits"] += int((spot > rec["spot"]) == (rec["bullish"] > 50))
    return ledger


def cycle(key, now, minute_index, previous):
    out = {"generated_utc": datetime.fromtimestamp(now, timezone.utc).isoformat(),
           "market_open": bool(regular_equity_hours(datetime.fromtimestamp(now, timezone.utc))),
           "live_orders_enabled": False, "mode": "READ_ONLY_ANALYSIS", "symbols": {}}
    if not out["market_open"]:
        out["note"] = "market closed; no provider requests"
        return out
    quotes = post("/clone-v2/market/quotes", {"symbols": list(SYMBOLS)}, key).get("quotes", {})
    today = datetime.fromtimestamp(now, IST).date().isoformat()
    m_bars = {}
    out["spot"] = {s: (quotes.get(s) or {}).get("ltp") for s in SYMBOLS
                   if type((quotes.get(s) or {}).get("ltp")) in (int, float)}
    try:
        carried = (previous or {}).get("oi_lean") or {}
        if minute_index % 5 == 0 or not carried:
            for s in SYMBOLS:
                try:
                    snap = oi_snapshot(key, s, today, OI_EXPIRY_CACHE)
                except Exception:
                    snap = None
                if snap:
                    out.setdefault("oi_lean", {})[s] = dict(snap, t=int(now))
        elif carried:
            out["oi_lean"] = carried
    except Exception:
        pass  # OI lean is best-effort
    idx_bars = {}
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
                    idx_bars[symbol] = response.get("bars")
                    lean = m_lean(response.get("bars"))
                    ltp = (quotes.get(symbol) or {}).get("ltp")
                    if lean and type(ltp) in (int, float):
                        out.setdefault("m_lean", {})[symbol] = dict(lean, ltp=float(ltp), mv=min_move(response.get("bars"), ltp, 20))
                        m_bars[symbol] = response.get("bars")
                    if type(ltp) in (int, float):
                        for hz, hl in m_leans(response.get("bars")).items():
                            if hz != "20" and hl:
                                out.setdefault("m_horizons", {}).setdefault(symbol, {})[hz] = dict(hl, ltp=float(ltp), mv=min_move(response.get("bars"), ltp, int(hz)))
                out["symbols"][symbol][frame] = evaluate(symbol, frame, response, quotes.get(symbol), now)
            except urllib.error.HTTPError as exc:
                out["symbols"][symbol][frame] = {"state": "ERROR", "reason": "HTTP %s" % exc.code}
            except Exception as exc:  # keep the loop alive; never print payloads
                out["symbols"][symbol][frame] = {"state": "ERROR", "reason": type(exc).__name__}
    try:
        carried_f = (previous or {}).get("fut_lean") or {}
        if minute_index % 5 == 0 or not carried_f:
            futures = (json.loads(FUTURES_FILE.read_text(encoding="utf-8")).get("futures")
                       if FUTURES_FILE.exists() else {}) or {}
            for s in SYMBOLS:
                try:
                    snap = fut_snapshot(key, s, today, futures, idx_bars.get(s))
                except Exception:
                    snap = None
                if snap:
                    out.setdefault("fut_lean", {})[s] = dict(snap, t=int(now))
        elif carried_f:
            out["fut_lean"] = carried_f
    except Exception:
        pass  # futures lean is best-effort
    try:   # B253: heavy-weight constituents lean per index (candles every 5 min, carried between)
        carried_h = (previous or {}).get("heavy_lean") or {}
        if heavy_lean is None:
            pass
        elif minute_index % 5 == 0 or not carried_h:
            cache = {}
            for s in SYMBOLS:
                names = [n for n in constituents(s)]
                for n in names:
                    if n not in cache:
                        try:
                            cache[n] = with_integrity(post("/clone-v2/market/candles", {
                                "symbol": n, "interval": 1, "from_date": today, "to_date": today}, key)).get("bars")
                        except Exception:
                            cache[n] = None
                hl = heavy_lean(s, cache)
                if hl:
                    out.setdefault("heavy_lean", {})[s] = dict(hl, t=int(now))
        elif carried_h:
            out["heavy_lean"] = carried_h
    except Exception:
        pass  # heavy-weight lean is best-effort
    for symbol, lean in (out.get("m_lean") or {}).items():
        try:
            fl = (out.get("fut_lean") or {}).get(symbol) or {}
            fbias = ("BULLISH" if fl.get("bullish", 50) >= 55 else "BEARISH" if fl.get("bullish", 50) <= 45 else None)
            frame_b = [(r or {}).get("bias") for r in (out["symbols"].get(symbol) or {}).values()
                       if (r or {}).get("bias") in ("BULLISH", "BEARISH")]
            # B252: 1m/3m/5m frames share one candle source -> ONE independent technical vote (majority)
            tech_b = ("BULLISH" if frame_b.count("BULLISH") > frame_b.count("BEARISH") else
                      "BEARISH" if frame_b.count("BEARISH") > frame_b.count("BULLISH") else None)
            hv = (out.get("heavy_lean") or {}).get(symbol) or {}
            hbias = ("BULLISH" if hv.get("bullish", 50) >= 60 else "BEARISH" if hv.get("bullish", 50) <= 40 else None)
            biases = [b for b in (tech_b, fbias, hbias) if b]
            ctx = m_context(lean, m_bars.get(symbol), biases, now, (out.get("oi_lean") or {}).get(symbol),
                            prev_close(key, symbol, today))
            if ctx:
                lean["context"] = ctx
        except Exception:
            pass  # context is best-effort
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


PREV_CLOSE = {}   # (symbol, today) -> previous session close; best-effort, fetched once per day


def prev_close(key, symbol, today):
    ck = (symbol, today)
    if ck in PREV_CLOSE:
        return PREV_CLOSE[ck]
    val = None
    try:
        from datetime import date, timedelta as _td
        d0 = date.fromisoformat(today)
        resp = with_integrity(post("/clone-v2/market/candles", {
            "symbol": symbol, "interval": 1, "from_date": (d0 - _td(days=6)).isoformat(),
            "to_date": (d0 - _td(days=1)).isoformat()}, key))
        for b in reversed(resp.get("bars") or []):
            if type(b[4]) in (int, float) and b[4] > 0:
                val = float(b[4]); break
    except Exception:
        val = None
    PREV_CLOSE[ck] = val
    return val


def ledger_step(ledger, out, now):
    """Pure: record M predictions every 5 min, score them after 20 min. Mutates and returns ledger."""
    ledger.setdefault("pending", []); ledger.setdefault("stats", {}); ledger.setdefault("last_t", {})
    if not out.get("market_open"):
        return ledger
    for symbol, lean in (out.get("m_lean") or {}).items():
        if now - ledger["last_t"].get(symbol, 0) >= LEDGER_EVERY_S and lean.get("lean") in ("BULLISH", "BEARISH", "NEUTRAL"):
            row_ = {"t": int(now), "symbol": symbol, "lean": lean["lean"], "entry": lean["ltp"],
                    "mv": lean.get("mv", 0.0), "s": lean.get("strength", 0.0)}
            ctx_ = lean.get("context") or {}
            if ctx_:
                row_["w"] = ctx_.get("window"); row_["c"] = "%d/%d" % (ctx_.get("agree", 0), ctx_.get("total", 0))
            ledger["pending"].append(row_)
            ledger["last_t"][symbol] = int(now)
    for symbol, hz_map in (out.get("m_horizons") or {}).items():
        for hz, lean in (hz_map or {}).items():
            key = symbol + "@" + hz
            if now - ledger["last_t"].get(key, 0) >= LEDGER_EVERY_S and lean.get("lean") in ("BULLISH", "BEARISH", "NEUTRAL"):
                ledger["pending"].append({"t": int(now), "symbol": symbol, "lean": lean["lean"],
                                          "entry": lean["ltp"], "h": int(hz), "mv": lean.get("mv", 0.0),
                                          "s": lean.get("strength", 0.0), "w": window_of(now)})
                ledger["last_t"][key] = int(now)
    keep = []
    for row in ledger["pending"]:
        hz = row.get("h", LEDGER_HORIZON_S // 60)
        if now - row["t"] < hz * 60:
            keep.append(row); continue
        price = ((out.get("m_lean") or {}).get(row["symbol"]) or {}).get("ltp")
        hit = resolve_prediction(row["entry"], row["lean"], price, row.get("mv", 0.0)) if price is not None else None
        if hit is None:
            ledger["flat"] = ledger.get("flat", 0) + 1   # neutral / noise-sized / no price: counted, not scored
            continue
        skey = row["symbol"] if "h" not in row else row["symbol"] + "@" + str(row["h"])
        st = ledger["stats"].setdefault(skey, {"n": 0, "hits": 0, "up": 0})
        st["n"] += 1; st["hits"] += int(bool(hit))
        went_up = (price > row["entry"])
        st["up"] = st.get("up", 0) + int(went_up)   # B252 baseline: how often the market simply rose
        hzv = row.get("h", LEDGER_HORIZON_S // 60)
        gk_list = [("sb", "%s:%s" % (hzv, strength_band(row.get("s", 0))))]
        if "h" not in row:
            gk_list += [("w", row.get("w")), ("c", row.get("c"))]
        elif hzv == 30 and row.get("w"):
            gk_list += [("w30", row.get("w"))]
        for gk, gv in gk_list:
            if gv:
                g = ledger.setdefault("groups", {}).setdefault(gk + ":" + str(gv), {"n": 0, "hits": 0})
                g["n"] += 1; g["hits"] += int(bool(hit))
    ledger["pending"] = keep[-400:]
    return ledger


VOTE_MIN_N = 30          # scored samples a box needs before it may vote
VOTE_MIN_RATE = 55.0     # measured hit-rate (%) a box needs before it may vote


OVERLAP_30M = 6          # samples every 5 min on a 30-min horizon overlap; ~1/6 is independent evidence


def _gate_row(n_eff, hits_eff, base=None):
    rate = round(100 * hits_eff / n_eff, 1) if n_eff else None
    low = wilson_low(hits_eff, n_eff) if n_eff else None
    edge = round(rate - base, 1) if (rate is not None and base is not None) else None
    ok = bool(n_eff >= VOTE_MIN_N and rate is not None and rate >= VOTE_MIN_RATE
              and low is not None and low >= 50.0 and (edge is None or edge > 0))
    return {"n": n_eff, "hit_rate": rate, "wilson_low": low, "baseline": base, "edge": edge,
            "need_n": VOTE_MIN_N, "need_rate": VOTE_MIN_RATE, "eligible": ok}


def vote_gate(ledger, replay=None):
    """Pure evidence gate per box (B252): enough INDEPENDENT scored samples, hit-rate above the bar,
    the 90% lower confidence bound (Wilson) at or above 50%, and an edge over the market-drift baseline.

    M: 30-minute rows (overlap divided by 6, live and replay alike), pooled, plus per-symbol and per-window rows.
    Baseline = share of the majority direction among scored moves (what always saying 'up' or 'down' would score).
    O/N/F: daily morning-lean ledgers (one sample per day, no overlap, no baseline).
    """
    def agg(stats, match=None):
        n = hits = up = 0
        for k, v in (stats or {}).items():
            if match is None or match(k):
                n += int(v.get("n", 0)); hits += int(v.get("hits", 0)); up += int(v.get("up", 0))
        return n, hits, up

    out = {}
    n, hits, up = agg(ledger.get("stats"), lambda k: k.endswith("@30"))
    rep = ((replay or {}).get("m_hit") or {}).get("30m") or {}
    if type(rep.get("n")) is int and type(rep.get("hit_rate")) in (int, float) and rep["n"] > 0:
        n += rep["n"]; hits += round(rep["n"] * rep["hit_rate"] / 100)
        if type(rep.get("up_rate")) in (int, float):
            up += round(rep["n"] * rep["up_rate"] / 100)
        else:
            up += rep["n"] // 2   # drift unknown: assume 50/50
    n_eff, h_eff, u_eff = n // OVERLAP_30M, round(hits / OVERLAP_30M), round(up / OVERLAP_30M)
    base = round(100 * max(u_eff, n_eff - u_eff) / n_eff, 1) if n_eff else None
    out["M"] = _gate_row(n_eff, h_eff, base)
    by_sym = {}
    for k, v in (ledger.get("stats") or {}).items():
        if k.endswith("@30"):
            sn, sh, su = int(v.get("n", 0)) // OVERLAP_30M, round(int(v.get("hits", 0)) / OVERLAP_30M), round(int(v.get("up", 0)) / OVERLAP_30M)
            sb = round(100 * max(su, sn - su) / sn, 1) if sn else None
            by_sym[k[:-3]] = _gate_row(sn, sh, sb)
    out["M_symbols"] = by_sym
    by_win = {}
    for k, v in (ledger.get("groups") or {}).items():
        if k.startswith("w30:"):
            wn, wh = int(v.get("n", 0)) // OVERLAP_30M, round(int(v.get("hits", 0)) / OVERLAP_30M)
            by_win[k[4:]] = _gate_row(wn, wh, None)
    out["M_windows"] = by_win
    for box in ("T", "C", "H"):
        r_ = (((replay or {}).get("box_hit") or {}).get(box) or {}).get("30m") or {}
        if type(r_.get("n")) is int and r_["n"] > 0 and type(r_.get("hit_rate")) in (int, float):
            bn, bh = r_["n"] // OVERLAP_30M, round(r_["n"] * r_["hit_rate"] / 100 / OVERLAP_30M)
            bu_ = round((r_.get("up_rate") or 50) * bn / 100)
            out[box] = _gate_row(bn, bh, round(100 * max(bu_, bn - bu_) / bn, 1) if bn else None)
        else:
            out[box] = _gate_row(0, 0, None)
    for box, field in (("O", "oi_stats"), ("N", "news_stats"), ("F", "fut_stats"), ("H_morning", "heavy_stats")):
        n, hits, _ = agg(ledger.get(field))
        out[box] = _gate_row(n, hits, None)
    return out


def ledger_summary(ledger):
    rows = {}
    for symbol, st in (ledger.get("stats") or {}).items():
        n = st.get("n", 0)
        rows[symbol] = {"n": n, "hits": st.get("hits", 0),
                        "hit_rate": round(100 * st.get("hits", 0) / n, 1) if n else None}
    groups = {k: {"n": v.get("n", 0), "hit_rate": round(100 * v.get("hits", 0) / v["n"], 1) if v.get("n") else None}
              for k, v in (ledger.get("groups") or {}).items()}
    oi = {k: {"n": v.get("n", 0), "hit_rate": round(100 * v.get("hits", 0) / v["n"], 1) if v.get("n") else None}
          for k, v in (ledger.get("oi_stats") or {}).items()}
    news = {k: {"n": v.get("n", 0), "hit_rate": round(100 * v.get("hits", 0) / v["n"], 1) if v.get("n") else None}
            for k, v in (ledger.get("news_stats") or {}).items()}
    fut = {k: {"n": v.get("n", 0), "hit_rate": round(100 * v.get("hits", 0) / v["n"], 1) if v.get("n") else None}
           for k, v in (ledger.get("fut_stats") or {}).items()}
    return {"horizon_minutes": LEDGER_HORIZON_S // 60, "scored": rows, "groups": groups, "oi_morning": oi, "news_morning": news, "fut_morning": fut,
            "heavy_morning": {k: {"n": v.get("n", 0), "hit_rate": round(100 * v.get("hits", 0) / v["n"], 1) if v.get("n") else None}
                              for k, v in (ledger.get("heavy_stats") or {}).items()},
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
FUTURES_FILE = Path(os.environ.get("BOTKING_FUTURES_CONTRACTS", str(OUT_FILE.parent / "futures-contracts.json")))


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


def parse_future_contracts(lines, today_iso):
    """Pure: scrip-master lines -> {"NIFTY": ["NSE_FNO", security_id, lot, "2026-12-30"]} nearest index future."""
    best = {}
    for row in csv.DictReader(lines):
        if row.get("SEM_INSTRUMENT_NAME") != "FUTIDX":
            continue
        name = str(row.get("SEM_TRADING_SYMBOL", "")).split("-")[0].strip().upper()
        exch = str(row.get("SEM_EXM_EXCH_ID", "")).strip().upper()
        expiry = str(row.get("SEM_EXPIRY_DATE", ""))[:10]
        try:
            sid = int(row.get("SEM_SMST_SECURITY_ID"))
            lot = int(float(row.get("SEM_LOT_UNITS")))
        except (TypeError, ValueError):
            continue
        if (name not in CONTRACT_UNDERLYINGS or exch not in ("NSE", "BSE") or len(expiry) != 10
                or expiry < today_iso or lot <= 0):
            continue
        if name not in best or expiry < best[name][3]:
            best[name] = [exch + "_FNO", sid, lot, expiry]
    return best


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
            try:
                futs = parse_future_contracts(io.StringIO(text, newline=""), today)
                if futs:
                    atomic_write(FUTURES_FILE, json.dumps({"fetched": int(now), "futures": futs}) + "\n")
            except Exception:
                pass  # futures list is best-effort
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
                nc = news_refresh(now)
                if nc:
                    out["news_cue"] = nc
            except Exception:
                pass  # headline cue is best-effort
            try:
                ledger = json.loads(LEDGER_FILE.read_text(encoding="utf-8")) if LEDGER_FILE.exists() else {}
                ledger = ledger_step(ledger if isinstance(ledger, dict) else {}, out, now)
                ledger = oi_morning_step(ledger, out, now)
                ledger = oi_morning_step(ledger, out, now, "news_cue", "news_morning", "news_stats")
                ledger = oi_morning_step(ledger, out, now, "fut_lean", "fut_morning", "fut_stats")
                ledger = oi_morning_step(ledger, out, now, "heavy_lean", "heavy_morning", "heavy_stats")
                atomic_write(LEDGER_FILE, json.dumps(ledger) + "\n")
                out["m_ledger"] = ledger_summary(ledger)
                try:
                    rp = Path(os.environ.get("BOTKING_REPLAY_OUT", str(OUT_FILE.parent / "replay-latest.json")))
                    out["vote_gate"] = vote_gate(ledger, json.loads(rp.read_text(encoding="utf-8")) if rp.exists() else None)
                except Exception:
                    pass  # gate is informational until the phone wiring reads it
            except Exception:
                pass  # ledger is best-effort; never stop the runner
            try:
                out["lot_sizes"] = load_lot_sizes(now)
                cdata = json.loads(CONTRACT_FILE.read_text(encoding="utf-8")) if CONTRACT_FILE.exists() else {}
                out["lot_by_expiry"] = lot_by_expiry(cdata.get("contracts") if isinstance(cdata, dict) else {})
            except Exception:
                pass  # lot sizes are best-effort
            try:
                au = Path("/home/opc/botking-clone-v2-private/autoupdate-status.json")
                if au.exists():
                    out["autoupdate"] = json.loads(au.read_text(encoding="utf-8"))
            except Exception:
                pass  # update status is informational only
            try:
                rp = Path(os.environ.get("BOTKING_REPLAY_OUT", str(OUT_FILE.parent / "replay-latest.json")))
                if rp.exists():
                    out["replay"] = json.loads(rp.read_text(encoding="utf-8"))
            except Exception:
                pass  # replay summary is informational only
            atomic_write(OUT_FILE, cap_signal_size(out) + "\n")
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
