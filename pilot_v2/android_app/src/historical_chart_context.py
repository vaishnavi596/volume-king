"""V2 local historical chart and context shortlist. No live/signal claim.

The original V1 live rank_candidates has strict verified-live gates and MUST
NOT be weakened or fed historical cache as if it were current market data.
"""
from legacy_technical_bridge import historical_scanner_analysis


def chart_points(candles, symbol, timeframe, *, selected_equities=(), limit=35):
    if type(limit) is not int or not 2 <= limit <= 200:
        raise ValueError("Invalid local chart window")
    view = candles.view(symbol, timeframe, selected_equities=selected_equities)
    if view["status"] != "HIST":
        return ()
    return tuple(float(bar["close"]) for bar in view["bars"][-limit:])


def historical_shortlist(candles, selected_equities, *, timeframe="3m", limit=5):
    if type(limit) is not int or not 1 <= limit <= 5:
        raise ValueError("Historical shortlist is limited to five")
    selected = tuple(selected_equities)
    if (len(selected) != len(set(selected)) or len(selected) > 70
            or any(type(sym) is not str or not sym for sym in selected)):
        raise ValueError("Invalid selected equity roster")
    items = []
    for symbol in selected:
        context = historical_scanner_analysis(
            candles, symbol, timeframe, selected_equities=selected)
        scan = context["scan"]
        if context["status"] != "HIST" or scan is None:
            continue
        direction = scan.get("bias")
        if direction not in ("BULLISH", "BEARISH"):
            continue
        score = scan.get("score")
        if type(score) is not int or not 0 <= score <= 100:
            continue
        items.append({"symbol": symbol, "direction": direction,
                      "score": score,
                      "label": f"{symbol} · {direction} HIST · {score}% historical "
                               "indicator agreement (NOT verified Super Five)"})
    items.sort(key=lambda row: (-row["score"], row["symbol"]))
    return tuple(items[:limit])
