"""B244 server-side PAPER position manager (hold / sell / stop-loss / target).

Paper only. This module never talks to Dhan and never places an order of any
kind. It keeps simulated positions in a small JSON file and closes them when a
supplied last price crosses the stop-loss or target. A live adapter would be a
separate, fail-closed module and does not exist.
"""
import json, math, os, threading, time, uuid

MAX_OPEN = 10
MAX_QTY = 100000
MAX_LEVELS = 3
MAX_TOTAL_LOTS = 50
LIVE_ORDERS_ENABLED = False  # constant; nothing in this module reads a switch


WINDOWS = (("OPEN_VOLATILE", 555, 585), ("SETTLING", 585, 600), ("BEST_TREND", 600, 690),
           ("MIDDAY_QUIET", 690, 810), ("AFTERNOON", 810, 900), ("LATE_RISKY", 900, 931))


def entry_window(ts):
    """IST time-window label for an epoch timestamp (general market-hours table; same table as the phone)."""
    from datetime import datetime, timezone, timedelta
    t = datetime.fromtimestamp(ts, timezone(timedelta(hours=5, minutes=30)))
    m = t.hour * 60 + t.minute
    for name, a, b in WINDOWS:
        if a <= m < b:
            return name
    return "OTHER"


class PaperEngine:
    def __init__(self, path=None, clock=time.time):
        self.path = path
        self.clock = clock
        self.lock = threading.RLock()
        self.positions = []
        self.last_price = {}
        self.started_at = clock()
        self.last_eval_at = None
        self.last_error = None
        self._load()

    # ---- persistence ----
    def _load(self):
        if not self.path or not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data.get("positions"), list):
                self.positions = [p for p in data["positions"] if isinstance(p, dict)]
        except (OSError, ValueError):
            self.last_error = "state file unreadable; started empty"

    def _save(self):
        if not self.path:
            return
        tmp = self.path + ".tmp"
        try:
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump({"positions": self.positions}, fh)
            os.replace(tmp, self.path)
        except OSError:
            self.last_error = "state file not writable"

    # ---- helpers ----
    @staticmethod
    def _num(v):
        return type(v) in (int, float) and math.isfinite(v) and v > 0

    def open_positions(self):
        return [p for p in self.positions if p.get("status") == "OPEN"]

    # ---- commands ----
    def open(self, symbol, side, qty, entry, stop, target=None):
        with self.lock:
            if not isinstance(symbol, str) or not symbol or len(symbol) > 32:
                raise ValueError("symbol required")
            if side not in ("BUY", "SELL"):
                raise ValueError("side must be BUY or SELL")
            if type(qty) is not int or not 1 <= qty <= MAX_QTY:
                raise ValueError("qty out of range")
            if not self._num(entry) or not self._num(stop):
                raise ValueError("entry and stop-loss are required")
            if target is not None and not self._num(target):
                raise ValueError("target invalid")
            if side == "BUY" and not (stop < entry and (target is None or target > entry)):
                raise ValueError("BUY needs stop below and target above entry")
            if side == "SELL" and not (stop > entry and (target is None or target < entry)):
                raise ValueError("SELL needs stop above and target below entry")
            if len(self.open_positions()) >= MAX_OPEN:
                raise ValueError("too many open paper positions")
            pos = {"id": uuid.uuid4().hex[:10], "symbol": symbol, "side": side,
                   "qty": qty, "entry": float(entry), "stop": float(stop),
                   "target": None if target is None else float(target),
                   "opened_at": self.clock(), "status": "OPEN",
                   "mode": "PAPER"}
            self.positions.append(pos)
            self._save()
            return dict(pos)

    def open_option(self, label, instrument, lot_size, lots, entry, stop, target,
                    levels=None, target_avg=None, expires_at=None, stop_avg=None):
        """B249: paper BUY of ONE option contract with optional averaging levels.

        Only BUY (long premium). Averaging adds lots to the SAME contract when its
        premium falls to an owner-typed level; the stop-loss is a fixed premium
        price that is never removed; two targets: one if never averaged, one after.
        """
        with self.lock:
            if not isinstance(label, str) or not label or len(label) > 40:
                raise ValueError("label required")
            if (not isinstance(instrument, dict) or not isinstance(instrument.get("seg"), str)
                    or type(instrument.get("sid")) is not int):
                raise ValueError("instrument required")
            if type(lot_size) is not int or not 1 <= lot_size <= MAX_QTY:
                raise ValueError("lot size invalid")
            if type(lots) is not int or not 1 <= lots <= MAX_TOTAL_LOTS:
                raise ValueError("lots out of range")
            if not self._num(entry) or (stop is not None and not self._num(stop)) or (target is not None and not self._num(target)):
                raise ValueError("entry must be a number; stop-loss and target must be numbers or left empty (editable later)")
            if (stop is not None and stop >= entry) or (target is not None and target <= entry):
                raise ValueError("BUY needs stop below and target above entry")
            clean = []
            for lv in (levels or []):
                if (not isinstance(lv, dict) or not self._num(lv.get("price"))
                        or type(lv.get("lots")) is not int or not 1 <= lv["lots"] <= MAX_TOTAL_LOTS):
                    raise ValueError("averaging level invalid")
                price = float(lv["price"])
                if not ((stop is None or stop < price) and price < entry):
                    raise ValueError("averaging level must be above stop-loss and below entry")
                clean.append({"price": price, "lots": lv["lots"]})
            if len(clean) > MAX_LEVELS:
                raise ValueError("too many averaging levels")
            clean.sort(key=lambda x: -x["price"])
            if len({x["price"] for x in clean}) != len(clean):
                raise ValueError("duplicate averaging level")
            if lots + sum(x["lots"] for x in clean) > MAX_TOTAL_LOTS:
                raise ValueError("total lots too high")
            ta = None
            if target_avg is not None:
                if not self._num(target_avg):
                    raise ValueError("averaged target invalid")
                ta = float(target_avg)
                if clean:
                    first_avg = (entry * lots + clean[0]["price"] * clean[0]["lots"]) / (lots + clean[0]["lots"])
                    if ta <= first_avg:
                        raise ValueError("averaged target must be above the averaged price")
                else:
                    raise ValueError("averaged target needs an averaging level")
            sa = None
            if stop_avg is not None:
                if not clean:
                    raise ValueError("averaged stop-loss needs an averaging level")
                if not self._num(stop_avg) or not 0 < stop_avg < clean[-1]["price"]:
                    raise ValueError("averaged stop-loss must be below the lowest averaging level")
                sa = float(stop_avg)
            if len(self.open_positions()) >= MAX_OPEN:
                raise ValueError("too many open paper positions")
            qty = lots * lot_size
            pos = {"id": uuid.uuid4().hex[:10], "symbol": label, "side": "BUY", "kind": "OPTION",
                   "instrument": {"seg": instrument["seg"], "sid": instrument["sid"]},
                   "lot_size": lot_size, "lots": lots, "qty": qty, "entry": float(entry),
                   "stop": None if stop is None else float(stop), "target": None if target is None else float(target), "target_if_averaged": ta, "stop_if_averaged": sa,
                   "levels": clean, "level_expires_at": expires_at, "averaged": False,
                   "fills": [{"price": float(entry), "qty": qty, "lots": lots, "t": self.clock()}],
                   "opened_at": self.clock(), "window": entry_window(self.clock()), "status": "OPEN", "mode": "PAPER"}
            self.positions.append(pos)
            self._save()
            return dict(pos)

    def open_instruments(self):
        with self.lock:
            return {p["symbol"]: (p["instrument"]["seg"], p["instrument"]["sid"])
                    for p in self.open_positions() if isinstance(p.get("instrument"), dict)}

    def _close(self, pos, price, reason):
        pos["status"] = "CLOSED"
        pos["exit"] = float(price)
        pos["reason"] = reason
        pos["closed_at"] = self.clock()
        sign = 1 if pos["side"] == "BUY" else -1
        if pos.get("fills"):
            pos["pnl"] = round(sum((pos["exit"] - f["price"]) * f["qty"] for f in pos["fills"]), 2)
        else:
            pos["pnl"] = round(sign * (pos["exit"] - pos["entry"]) * pos["qty"], 2)

    def edit_levels(self, pos_id, changes):
        """B255: edit the PROTECTION of an open position (stop, target, averaged stop/target, averaging levels).
        The trade itself (side, quantity, entry, fills) is never editable: only hold or exit."""
        allowed = {"stop", "target", "stop_if_averaged", "target_if_averaged", "levels"}
        if not isinstance(changes, dict) or not changes or set(changes) - allowed:
            raise ValueError("only stop, target, averaged stop/target and averaging levels can be edited")
        with self.lock:
            pos = next((p for p in self.open_positions() if p["id"] == pos_id), None)
            if pos is None:
                raise KeyError("open position not found")
            buy = pos["side"] == "BUY"
            ref = (pos.get("fills") or [{"price": pos["entry"]}])[0]["price"]   # first fill price
            new = {k: changes[k] for k in changes}
            for k in ("stop", "target", "stop_if_averaged", "target_if_averaged"):
                if k in new and new[k] is not None and not self._num(new[k]):
                    raise ValueError(k + " invalid")
            if "stop" in new and new["stop"] is None:
                raise ValueError("stop-loss can be changed but not removed")
            stop = float(new["stop"]) if "stop" in new else pos.get("stop")
            target = (None if new.get("target") is None else float(new["target"])) if "target" in new else pos.get("target")
            if stop is not None and not ((stop < ref) if buy else (stop > ref)):
                raise ValueError("stop-loss must be on the loss side of the entry")
            if target is not None and not ((target > ref) if buy else (target < ref)):
                raise ValueError("target must be on the profit side of the entry")
            if "levels" in new:
                clean = []
                for lv in (new["levels"] or []):
                    if (not isinstance(lv, dict) or not self._num(lv.get("price"))
                            or type(lv.get("lots")) is not int or not 1 <= lv["lots"] <= MAX_TOTAL_LOTS):
                        raise ValueError("averaging level invalid")
                    price = float(lv["price"])
                    if stop is not None and not (stop < price < ref):
                        raise ValueError("averaging level must be above stop-loss and below entry")
                    clean.append({"price": price, "lots": lv["lots"]})
                if len(clean) > MAX_LEVELS or len({x["price"] for x in clean}) != len(clean):
                    raise ValueError("too many or duplicate averaging levels")
                if pos.get("lots", 0) + sum(x["lots"] for x in clean) > MAX_TOTAL_LOTS:
                    raise ValueError("total lots too high")
                clean.sort(key=lambda x: -x["price"])
                pos["levels"] = clean
            for k in ("stop_if_averaged", "target_if_averaged"):
                if k in new:
                    pos[k] = None if new[k] is None else float(new[k])
            pos["stop"] = stop
            pos["target"] = target
            pos.setdefault("edits", []).append({"t": self.clock(), "fields": sorted(changes)})
            del pos["edits"][:-10]
            self._save()
            return dict(pos)

    def close(self, pos_id, price=None):
        with self.lock:
            for p in self.open_positions():
                if p["id"] == pos_id:
                    px = price if self._num(price) else self.last_price.get(p["symbol"])
                    if not self._num(px):
                        raise ValueError("no price available to close")
                    self._close(p, px, "MANUAL")
                    self._save()
                    return dict(p)
            raise KeyError("open position not found")

    def observe(self, prices):
        """Feed last prices; closes positions that crossed stop or target."""
        closed = []
        with self.lock:
            for sym, px in (prices or {}).items():
                if self._num(px):
                    self.last_price[sym] = float(px)
            for p in self.open_positions():
                px = self.last_price.get(p["symbol"])
                if px is None:
                    continue
                buy = p["side"] == "BUY"
                stp = p["stop"]
                if p.get("averaged") and p.get("stop_if_averaged"):
                    stp = p["stop_if_averaged"]
                if stp is not None and ((px <= stp) if buy else (px >= stp)):
                    self._close(p, stp, "STOP_LOSS")
                    closed.append(dict(p))
                    continue
                if p.get("levels"):
                    self._work_levels(p, px)
                tgt = p["target"]
                if p.get("averaged") and p.get("target_if_averaged"):
                    tgt = p["target_if_averaged"]
                if tgt is not None and ((px >= tgt) if buy else (px <= tgt)):
                    self._close(p, tgt, "TARGET")
                else:
                    continue
                closed.append(dict(p))
            self.last_eval_at = self.clock()
            if closed or self._level_dirty:
                self._save()
                self._level_dirty = False
        return closed

    _level_dirty = False

    def _work_levels(self, p, px):
        """Fill averaging levels the premium has reached (at the level price); drop expired ones."""
        exp = p.get("level_expires_at")
        if exp is not None and self.clock() > exp:
            p["levels"] = []
            self._level_dirty = True
            return
        while p["levels"] and px <= p["levels"][0]["price"]:
            lv = p["levels"].pop(0)
            qty = lv["lots"] * p["lot_size"]
            p["fills"].append({"price": lv["price"], "qty": qty, "lots": lv["lots"], "t": self.clock()})
            total = sum(f["qty"] for f in p["fills"])
            p["entry"] = round(sum(f["price"] * f["qty"] for f in p["fills"]) / total, 4)
            p["qty"] = total
            p["lots"] = sum(f["lots"] for f in p["fills"])
            p["averaged"] = True
            self._level_dirty = True

    def heartbeat(self):
        with self.lock:
            now = self.clock()
            opens = self.open_positions()
            return {"mode": "PAPER", "live_orders_enabled": LIVE_ORDERS_ENABLED,
                    "engine_started_at": self.started_at,
                    "uptime_seconds": round(now - self.started_at, 1),
                    "last_eval_at": self.last_eval_at,
                    "last_eval_age_seconds": (None if self.last_eval_at is None
                                              else round(now - self.last_eval_at, 1)),
                    "open_count": len(opens),
                    "closed_count": len(self.positions) - len(opens),
                    "open_symbols": sorted({p["symbol"] for p in opens}),
                    "last_error": self.last_error}

    def window_stats(self):
        """Measured outcomes of CLOSED paper trades by entry time-window (informational, owner's own data)."""
        out = {}
        with self.lock:
            for p in self.positions:
                if p.get("status") != "CLOSED":
                    continue
                w = p.get("window") or "OTHER"
                st = out.setdefault(w, {"n": 0, "target": 0, "stop": 0, "pnl": 0.0})
                st["n"] += 1
                st["target"] += p.get("reason") == "TARGET"
                st["stop"] += p.get("reason") == "STOP_LOSS"
                st["pnl"] = round(st["pnl"] + float(p.get("pnl") or 0), 2)
        return out

    def state(self):
        with self.lock:
            return {"heartbeat": self.heartbeat(), "window_stats": self.window_stats(),
                    "positions": [dict(p) for p in self.positions[-100:]]}


