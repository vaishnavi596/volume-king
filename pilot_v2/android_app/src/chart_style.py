"""Offline V2 Scanner chart style: strict local presentation only.

This preference never changes cached candles, timeframes, provider polling or
trade signals; no V1 WebView/Angel/Yahoo provider code is imported.
"""
CHART_STYLES = ("Candles", "Line")
DEFAULT_CHART_STYLE = "Candles"

def chart_style_choice(value):
    if type(value) is not str or value not in CHART_STYLES:
        raise ValueError("Unsupported local historical chart style")
    return value
