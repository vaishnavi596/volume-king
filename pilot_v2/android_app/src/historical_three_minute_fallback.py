"""Scanner-only 3m historical view over authenticated cached 1m candles.

Read-only; never mutates transport cache, labels history as verified live or
synthesizes missing minute bars.
"""
from time import time
from historical_migration import three_minute_from_local_history

class HistoricalThreeMinuteFallback:
    def __init__(self, primary, *, clock=time):
        self.primary = primary
        self.clock = clock

    def view(self, symbol, timeframe, *, selected_equities=()):
        direct = self.primary.view(symbol, timeframe, selected_equities=selected_equities)
        if timeframe != "3m" or direct["status"] == "HIST":
            return direct
        derived = three_minute_from_local_history(
            self.primary, symbol, selected_equities=selected_equities,
            now_epoch=self.clock())
        if derived["status"] != "HIST" or len(derived["bars"]) < 2:
            return direct
        bars = tuple({
            "timestamp": int(t), "open": o, "high": h, "low": l,
            "close": c, "volume": v, "completed": True
        } for t, o, h, l, c, v in derived["bars"])
        return {"status": "HIST", "bars": bars, "count": len(bars),
                "derived_from": "cached_1m", "verified_live": False}

    def summary(self, symbol, timeframe, *, selected_equities=()):
        view = self.view(symbol, timeframe, selected_equities=selected_equities)
        if view["status"] != "HIST":
            return f"{symbol} {timeframe}: candles WAIT"
        suffix = " · derived from cached 1m" if view.get("derived_from") else ""
        return (f"{symbol} {timeframe}: {view['count']} completed historical bars "
                f"(unverified){suffix}")
