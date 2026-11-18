"""Flet V2 offline Scanner selection. App owns choices; no broker polling."""
from dataclasses import dataclass

INDEXES = ("NIFTY", "BANKNIFTY", "SENSEX")
TIMEFRAMES = ("1m", "3m", "5m")

class ScannerError(ValueError):
    pass

@dataclass(frozen=True)
class ScannerSelection:
    symbol: str = "NIFTY"
    timeframe: str = "1m"

    def __post_init__(self):
        if (type(self.symbol) is not str or type(self.timeframe) is not str
                or self.timeframe not in TIMEFRAMES):
            raise ScannerError("Invalid Scanner selection")

    def saved_state(self):
        return {"schema_version": 1, "symbol": self.symbol, "timeframe": self.timeframe}

    @classmethod
    def from_saved(cls, saved, watchlists):
        if (type(saved) is not dict
                or set(saved) != {"schema_version", "symbol", "timeframe"}
                or type(saved["schema_version"]) is not int
                or saved["schema_version"] != 1):
            raise ScannerError("Invalid local Scanner save")
        selection = cls(saved["symbol"], saved["timeframe"])
        if selection.symbol not in selectable_symbols(watchlists):
            raise ScannerError("Scanner symbol is no longer selected")
        return selection

def selectable_symbols(watchlists):
    """Indexes independent of dynamically selected 0–70 equities."""
    return INDEXES + tuple(watchlists.selected)

def choose(current, watchlists, *, symbol=None, timeframe=None):
    candidate = ScannerSelection(
        current.symbol if symbol is None else symbol,
        current.timeframe if timeframe is None else timeframe)
    if candidate.symbol not in selectable_symbols(watchlists):
        raise ScannerError("Select a valid saved equity or dashboard index")
    return candidate

def for_visible_roster(current, watchlists):
    """Removed shares cannot be scanned from stale UI state."""
    if current.symbol not in selectable_symbols(watchlists):
        return ScannerSelection()
    return current
