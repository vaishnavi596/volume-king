"""App-owned normalized candle cache; not a Dhan/Oracle network adapter."""
from math import isfinite

TIMEFRAMES = ("1m", "3m", "5m")
INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
BAR_FIELDS = {"timestamp", "open", "high", "low", "close", "volume", "completed"}

class CandleEvidenceError(ValueError):
    pass

def validate_completed_bars(bars):
    """Require trustworthy normalized completed OHLCV bars, never synthesize candles."""
    if type(bars) is not list or len(bars) < 2 or len(bars) > 2000:
        raise CandleEvidenceError("Missing or excessive completed history")
    accepted = []
    previous = 0
    for bar in bars:
        if type(bar) is not dict or set(bar) != BAR_FIELDS or bar["completed"] is not True:
            raise CandleEvidenceError("Malformed or unfinished candle")
        t = bar["timestamp"]
        if type(t) is not int or t <= previous:
            raise CandleEvidenceError("Candle timestamps are not strictly increasing")
        prices = [bar[key] for key in ("open", "high", "low", "close")]
        volume = bar["volume"]
        if (any(type(v) not in (int, float) or not isfinite(v) or v <= 0 for v in prices)
                or type(volume) not in (int, float) or not isfinite(volume) or volume < 0
                or bar["high"] < max(bar["open"], bar["close"], bar["low"])
                or bar["low"] > min(bar["open"], bar["close"], bar["high"])):
            raise CandleEvidenceError("Candle OHLCV is not valid")
        accepted.append(dict(bar))
        previous = t
    return accepted

class LocalCandleHistory:
    """Per symbol/timeframe revision isolation; last good on invalid feed."""
    def __init__(self):
        self._entries = {}

    def accept(self, symbol, timeframe, revision, bars, *, allowed_symbols, source="dhan"):
        allowed = tuple(allowed_symbols)
        if (type(symbol) is not str or symbol not in allowed
                or type(timeframe) is not str or timeframe not in TIMEFRAMES
                or type(revision) is not int or revision < 0
                or source != "dhan"):
            raise CandleEvidenceError("Untrusted candle source or context")
        validated = validate_completed_bars(bars)
        key = (symbol, timeframe)
        previous = self._entries.get(key)
        if previous and (revision <= previous["revision"]
                         or validated[-1]["timestamp"] < previous["bars"][-1]["timestamp"]):
            # A higher transport revision is not evidence of a newer candle.
            # Protect last-good history from a replay/short historical window.
            return False
        self._entries[key] = {"revision": revision, "bars": validated}
        return True

    def view(self, symbol, timeframe, *, selected_equities=()):
        if (symbol not in INDEXES and symbol not in selected_equities) or timeframe not in TIMEFRAMES:
            return {"status": "WAIT", "bars": (), "count": 0}
        entry = self._entries.get((symbol, timeframe))
        if entry is None:
            return {"status": "WAIT", "bars": (), "count": 0}
        return {"status": "HIST", "bars": tuple(dict(b) for b in entry["bars"]),
                "count": len(entry["bars"])}

    def summary(self, symbol, timeframe, *, selected_equities=()):
        v = self.view(symbol, timeframe, selected_equities=selected_equities)
        return (f"{symbol} {timeframe}: {v['count']} completed historical bars (unverified)"
                if v["status"] == "HIST" else f"{symbol} {timeframe}: candles WAIT")

    def forget_removed(self, selected_equities):
        allowed = set(INDEXES).union(selected_equities)
        self._entries = {key: value for key, value in self._entries.items()
                         if key[0] in allowed}
