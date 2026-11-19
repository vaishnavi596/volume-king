"""App-side Dhan equity catalog selection. No provider calls or fixed 54-symbol list.

An authenticated catalog source supplies NSE_EQ symbols; only the user's
0..70 selected symbols are included in market-data demand.
"""
from app_state import LocalWatchlists, SelectionError, valid_symbol

MAX_CATALOG_ROWS = 100000
MAX_SEARCH_RESULTS = 50


class EquityCatalog:
    def __init__(self, rows):
        if type(rows) not in (list, tuple) or len(rows) > MAX_CATALOG_ROWS:
            raise ValueError("Untrusted equity catalog")
        mapping = {}
        for row in rows:
            if type(row) is not dict or set(row) != {"symbol", "segment", "security_id", "name"}:
                raise ValueError("Invalid instrument row")
            symbol = row["symbol"]
            if (not valid_symbol(symbol) or row["segment"] != "NSE_EQ"
                    or type(row["security_id"]) not in (int, str)
                    or not str(row["security_id"]).isdigit()
                    or int(row["security_id"]) <= 0
                    or type(row["name"]) is not str or not 1 <= len(row["name"]) <= 120):
                raise ValueError("Invalid verified equity")
            if symbol in mapping:
                raise ValueError("Ambiguous duplicate equity")
            mapping[symbol] = dict(row)
        self._rows = mapping

    def search(self, query, limit=MAX_SEARCH_RESULTS):
        if (type(query) is not str or len(query) > 64 or
                type(limit) is not int or not 1 <= limit <= MAX_SEARCH_RESULTS):
            raise ValueError("Invalid catalog query")
        q = query.strip().upper()
        matching = (v for v in self._rows.values()
                    if q in v["symbol"] or q in v["name"].upper())
        return tuple(sorted(matching, key=lambda v: (not v["symbol"].startswith(q), v["symbol"]))[:limit])

    def add(self, watchlists, index, symbol):
        if not isinstance(watchlists, LocalWatchlists) or symbol not in self._rows:
            raise SelectionError("Share not in verified Dhan equity catalog")
        watchlists.add(index, symbol)

    def selected_demand(self, watchlists):
        if not isinstance(watchlists, LocalWatchlists):
            raise SelectionError("Validated Watchlists required")
        selected = watchlists.selected
        if any(s not in self._rows for s in selected):
            raise SelectionError("Selection no longer verified in catalog")
        return selected
