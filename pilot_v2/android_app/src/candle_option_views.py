"""V2 native completed-candle geometry and strict Dhan CE/PE strike cache.

Display-only: never calls Dhan, fabricates strikes, or computes trading signals.
A trusted session is enforced by future authenticated transport, not a flag.
"""
from math import isfinite
from option_evidence import INDEXES, OptionEvidenceError, valid_expiry


def candle_geometry(cache, symbol, timeframe, *, selected_equities=(),
                    limit=22, height=116):
    """Finite OHLC wick/body pixels for Flet-native historical candle render."""
    if type(limit) is not int or not 2 <= limit <= 100:
        raise ValueError("Invalid candle display count")
    view = cache.view(symbol, timeframe, selected_equities=selected_equities)
    if view["status"] != "HIST":
        return ()
    series = view["bars"][-limit:]
    lo = min(b["low"] for b in series)
    hi = max(b["high"] for b in series)
    span = max(hi - lo, .000001)
    def y(price):
        return round(4 + (hi - price) * (height - 8) / span, 2)
    return tuple({
        "timestamp": b["timestamp"], "up": b["close"] >= b["open"],
        "wick_top": y(b["high"]),
        "wick_height": max(1., y(b["low"]) - y(b["high"])),
        "body_top": min(y(b["open"]), y(b["close"])),
        "body_height": max(1., abs(y(b["open"]) - y(b["close"]))),
    } for b in series)


_STRIKE = frozenset(("strike", "ce_price", "ce_oi", "ce_volume",
                      "pe_price", "pe_oi", "pe_volume"))
_FIELDS = frozenset(("symbol", "expiry", "revision", "observed_at",
                      "source", "rows"))


class LocalOptionStrikes:
    """Per-symbol/expiry strict ATM±3 chain, independent of aggregate metrics."""
    def __init__(self):
        self._cache = {}

    def accept(self, payload, expiry_choices, *, selected_equities=(),
               trusted_transport=False):
        if trusted_transport is not True or type(payload) is not dict or set(payload) != _FIELDS:
            raise OptionEvidenceError("Authenticated complete Dhan chain required")
        symbol = payload["symbol"]
        expiry = payload["expiry"]
        allowed = INDEXES + tuple(selected_equities)
        if (type(symbol) is not str or symbol not in allowed
                or not valid_expiry(expiry)
                or expiry_choices.selected(symbol, selected_equities=selected_equities) != expiry
                or type(payload["revision"]) is not int or payload["revision"] < 0
                or type(payload["observed_at"]) is not int or payload["observed_at"] <= 0
                or payload["source"] != "dhan" or type(payload["rows"]) is not list
                or len(payload["rows"]) != 7):
            raise OptionEvidenceError("Invalid symbol, expiry or exact strike window")
        last = 0
        clean = []
        for row in payload["rows"]:
            if type(row) is not dict or set(row) != _STRIKE:
                raise OptionEvidenceError("Malformed CE/PE strike row")
            strike = row["strike"]
            if (type(strike) not in (int, float) or not isfinite(strike)
                    or strike <= last):
                raise OptionEvidenceError("Strikes must be positive and ascending")
            last = strike
            if any(type(row[k]) not in (int, float) or not isfinite(row[k])
                   or row[k] < 0 for k in _STRIKE - {"strike"}):
                raise OptionEvidenceError("Invalid CE/PE quote or OI")
            clean.append(dict(row))
        key = (symbol, expiry)
        old = self._cache.get(key)
        if old and (payload["revision"] <= old["revision"]
                    or payload["observed_at"] < old["observed_at"]):
            return False
        self._cache[key] = {
            "revision": payload["revision"],
            "observed_at": payload["observed_at"], "rows": tuple(clean),
        }
        return True

    def visible(self, symbol, expiry, expiry_choices, *, selected_equities=()):
        if expiry_choices.selected(symbol, selected_equities=selected_equities) != expiry:
            return {"status": "WAIT", "rows": ()}
        item = self._cache.get((symbol, expiry))
        if item is None:
            return {"status": "WAIT", "rows": ()}
        return {"status": "HIST", "rows": tuple(dict(r) for r in item["rows"])}

    def forget_removed(self, selected_equities):
        allowed = set(INDEXES).union(selected_equities)
        self._cache = {k: v for k, v in self._cache.items() if k[0] in allowed}
