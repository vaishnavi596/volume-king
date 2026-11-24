"""Read-only exact-frame C/N/F/O source endpoint audit.

Distinguishes cached context from independent directional voting evidence.
This module cannot request providers, write orders, or certify live timestamps.
"""
from math import isfinite
from datetime import date
from five_engine import completed_timeframe_candle_balance


def _positive_stamp(value):
    return type(value) in (int, float) and isfinite(value) and value > 0


def four_box_source_readiness(*, symbol, timeframe, generation, history,
                              news_cache=None, futures_cache=None,
                              option_context=None, now):
    """Describe what real cache data can prove; never synthesize a vote.

    Note: caller's contexts have no authenticated independent directional
    provenance; verified LIVE directional outputs are always unavailable.
    """
    if (not isinstance(symbol, str) or not symbol.strip()
            or timeframe not in ("1m", "3m", "5m")
            or type(generation) is not int or generation < 0
            or not _positive_stamp(now)):
        raise ValueError("Valid exact symbol/timeframe/generation/time required")
    history = history if isinstance(history, dict) else {}
    news_cache = news_cache if isinstance(news_cache, dict) else {}
    option_context = option_context if isinstance(option_context, dict) else {}
    futures_cache = futures_cache if isinstance(futures_cache, dict) else {}
    exact_history = (history.get("source") == "Dhan"
                     and history.get("_scanner_timeframe") == timeframe
                     and isinstance(history.get("bars"), (tuple, list)))
    balance = (completed_timeframe_candle_balance(history, timeframe, now=now)
               if exact_history else None)
    candles = history.get("bars") if exact_history else []
    news = news_cache.get("items")
    headlines = len(news) if isinstance(news, (tuple, list)) else 0
    # The current news source is RSS context; no verified price-impact source.
    option_match = (option_context.get("source") == "dhan"
                    and option_context.get("symbol") == symbol
                    and isinstance(option_context.get("expiry"), str)
                    and bool(option_context["expiry"].strip())
                    and option_context.get("signal_eligible") is False)
    # Context futures LTP/OI without broker-certified trade side is not a vote.
    expiry=futures_cache.get("expiry")
    ltp=futures_cache.get("ltp")
    try:
        expiry_valid=(isinstance(expiry,str) and date.fromisoformat(expiry).isoformat()==expiry)
    except ValueError:
        expiry_valid=False
    futures_match = (futures_cache.get("source") == "Dhan"
                     and futures_cache.get("symbol") == symbol
                     and futures_cache.get("underlying") == symbol
                     and futures_cache.get("exchange_segment") == "NSE_FNO"
                     and futures_cache.get("mapping_verified") is True
                     and expiry_valid
                     and isinstance(futures_cache.get("contract"), str)
                     and bool(futures_cache["contract"].strip())
                     and type(ltp) in (int,float) and isfinite(ltp) and ltp>0
                     and futures_cache.get("freshness") == "unverified"
                     and futures_cache.get("direction") is None
                     and futures_cache.get("direction_verified") is False
                     and futures_cache.get("signal_eligible") is False
                     and futures_cache.get("live_orders_enabled") is False)
    sources = {
        "C": {"cache_present": bool(candles), "context_count": len(candles),
              "historical_direction_available": balance is not None,
              "historical_direction": ("BULLISH" if balance["bullish"] > balance["bearish"]
                                       else "BEARISH" if balance["bearish"] > balance["bullish"]
                                       else "NEUTRAL") if balance else None,
              "historical_bullish": balance["bullish"] if balance else None,
              "historical_bearish": balance["bearish"] if balance else None,
              "blocker": ("NONE_HIST_ONLY_NOT_LIVE" if balance else
                          "EXACT_FRAME_DHAN_CANDLES_MISSING" if not candles else
                          "HIST_CANDLE_DIRECTION_OR_SPACING_NOT_READY")},
        "N": {"cache_present": headlines > 0, "context_count": headlines,
              "historical_direction_available": False,
              "blocker": ("INDEPENDENT_VERIFIED_NEWS_IMPACT_NOT_WIRED" if headlines
                          else "SYMBOL_NEWS_HEADLINES_MISSING")},
        "F": {"cache_present": futures_match, "context_count": int(futures_match),
              "historical_direction_available": False,
              "blocker": ("INDEPENDENT_VALIDATED_FUTURES_TRADE_FLOW_NOT_WIRED"
                          if futures_match else "VERIFIED_FUTURES_CONTRACT_CONTEXT_MISSING")},
        "O": {"cache_present": option_match, "context_count": int(option_match),
              "historical_direction_available": False,
              "blocker": ("INDEPENDENT_EXPIRY_SCOPED_OPTION_TRADE_FLOW_NOT_WIRED"
                          if option_match else "MATCHING_DHAN_OPTION_EXPIRY_CONTEXT_MISSING")},
    }
    for row in sources.values():
        row["live_direction_verified"] = False
        row["source_evidence_mode"] = "HIST_ONLY" if row.get("historical_direction_available") else "CONTEXT_ONLY"
    return {"mode": "FOUR_BOX_CACHE_ONLY_SOURCE_READINESS",
            "symbol": symbol, "timeframe": timeframe, "generation": generation,
            "box_sources": sources, "live_vote_count": 0,
            "provider_requests": 0, "orders_sent": 0,
            "scope": "CACHE_CONTEXT_NOT_PROVIDER_PROOF"}
