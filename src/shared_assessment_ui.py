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
    fetched = record.get("fetched")
    if (type(fetched) not in (int, float) or not math.isfinite(fetched)
            or type(now) not in (int, float) or not math.isfinite(now)
            or type(max_age) not in (int, float) or not math.isfinite(max_age)
            or max_age < 0 or now < fetched or now - fetched > max_age):
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
    if (set(factors) != {"news", "futures", "options", "candle"}
            or any(not isinstance(row, dict)
                   or row.get("status") not in ("available", "unavailable")
                   for row in factors.values())):
        return ["Oracle 4 factors / 5 filters • WAIT • incomplete factors"]
    # A malformed/unhashable id must show WAIT, never crash a 54-symbol view.
    if (len(filters) != len(FILTER_NAMES)
            or any(not isinstance(item, dict)
                   or not isinstance(item.get("id"), str)
                   or item["id"] not in FILTER_NAMES
                   or item.get("status") not in ("available", "unavailable")
                   for item in filters)):
        return ["Oracle 4 factors / 5 filters • WAIT • incomplete filters"]
    indexed = {item["id"]: item for item in filters}
    if set(indexed) != set(FILTER_NAMES):
        return ["Oracle 4 factors / 5 filters • WAIT • incomplete filters"]
    # Only label a *validated full contract* as a known server placeholder.
    # An incomplete payload remains malformed even when it says not_configured.
    if data.get("collection_status") == "not_configured":
        if (any(row["status"] != "unavailable" for row in factors.values())
                or any(row.get("status") != "unavailable" for row in filters)):
            return ["Oracle 4 factors / 5 filters • WAIT • inconsistent server response"]
        return ["Oracle 4 factors / 5 filters • WAIT • server producer not configured"]
    lines = ["Oracle 4 factors / 5 filters • informational only • live orders OFF"]
    labels = {"oi_support": "OI Support", "oi_resistance": "OI Resistance",
              "max_pain": "Max Pain", "pcr": "PCR", "candle_trend": "Candle"}
    for key in FILTER_NAMES:
        row = indexed[key]
        value = row.get("value")
        if row.get("status") != "available":
            # Show only allowlisted reasons; never render arbitrary upstream text.
            reasons = {
                "option_chain_unavailable": "option chain unavailable",
                "expiry_unavailable": "expiry unavailable",
                "candle_history_unavailable": "candle history unavailable",
                "stale_data": "stale data",
                "not_configured": "data source not configured",
            }
            reason = row.get("reason")
            detail = reasons.get(reason) if isinstance(reason, str) else None
            rendered = "WAIT" + (" • " + detail if detail else "")
        elif (key != "candle_trend" and type(value) in (int, float)
              and math.isfinite(value) and value > 0):
            rendered = f"{value:.3f}" if key == "pcr" else f"{value:,.2f}"
        elif isinstance(value, str) and key == "candle_trend" and value in ("bullish", "bearish", "neutral", "BULLISH", "BEARISH", "NEUTRAL"):
            rendered = value.upper() + " • historical/unverified"
        else:
            rendered = "WAIT"
        lines.append(labels[key] + ": " + rendered)
    lines.append("News/Futures/Options/Candle: no verified 0–100 scores; not a trade signal")
    return lines
