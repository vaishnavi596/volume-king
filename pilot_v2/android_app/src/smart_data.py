"""Flet V2 app-owned Smart Data policy; computes intent, never polls Dhan."""
from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone

IST = timezone(timedelta(hours=5, minutes=30), name="IST")
MARKET_START = time(9, 10)
MARKET_END = time(15, 45)
INTERVALS = (180, 300, 600)

class SmartDataError(ValueError):
    pass

@dataclass(frozen=True)
class SmartDataSettings:
    """Only mobile display/refresh choices. Not broker or Oracle configuration."""
    auto_refresh: bool = True
    equity_seconds: int = 180

    def __post_init__(self):
        if type(self.auto_refresh) is not bool or type(self.equity_seconds) is not int or self.equity_seconds not in INTERVALS:
            raise SmartDataError("Invalid app refresh settings")

    def saved_state(self):
        return {"schema_version": 1, "auto_refresh": self.auto_refresh,
                "equity_seconds": self.equity_seconds}

    @classmethod
    def from_saved(cls, data):
        if (type(data) is not dict or set(data) !=
                {"schema_version", "auto_refresh", "equity_seconds"}
                or type(data["schema_version"]) is not int or data["schema_version"] != 1):
            raise SmartDataError("Invalid local Smart Data settings")
        return cls(data["auto_refresh"], data["equity_seconds"])

def permitted_auto_refresh(now, *, market_session_confirmed, settings):
    """No holiday/market-status guesses; must have explicit session evidence."""
    if not isinstance(now, datetime) or now.tzinfo is None:
        raise SmartDataError("Timezone-aware clock required")
    if type(market_session_confirmed) is not bool or not isinstance(settings, SmartDataSettings):
        raise SmartDataError("Verified market session and app settings required")
    local = now.astimezone(IST)
    return bool(settings.auto_refresh and market_session_confirmed and
                local.weekday() < 5 and MARKET_START <= local.time().replace(tzinfo=None) <= MARKET_END)

def selected_equity_plan(watchlists):
    """Uses existing app owned saved selections, never requests all 70 by default."""
    selected = watchlists.selected
    return {"equities": selected, "indices": ("NIFTY", "BANKNIFTY", "SENSEX"),
            "equity_count": len(selected)}
