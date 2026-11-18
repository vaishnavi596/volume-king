"""BOT KING V2 Dashboard display-only V1-parity view model.

This module never fetches Dhan, infers signals, or upgrades HIST to LIVE.
"""
from shared_filter_context import shared_filter_context

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")


def index_card_model(symbol, quote_inbox, evidence_inbox, selected_equities=()):
    if symbol not in INDEXES:
        raise ValueError("Index card requires one supported index")
    quote = quote_inbox.visible(symbol, selected_equities)
    candles = evidence_inbox.candles.view(
        symbol, "1m", selected_equities=selected_equities)
    factors = shared_filter_context(
        evidence_inbox.filters, symbol, "1m", selected_equities=selected_equities)
    status = quote["status"]
    if status not in ("WAIT", "HIST"):
        raise ValueError("Unverified quote status cannot be LIVE")
    return {
        "symbol": symbol, "timeframe": "1m", "status": status,
        "price_label": (f'{quote["price"]:,.2f} HIST (unverified)'
                        if status == "HIST" else "WAIT"),
        "candle_label": (f'{candles["count"]} completed 1m candles HIST'
                         if candles["status"] == "HIST" else "1m candles WAIT"),
        "filters": factors["rows"], "sixth": factors["sixth"],
        "factor_coverage": factors["coverage_label"],
    }


def status_overview(selected_equities, quote_inbox, evidence_inbox):
    """App-only compact truthfulness summary; never a provider health assertion."""
    selected = tuple(selected_equities)
    cards = tuple(index_card_model(s, quote_inbox, evidence_inbox, selected)
                  for s in INDEXES)
    return {
        "index_quote_coverage": sum(card["status"] == "HIST" for card in cards),
        "index_count": 3,
        "equity_count": len(selected),
        "feed": "OFFLINE / unverified; authenticated live integration pending",
        "master": "Master access not connected; enable/disable pending",
        "orders": "LIVE ORDERS OFF",
    }
