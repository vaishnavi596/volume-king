"""V2 read-only completed-candle technical panel.

Uses the existing validated historical indicator bridge; does not request
quotes, fabricate live signals, or modify the five evidence-gated filters.
"""
from legacy_technical_bridge import historical_scanner_analysis

def historical_indicator_panel(history, symbol, timeframe, *, selected_equities=()):
    context = historical_scanner_analysis(
        history, symbol, timeframe, selected_equities=selected_equities)
    indicators = context.get("indicators")
    if context["status"] != "HIST" or not indicators:
        return ("EMA 20/50 WAIT · RSI 14 WAIT · ATR 14 WAIT · levels WAIT",)
    return (
        f'EMA20 {indicators["ema20"]:.2f} · EMA50 {indicators["ema50"]:.2f} HIST',
        f'RSI14 {indicators["rsi14"]:.1f} · ATR14 {indicators["atr14"]:.2f} HIST',
        f'Historical support {indicators["support"]:.2f} · '
        f'resistance {indicators["resistance"]:.2f} (unverified)',
    )