def scenarios(entry, lots, lot_size, levels, stop, target, target_avg, stop_avg=None):
    """B250 single source of truth for the rupee view of an option BUY with averaging.

    Same inputs the engine validates in open_option. Returns {"ok":bool,"reason":str,"rows":[...]}.
    The phone shows this; its own copy of the maths is only an offline estimate.
    """
    num = PaperEngine._num
    try:
        if not (num(entry) and num(stop) and num(target) and stop < entry < target):
            return {"ok": False, "reason": "stop below entry below target required", "rows": []}
        if type(lots) is not int or not 1 <= lots <= MAX_TOTAL_LOTS or type(lot_size) is not int or lot_size < 1:
            return {"ok": False, "reason": "lots/lot size invalid", "rows": []}
        lv = []
        for x in (levels or []):
            if not (num(x.get("price")) and type(x.get("lots")) is int and x["lots"] >= 1 and stop < x["price"] < entry):
                return {"ok": False, "reason": "averaging level invalid", "rows": []}
            lv.append((float(x["price"]), x["lots"]))
        lv.sort(key=lambda t: -t[0])
        qty, cost, n = lots * lot_size, entry * lots * lot_size, lots
        ta = float(target_avg) if num(target_avg) else None
        sa = None
        if num(stop_avg):
            if not lv or not 0 < stop_avg < lv[-1][0]:
                return {"ok": False, "reason": "averaged stop below lowest level required", "rows": []}
            sa = float(stop_avg)

        def row(label, n_lots, q, c, tgt, stp):
            avg = c / q
            return {"label": label, "lots": n_lots, "qty": q, "avg": round(avg, 2), "invested": round(c, 2),
                    "stop": stp, "loss_at_stop": round((avg - stp) * q, 2), "target": tgt,
                    "profit_at_target": round((tgt - avg) * q, 2) if tgt and tgt > avg else None}
        rows = [row("no averaging", lots, qty, cost, float(target), float(stop))]
        for i, (p_, k) in enumerate(lv, 1):
            n += k; qty += k * lot_size; cost += p_ * k * lot_size
            rows.append(row("after level %d (%g)" % (i, p_), n, qty, cost, ta if ta else float(target), sa if sa else float(stop)))
        return {"ok": True, "reason": "", "rows": rows}
    except (TypeError, ValueError, AttributeError):
        return {"ok": False, "reason": "invalid input", "rows": []}
