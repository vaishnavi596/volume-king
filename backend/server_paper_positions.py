"""B244 server-side PAPER position manager (hold / sell / stop-loss / target).

Paper only. This module never talks to Dhan and never places an order of any
kind. It keeps simulated positions in a small JSON file and closes them when a
supplied last price crosses the stop-loss or target. A live adapter would be a
separate, fail-closed module and does not exist.
"""
import json, math, os, threading, time, uuid

MAX_OPEN = 10
MAX_QTY = 100000
LIVE_ORDERS_ENABLED = False  # constant; nothing in this module reads a switch


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

    def _close(self, pos, price, reason):
        pos["status"] = "CLOSED"
        pos["exit"] = float(price)
        pos["reason"] = reason
        pos["closed_at"] = self.clock()
        sign = 1 if pos["side"] == "BUY" else -1
        pos["pnl"] = round(sign * (pos["exit"] - pos["entry"]) * pos["qty"], 2)

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
                if (px <= p["stop"]) if buy else (px >= p["stop"]):
                    self._close(p, p["stop"], "STOP_LOSS")
                elif p["target"] is not None and ((px >= p["target"]) if buy else (px <= p["target"])):
                    self._close(p, p["target"], "TARGET")
                else:
                    continue
                closed.append(dict(p))
            self.last_eval_at = self.clock()
            if closed:
                self._save()
        return closed

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

    def state(self):
        with self.lock:
            return {"heartbeat": self.heartbeat(),
                    "positions": [dict(p) for p in self.positions[-100:]]}
