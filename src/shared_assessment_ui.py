"""Strict presentation of Oracle shared assessment: unverified != bullish signal."""
import math
import time

FILTER_NAMES = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")

def assessment_lines(symbol, cached, *, now=None, max_age=180):
    """Display cached per-symbol values without interpreting stale metrics as votes."""
    if not isinstance(symbol, str) or not symbol or not isinstance(cached, dict):
        return ["Oracle 4 factors / 5 filters • WAIT • no matching cache"]
    record = cached.get(symbol)
    if not isinstance(record, dict):
        return ["Oracle 4 factors / 5 filters • WAIT • not requested"]
    now = time.monotonic() if now is None else now
    if (not isinstance(record.get("fetched"), (int, float))
            or now < record["fetched"] or now - record["fetched"] > max_age):
        return ["Oracle 4 factors / 5 filters • WAIT • cached assessment expired"]
    data = record.get("data")
    if not isinstance(data, dict) or data.get("symbol") != symbol:
        return ["Oracle 4 factors / 5 filters • WAIT • mismatched symbol"]
    if data.get("live_orders_enabled") is not False or data.get("signal_eligible") is not False:
        return ["Oracle 4 factors / 5 filters • WAIT • unsafe response"]
    filters = data.get("assessment_filters")
    factors = data.get("factors")
    if not isinstance(filters, list) or not isinstance(factors, dict):
        return ["Oracle 4 factors / 5 filters • WAIT • malformed response"]
    if set(factors) != {"news", "futures", "options", "candle"}:
        return ["Oracle 4 factors / 5 filters • WAIT • incomplete factors"]
    indexed = {f.get("id"): f for f in filters if isinstance(f, dict)}
    if set(indexed) != set(FILTER_NAMES) or len(filters) != 5:
        return ["Oracle 4 factors / 5 filters • WAIT • incomplete filters"]
    lines = ["Oracle 4 factors / 5 filters • informational only • live orders OFF"]
    labels = {"oi_support": "OI Support", "oi_resistance": "OI Resistance",
              "max_pain": "Max Pain", "pcr": "PCR", "candle_trend": "Candle"}
    for key in FILTER_NAMES:
        row = indexed[key]
        value = row.get("value")
        if row.get("status") != "available":
            rendered = "WAIT"
        elif type(value) in (int, float) and math.isfinite(value):
            rendered = f"{value:.3f}" if key == "pcr" else f"{value:,.2f}"
        elif isinstance(value, str) and key == "candle_trend" and value in ("bullish", "bearish", "neutral", "BULLISH", "BEARISH", "NEUTRAL"):
            rendered = value.upper() + " • historical/unverified"
        else:
            rendered = "WAIT"
        lines.append(labels[key] + ": " + rendered)
    lines.append("News/Futures/Options/Candle: no verified 0–100 scores; not a trade signal")
    return lines
