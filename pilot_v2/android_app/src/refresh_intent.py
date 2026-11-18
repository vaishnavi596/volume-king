"""FT-3 Flet-only refresh intent. Zero HTTP requests, timers or server settings."""
from dataclasses import dataclass
from datetime import datetime
from smart_data import (SmartDataSettings, SmartDataError,
                        permitted_auto_refresh, selected_equity_plan)

@dataclass(frozen=True)
class RefreshIntent:
    permitted: bool
    reason: str
    equities: tuple
    indexes: tuple
    equity_seconds: int
    index_signal_timeframe: str = "1m"
    watchlist_candle_timeframe: str = "3m"

def make_refresh_intent(watchlists, settings, now, *,
                        confirmed_session=False, manual=False):
    """One app-owner decision for a shared upstream pipe, not a poll scheduler."""
    if type(manual) is not bool or type(confirmed_session) is not bool:
        raise SmartDataError("Explicit refresh origin and session evidence required")
    if not isinstance(settings, SmartDataSettings) or not isinstance(now, datetime):
        raise SmartDataError("App settings and aware timestamp required")
    selection = selected_equity_plan(watchlists)
    if not (0 <= selection["equity_count"] <= 70):
        raise SmartDataError("Invalid selected equity demand")
    if manual:
        # Manual after close is allowed. Transport permission/429 still independent.
        permitted, reason = True, "MANUAL_DATA_REQUEST_ONLY"
    else:
        permitted = permitted_auto_refresh(
            now, market_session_confirmed=confirmed_session, settings=settings)
        reason = "AUTO_MARKET_CONFIRMED" if permitted else "AUTO_OFF_OR_UNCONFIRMED"
    return RefreshIntent(
        permitted, reason,
        tuple(selection["equities"]) if permitted else (),
        tuple(selection["indices"]) if permitted else (),
        settings.equity_seconds)
