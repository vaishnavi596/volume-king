"""Local Watchlist symbol search; no quote fetch or roster mutation.

Filters only currently visible selected group, preserving its original order.
"""
from app_state import valid_symbol


def filtered_watchlist_symbols(group, query):
    if type(group) is not list or any(not valid_symbol(s) for s in group):
        raise ValueError("Watchlist search requires validated equities")
    if len(group) != len(set(group)):
        raise ValueError("Duplicate Watchlist symbol")
    if type(query) is not str or len(query) > 64:
        raise ValueError("Invalid Watchlist search text")
    needle = query.strip().upper()
    if not needle:
        return list(group)
    return [symbol for symbol in group if needle in symbol]
