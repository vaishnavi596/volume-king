"""V2 app-owned joint data-readiness view over one shared validated cache.

One roster; independent index lane; source-gated candles, filters, options and
Super Five readiness. This is a local immutable presentation snapshot, not
a scheduler, HTTP client, broker session, market signal or live attestation.
"""
from app_state import INDEXES, MAX_EQUITIES
from scanner_state import TIMEFRAMES
from smart_data import selected_equity_plan
from shared_filter_context import shared_filter_context


def joint_data_readiness(watchlists, scanner, smart, quotes, evidence,
                         historical):
    """Truthful readiness of the selected symbol without network I/O."""
    plan = selected_equity_plan(watchlists)
    selected = tuple(plan["equities"])
    if (len(selected) > MAX_EQUITIES or len(set(selected)) != len(selected)
            or any(sym in INDEXES for sym in selected)):
        raise ValueError("Invalid app-owned unique equity workload")
    symbol, timeframe = scanner.symbol, scanner.timeframe
    if timeframe not in TIMEFRAMES or symbol not in INDEXES + selected:
        raise ValueError("Scanner selection is not in selected data demand")
    visible = quotes.visible(symbol, selected)
    history = historical.view(symbol, timeframe, selected_equities=selected)
    filters = shared_filter_context(evidence.filters, symbol, timeframe,
                                    selected_equities=selected)
    expiry = evidence.expiries.selected(symbol, selected_equities=selected)
    option = (evidence.options.visible(symbol, expiry, selected_equities=selected)
              if expiry else {"status": "WAIT"})
    strikes = (evidence.strikes.visible(
        symbol, expiry, evidence.expiries, selected_equities=selected)
        if expiry else {"status": "WAIT"})
    # This readiness model cannot certify provider auth, source freshness or
    # verified Super Five voting, even when historical evidence is complete.
    requested = len(selected)
    return {
        "symbol": symbol, "timeframe": timeframe,
        "equity_count": requested, "equities": selected,
        "index_count": len(INDEXES), "indexes": INDEXES,
        "requested_quote_symbols": requested + len(INDEXES),
        "selected_only": True,
        "equity_refresh_seconds": smart.equity_seconds,
        "auto_refresh_enabled": smart.auto_refresh,
        "quote_status": visible["status"], "candle_status": history["status"],
        "candle_count": history["count"],
        "filter_coverage": filters["coverage"],
        "filter_count": 5, "sixth_filter": filters["sixth"],
        "filter_label": filters["coverage_label"],
        "expiry_status": "HIST" if expiry else "WAIT",
        "option_status": option["status"],
        "strikes_status": strikes["status"],
        "super_five_status": "WAIT",
        "live_verified": False, "network_requests": 0,
        "gateway_connected": False,
    }


def data_readiness_label(state):
    if state["live_verified"] is not False or state["gateway_connected"] is not False:
        raise ValueError("Offline readiness must not claim live verification")
    return (
        f'{state["equity_count"]}/70 equities + 3 indexes · '
        f'{state["timeframe"]} · Quote {state["quote_status"]} · '
        f'Candles {state["candle_status"]} · '
        f'{state["filter_coverage"]}/5 filters · '
        f'Options {state["option_status"]} · Super Five WAIT · '
        'Oracle not connected')
