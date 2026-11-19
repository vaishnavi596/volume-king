"""BOT KING V2 device-side read-only quote acceptance; NO network or login."""
from math import isfinite

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")

class FeedError(ValueError):
    pass

def validate_readonly_snapshot(payload, allowed_symbols):
    """Validate entire frozen V2 schema before mutating any last-good state."""
    required = {"protocol", "schema_version", "source", "freshness",
                "live_orders_enabled", "revision", "quotes"}
    if (type(payload) is not dict or set(payload) != required
            or payload["protocol"] != "botking-v2-readonly"
            or type(payload["schema_version"]) is not int or payload["schema_version"] != 1
            or payload["source"] != "dhan" or payload["freshness"] != "unverified"
            or payload["live_orders_enabled"] is not False
            or type(payload["revision"]) is not int or payload["revision"] < 0
            or type(payload["quotes"]) is not dict):
        raise FeedError("Invalid read-only Dhan contract")
    if type(allowed_symbols) not in (tuple, list, frozenset, set):
        raise FeedError("Invalid requested roster")
    allowed = set(allowed_symbols)
    if len(allowed) != len(allowed_symbols) or not all(type(s) is str for s in allowed):
        raise FeedError("Invalid or duplicate requested symbol")
    accepted = {}
    for symbol, row in payload["quotes"].items():
        if (type(symbol) is not str or symbol not in allowed
                or type(row) is not dict
                or set(row) != {"price", "freshness", "live_verified", "revision"}
                or type(row["price"]) not in (int, float)
                or not isfinite(row["price"]) or row["price"] <= 0
                or row["freshness"] != "unverified"
                or row["live_verified"] is not False
                or type(row["revision"]) is not int
                or row["revision"] < 0 or row["revision"] > payload["revision"]):
            raise FeedError("Rejected unselected or untrusted quote")
        accepted[symbol] = dict(row)
    return payload["revision"], accepted

class DeviceQuoteView:
    """Keep last-good per selected symbol; never turn unverified into LIVE."""
    def __init__(self):
        self.revision = -1
        self._rows = {}

    def apply(self, payload, selected_equities):
        roster = tuple(selected_equities)
        allowed = INDEXES + roster
        revision, accepted = validate_readonly_snapshot(payload, allowed)
        if revision <= self.revision:
            return False
        # Apply all-or-nothing; absent symbols retain their last-good quote.
        self._rows = {symbol: dict(row) for symbol, row in self._rows.items()
                      if symbol in allowed}
        # A newer feed envelope may include a stale per-symbol row. Never
        # replace a last-good quote with an older symbol revision.
        for symbol, row in accepted.items():
            previous = self._rows.get(symbol)
            if previous is None or row["revision"] >= previous["revision"]:
                self._rows[symbol] = row
        self.revision = revision
        return True

    def visible(self, symbol, selected_equities):
        if symbol not in INDEXES and symbol not in selected_equities:
            return {"status": "WAIT", "price": None, "revision": None}
        row = self._rows.get(symbol)
        if row is None:
            return {"status": "WAIT", "price": None, "revision": None}
        # No trusted exchange timestamp in v1 contract: safe label is historical.
        return {"status": "HIST", "price": row["price"], "revision": row["revision"]}

    def forget_removed(self, selected_equities):
        allowed = set(INDEXES).union(selected_equities)
        self._rows = {key: val for key, val in self._rows.items() if key in allowed}

    def display(self, symbol, selected_equities):
        view = self.visible(symbol, selected_equities)
        if view["price"] is None:
            return f"{symbol} — WAIT"
        return f"{symbol} — {view['price']:,.2f} HIST (unverified)"
