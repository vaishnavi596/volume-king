"""V2 app-only adapter for original V1 technical engines, NOT a broker or vote producer.

Only validated completed Dhan candle cache is eligible. Legacy technical
indicators describe historical price patterns, never verified five-engine
direction or live profitability. No network, credentials or order API.
"""
from scanner_engine import analyze
from chart_indicators import chart_indicators

TECHNICAL_INDICATORS = ("EMA 9/21", "RSI 14", "MACD", "VWAP", "Supertrend")


def historical_scanner_analysis(candle_history, symbol, timeframe, *,
                                selected_equities=()):
    view = candle_history.view(symbol, timeframe,
                               selected_equities=selected_equities)
    fallback = {"status": "WAIT", "symbol": symbol, "timeframe": timeframe,
                "summary": "Technical Scanner WAIT · 30 completed candles required",
                "indicators": None, "scan": None}
    if view["status"] != "HIST" or view["count"] < 30:
        return fallback
    bars = [
        [b["timestamp"], b["open"], b["high"], b["low"], b["close"], b["volume"]]
        for b in view["bars"]
    ]
    technical = chart_indicators(bars)
    if technical.get("status") != "AVAILABLE":
        return fallback
    result = analyze(bars, selected=TECHNICAL_INDICATORS, timeframe=timeframe)
    # Invalid, missing or incomplete historical evidence must not imply LIVE.
    if result.get("count", 0) < 30 or result.get("timestamp") != bars[-1][0]:
        return fallback
    if result.get("reason", "").startswith(("Invalid", "Irregular", "Need ")):
        return fallback
    state = result.get("bias", "WAIT")
    if state not in ("WAIT", "BULLISH", "BEARISH"):
        return fallback
    summary = (
        f"Technical candles HIST · {symbol} {timeframe} · "
        f"EMA20 {technical['ema20']:.2f} · RSI14 {technical['rsi14']:.1f} · "
        f"scanner {state} (historical, not live/5-filter score)"
    )
    return {"status": "HIST", "symbol": symbol, "timeframe": timeframe,
            "summary": summary, "indicators": technical, "scan": result}
