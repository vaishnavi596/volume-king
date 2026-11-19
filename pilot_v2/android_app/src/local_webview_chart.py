"""Offline-only safe historical chart HTML for a possible future WebView.

No external URLs, remote scripts, session tokens, provider access, or Flet
WebView creation. A native candle/line chart remains the current V2 default.
"""
from html import escape
from math import isfinite
from app_state import INDEXES, valid_symbol
from candle_history import TIMEFRAMES, CandleEvidenceError, validate_completed_bars

WINDOWS = (15, 35, 70)
STYLES = ("Candles", "Line")


def historical_chart_html(history, symbol, timeframe, *, selected_equities=(),
                          limit=35, style="Candles"):
    """Return local SVG HTML only for retained validated completed OHLC bars.

    None means WAIT; never fabricate candles, trend, volume or exchange time.
    The caller must still prove actual WebView support on Android before use.
    """
    if (type(symbol) is not str or
            not (symbol in INDEXES or valid_symbol(symbol)) or
            type(timeframe) is not str or timeframe not in TIMEFRAMES or
            type(limit) is not int or limit not in WINDOWS or style not in STYLES):
        raise ValueError("Unsupported local historical chart selection")
    if not callable(getattr(history, "view", None)):
        raise ValueError("Validated candle history view required")
    selected = tuple(selected_equities)
    if symbol not in INDEXES and symbol not in selected:
        return None
    result = history.view(symbol, timeframe, selected_equities=selected)
    if type(result) is not dict or result.get("status") != "HIST":
        return None
    bars = validate_completed_bars(list(result.get("bars", ())))
    bars = bars[-limit:]
    low = min(item["low"] for item in bars)
    high = max(item["high"] for item in bars)
    if not isfinite(high - low):
        raise CandleEvidenceError("Invalid historical price range")
    span = high - low if high > low else max(high * 0.001, 0.01)
    chart_width = max(360, len(bars) * 14 + 62)
    left, top, graph_height = 32, 22, 184

    def y(value):
        return top + (high - value) / span * graph_height

    graphics = []
    for i, item in enumerate(bars):
        center = left + i * 14 + 7
        if style == "Candles":
            shade = "#16c784" if item["close"] >= item["open"] else "#ff7890"
            y_high, y_low = y(item["high"]), y(item["low"])
            y_open, y_close = y(item["open"]), y(item["close"])
            graphics.append(
                f'<line x1="{center}" x2="{center}" y1="{y_high:.1f}" '
                f'y2="{y_low:.1f}" stroke="{shade}" stroke-width="2"/>'
                f'<rect x="{center - 4}" y="{min(y_open, y_close):.1f}" '
                f'width="8" height="{max(1.0, abs(y_open - y_close)):.1f}" '
                f'fill="{shade}"/>')
    if style == "Line":
        coords = " ".join(
            f"{left + i * 14 + 7},{y(item['close']):.1f}"
            for i, item in enumerate(bars))
        graphics.append(
            f'<polyline points="{coords}" fill="none" stroke="#e9b949" '
            f'stroke-width="2.5"/>')
    heading = escape(f"{symbol} · {timeframe} · completed historical candles", quote=True)
    graphic = "".join(graphics)
    return (
        '<!doctype html><html><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<meta http-equiv="Content-Security-Policy" '
        'content="default-src &#39;none&#39;; style-src &#39;unsafe-inline&#39;">'
        '<style>html,body{margin:0;background:#080f18;color:#eaf1f6;'
        'font:14px sans-serif}header{padding:10px;color:#e9b949}'
        'small{display:block;padding:8px;color:#b0bdc6}</style>'
        '</head><body><header>' + heading + '</header>'
        f'<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-label="{heading}" viewBox="0 0 {chart_width} 235" '
        f'width="100%" height="245">'
        f'<text x="2" y="16" fill="#b0bdc6" font-size="12">{high:.2f}</text>'
        f'{graphic}'
        f'<text x="2" y="228" fill="#b0bdc6" font-size="12">{low:.2f}</text>'
        '</svg><small>HIST / unverified · not LIVE · not a trade signal</small>'
        '</body></html>')
