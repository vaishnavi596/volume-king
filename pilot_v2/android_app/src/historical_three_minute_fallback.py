"""Shared 1/3/5/15/30m historical-only candle view for V2 screens.

Legacy class name retained so Scanner and Super Five tests stay compatible.
Direct validated cache wins. Otherwise derive only full session-aligned
candles from the same locally accepted one-minute source, without network.
"""
from time import time
from historical_migration import three_minute_from_local_history
from completed_timeframe_resampler import complete_session_bars


class HistoricalThreeMinuteFallback:
    def __init__(self, primary, *, clock=time):
        self.primary = primary
        self.clock = clock

    def view(self, symbol, timeframe, *, selected_equities=()):
        direct = self.primary.view(
            symbol, timeframe, selected_equities=selected_equities)
        if direct["status"] == "HIST" or timeframe == "1m":
            return direct
        if timeframe not in ("3m", "5m", "15m", "30m"):
            return direct
        minute = self.primary.view(
            symbol, "1m", selected_equities=selected_equities)
        if minute["status"] != "HIST":
            return direct
        if timeframe == "3m":
            derived = three_minute_from_local_history(
                self.primary, symbol, selected_equities=selected_equities,
                now_epoch=self.clock())
            bars = tuple({
                "timestamp": int(t), "open": o, "high": h,
                "low": l, "close": c, "volume": v, "completed": True
            } for t, o, h, l, c, v in derived["bars"])
        else:
            bars = complete_session_bars(
                minute["bars"], timeframe, now_epoch=self.clock())
        if len(bars) < 2:
            return direct
        return {"status": "HIST", "bars": bars, "count": len(bars),
                "derived_from": "cached_1m", "verified_live": False}

    def summary(self, symbol, timeframe, *, selected_equities=()):
        view = self.view(symbol, timeframe, selected_equities=selected_equities)
        if view["status"] != "HIST":
            return f"{symbol} {timeframe}: candles WAIT"
        suffix = " · derived from cached 1m" if view.get("derived_from") else ""
        return (f"{symbol} {timeframe}: {view['count']} completed historical bars "
                f"(unverified){suffix}")
