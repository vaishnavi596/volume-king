"""App-owned V2 selected-equity Watchlist 3m compact display contract.

No network, live data, synthetic scoring or server-side preferences.
"""
from app_state import INDEXES, MAX_EQUITIES


def watchlist_row(symbol, quotes, evidence, *, selected_equities):
    selected = tuple(selected_equities)
    if (type(symbol) is not str or symbol not in selected or symbol in INDEXES
            or len(selected) > MAX_EQUITIES or len(set(selected)) != len(selected)):
        raise ValueError("Watchlist row must be a unique selected equity")
    quote = quotes.visible(symbol, selected)
    candle = evidence.candles.view(symbol, "3m", selected_equities=selected)
    filters = evidence.filters.rows(symbol, "3m", selected_equities=selected)
    return {
        "symbol": symbol,
        "price": (f'{quote["price"]:,.2f} HIST' if quote["status"] == "HIST" else "WAIT"),
        "candle": (f'{candle["count"]} completed 3m candles HIST'
                   if candle["status"] == "HIST" else "3m candles WAIT"),
        "filter_text": " · ".join(
            f"{name} {value}" for name, value in filters[:5] if value != "WAIT"
        ) or "5 filters WAIT · no verified evidence",
        "sixth": filters[5],
        "historical_only": True,
    }


def watchlist_rows(group, quotes, evidence, *, selected_equities):
    if type(group) is not list or len(group) != len(set(group)):
        raise ValueError("Duplicate or invalid Watchlist group")
    return tuple(watchlist_row(s, quotes, evidence,
                               selected_equities=selected_equities) for s in group)
