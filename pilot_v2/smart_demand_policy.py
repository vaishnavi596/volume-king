"""One V2 pipeline, differentiated priority for data demands.

Pure APP-owned demand plan: no network, Dhan orders, credentials, timers or
separate pipelines. Target intervals are NOT permission to exceed Dhan quotas.
Actual provider cadence must be bounded by the gateway's shared rate budget.
"""
from __future__ import annotations
from dataclasses import dataclass

# Smaller integer = higher scheduling priority. All lanes share ONE budget.
PRIORITY = {"interactive": 0, "foreground": 1, "standard": 2, "background": 3}
FEATURES = {
    "manual_decision": ("interactive", "quotes", 30),
    "selected_scanner": ("interactive", "candles", 30),
    "index_dashboard": ("foreground", "indices", 60),
    "super_five_visible": ("foreground", "candles", 60),
    "watchlist_visible": ("standard", "quotes", 180),
    "watchlist_candles": ("standard", "candles", 180),
    "option_chain_visible": ("standard", "options", 60),
    "assessment_filters": ("standard", "assessment", 180),
    "historical_backfill": ("background", "candles", 600),
    "news_background": ("background", "news", 600),
}
# Last tuple entry is a *desired* freshness interval in seconds, not a fixed
# provider polling frequency. Provider budget, cache and market hours win.
ALLOWED_FEEDS = frozenset(("quotes", "indices", "candles", "options",
                           "assessment", "news"))


@dataclass(frozen=True)
class Demand:
    feed: str
    symbols: tuple
    priority: int
    freshness_seconds: int
    consumers: tuple


def plan_demands(requests):
    """Coalesce common symbol/feed demands; do not multiply broker requests.

    Each request is (feature_name, tuple_of_symbols). An interactive request
    can prioritize a shared row but never bypass authorization or provider
    cooldown. Unknown sources must remain blocked by actual source adapters.
    """
    if type(requests) not in (tuple, list):
        raise ValueError("Invalid V2 demand plan")
    grouped = {}
    for request in requests:
        if type(request) not in (tuple, list) or len(request) != 2:
            raise ValueError("Invalid demand")
        feature, symbols = request
        if type(feature) is not str or feature not in FEATURES:
            raise ValueError("Unknown demand feature")
        if type(symbols) not in (tuple, list) or len(symbols) > 70:
            raise ValueError("Invalid symbol roster")
        from .gateway_contract import symbol_ok
        if any(not symbol_ok(symbol) for symbol in symbols):
            raise ValueError("Invalid selected symbol")
        tier, feed, freshness = FEATURES[feature]
        if feed not in ALLOWED_FEEDS:
            raise ValueError("Unsupported data lane")
        for symbol in set(symbols):
            key = (feed, symbol)
            if key not in grouped:
                grouped[key] = [PRIORITY[tier], freshness, set()]
            g = grouped[key]
            g[0] = min(g[0], PRIORITY[tier])
            g[1] = min(g[1], freshness)
            g[2].add(feature)
    return tuple(
        Demand(feed, (symbol,), data[0], data[1], tuple(sorted(data[2])))
        for (feed, symbol), data in sorted(
            grouped.items(), key=lambda item: (item[1][0], item[0][0], item[0][1]))
    )
