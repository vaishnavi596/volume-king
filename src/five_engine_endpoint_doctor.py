"""STANDARD-2 read-only five-engine end-to-end status explanation.

Reports the precise next verification point. It never requests market data,
certifies an exchange timestamp, publishes snapshots or sends an order.
"""

ENGINE_PATHS = {
    "technical": ("Dhan OHLCV → Oracle /market/candles → exact-frame phone cache",
                  "Scanner 13 technical votes → exact-frame contextual publisher → T box",
                  "CHECK_EXCHANGE_TIMESTAMP_AND_PUBLISHER"),
    "candle": ("Dhan 1m/3m OHLCV → Oracle → phone candle cache",
               "completed contiguous price-action sample → independent C box",
               "VERIFY_INDEPENDENT_CANDLE_DIRECTION_AND_RAW_OHLCV"),
    "news": ("symbol-tagged publisher headlines → local news cache",
             "verified independent news-impact scoring → N box",
             "IMPLEMENT_AUTHENTICATED_SYMBOL_NEWS_IMPACT"),
    "futures": ("Dhan mapped futures contract → authenticated futures data",
                "validated directional trade flow → F box",
                "WIRE_CONTRACT_MAPPING_AND_MEASURED_DIRECTIONAL_FLOW"),
    "options": ("Dhan option chain + exact underlying/expiry/contract",
                "validated directional option trade flow → O box",
                "WIRE_AUTHENTICATED_EXPIRY_SPECIFIC_OPTION_FLOW"),
}

def five_engine_endpoint_diagnostic(*, symbol, timeframe, generation,
                                    technical_calculated, technical_total,
                                    historical_technical_votes,
                                    historical_candle_directional,
                                    news_headline_count, option_context_present,
                                    snapshots_present, market_open,
                                    exchange_timestamp_verified,
                                    raw_dhan_candles_verified=False):
    if not symbol or timeframe not in ("1m","3m","5m") or type(generation) is not int:
        raise ValueError("Exact symbol, timeframe and generation required")
    stages=[]
    for name in ("technical","candle","news","futures","options"):
        start,endpoint,action=ENGINE_PATHS[name]
        if name=="technical":
            hist="HIST_CALCULATED" if historical_technical_votes>0 else "HIST_WAIT_NO_DIRECTIONAL_VOTES"
            blocker=("EXACT_FRAME_PUBLISH_MISSING" if not snapshots_present else
                     "SOURCE_EXCHANGE_TIMESTAMP_UNVERIFIED" if not exchange_timestamp_verified else
                     "INDEPENDENT_LIVE_EVIDENCE_NOT_CONFIRMED")
        elif name=="candle":
            hist="HIST_DIRECTIONAL_AVAILABLE" if historical_candle_directional>=5 else "HIST_WAIT_INSUFFICIENT_DIRECTIONAL_BODIES"
            blocker=("RAW_DHAN_CANDLE_PROVENANCE_UNVERIFIED" if not raw_dhan_candles_verified else
                     "INDEPENDENT_CANDLE_LIVE_ADAPTER_NOT_WIRED")
        elif name=="news":
            hist="HEADLINE_CONTEXT_ONLY" if news_headline_count else "HIST_NO_HEADLINES"
            blocker="NEWS_DIRECTIONAL_IMPACT_ADAPTER_NOT_WIRED"
        elif name=="futures":
            hist="HIST_NO_AUTHENTICATED_DIRECTIONAL_FLOW"
            blocker="FUTURES_DIRECTIONAL_FLOW_ADAPTER_NOT_WIRED"
        else:
            hist="OPTION_CHAIN_CONTEXT_ONLY" if option_context_present else "HIST_NO_OPTION_CHAIN_CONTEXT"
            blocker="OPTIONS_DIRECTIONAL_FLOW_ADAPTER_NOT_WIRED"
        stages.append({
            "engine":name,"symbol":symbol,"timeframe":timeframe,
            "generation":generation,
            "start":start,"endpoint":endpoint,
            "historical_state":hist,
            "live_state":"MARKET_CLOSED" if not market_open else "NOT_VERIFIED",
            "blocked_at":blocker,
            "next_action":action,
            "verified_live":False,
        })
    return {
        "mode":"CACHE_ONLY_NO_PROVIDER_REQUESTS",
        "status":"DIAGNOSTIC_NOT_LIVE_CERTIFICATION",
        "technical_calculated":technical_calculated,
        "technical_total":technical_total,
        "live_verified_box_count":0,
        "market_open":bool(market_open),
        "box_paths":stages,
        "last_endpoint":"PHONE_FIVE_ENGINE_DISPLAY",
        "orders_sent":0,
    }
