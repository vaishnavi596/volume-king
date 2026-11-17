"""Read-only BOT KING Smart Engine data-discovery planner.

No network, disk writes, browser automation, or Dhan API calls. It determines
which provenance-labeled source *could* answer a research question. The app /
Oracle coordinator must separately authorize, throttle and execute any fetch.
"""
from datetime import date, timedelta
from dataclasses import dataclass

WINDOWS = {"1m": 31, "1y": 366, "2y": 731}
PRICE_SOURCES = ("cached_dhan_history", "dhan_historical")
CONTEXT_SOURCES = ("saved_research", "online_primary_sources")


@dataclass(frozen=True)
class ResearchRequest:
    symbol: str
    as_of: str
    window: str
    category: str = "price_history"
    enable_dhan: bool = False
    enable_online: bool = False

    def __post_init__(self):
        if not isinstance(self.symbol, str) or not self.symbol or not self.symbol.isascii():
            raise ValueError("Invalid symbol")
        if not isinstance(self.as_of, str) or date.fromisoformat(self.as_of).isoformat() != self.as_of:
            raise ValueError("Invalid as_of")
        if self.window not in WINDOWS:
            raise ValueError("Unsupported research window")
        if self.category not in ("price_history", "news_context"):
            raise ValueError("Unsupported research category")
        if type(self.enable_dhan) is not bool or type(self.enable_online) is not bool:
            raise ValueError("Explicit data-permission flags required")


def plan_research(request, *, cached_days=(), broker_history_available=False,
                  online_provider_available=False, max_request_chunks=2):
    """Report source choices without executing any external request.

    A real market-data eligibility/provider-limit check and persistent cache
    index are required before execution. Chunk size is a conservative *planner*
    setting, not an assertion of the Dhan API's permitted date-span.
    """
    if not isinstance(request, ResearchRequest):
        raise ValueError("ResearchRequest required")
    if type(broker_history_available) is not bool or type(online_provider_available) is not bool:
        raise ValueError("Invalid capability")
    if type(max_request_chunks) is not int or not 0 <= max_request_chunks <= 4:
        raise ValueError("Invalid provider budget")
    ending = date.fromisoformat(request.as_of) - timedelta(days=1)
    starting = ending - timedelta(days=WINDOWS[request.window] - 1)
    normalized = set()
    for item in cached_days:
        if not isinstance(item, str):
            raise ValueError("Invalid cache manifest")
        parsed = date.fromisoformat(item)
        if parsed.isoformat() != item:
            raise ValueError("Invalid cache date")
        normalized.add(parsed)
    relevant = sorted(x for x in normalized if starting <= x <= ending)
    base = {
        "symbol": request.symbol, "category": request.category,
        "window": request.window, "start_date": starting.isoformat(),
        "end_date": ending.isoformat(),
        "source_verified": False, "live_data_verified": False,
        "signal_eligible": False, "bullish_score": None, "bearish_score": None,
        "broker_requests_executed": 0, "browser_requests_executed": 0,
        "no_live_orders": True, "cache_days_known": len(relevant),
    }
    if request.category == "news_context":
        if request.enable_online and online_provider_available:
            return dict(base, next_source="online_primary_sources",
                        state="REQUIRES_OPERATOR_OR_COORDINATOR_EXECUTION",
                        advisory="Source citations, timestamps and issuer linkage required before explaining causes")
        return dict(base, next_source="saved_research", state="ONLINE_RESEARCH_NOT_CONFIGURED",
                    advisory="No verified causal attribution from candle data")
    if relevant:
        # Cached data may answer some/all of the request but not automatically prove
        # complete trading-session coverage (weekends, holidays, gaps).
        cache_state = "CACHE_PRESENT_COVERAGE_UNVERIFIED"
    else:
        cache_state = "CACHE_EMPTY"
    if request.enable_dhan and broker_history_available and max_request_chunks:
        return dict(base, next_source="dhan_historical",
                    state="BROKER_FETCH_PLAN_REQUIRES_RATE_LIMIT_AND_ENTITLEMENT",
                    cache_state=cache_state,
                    max_request_chunks=max_request_chunks,
                    advisory="Request only missing approved ranges; actual spans must match Dhan contract and global 429 budget")
    return dict(base, next_source="cached_dhan_history", state=cache_state,
                advisory="Do not infer absent market sessions or re-label historical data as live")
