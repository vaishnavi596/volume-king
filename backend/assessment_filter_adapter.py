"""Pure read-only adapter for five assessment filter slots.

Only use already collected Dhan option metrics. A calculated value is
informational, never a verified directional score. No broker I/O here.
"""
from math import isfinite

FILTER_IDS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")


def option_filter_rows(metrics=None):
    """Map validated numeric metrics to informational filter rows.

    Do not promote stale/unverified option data into a live signal.
    OI support/resistance require strike-level directional validation and
    candle trend requires independent candle evidence.
    """
    rows = {key: {"id": key, "status": "unavailable",
                  "reason": "not_configured"} for key in FILTER_IDS}
    if not isinstance(metrics, dict) or metrics.get("signal_eligible") is not False:
        return [rows[key] for key in FILTER_IDS]
    for key in ("max_pain", "pcr"):
        value = metrics.get(key)
        if (type(value) in (int, float) and isfinite(value) and value > 0
                and metrics.get("freshness") == "unverified"):
            rows[key] = {"id": key, "status": "available",
                         "value": value, "verification": "unverified",
                         "source": "dhan"}
    return [rows[key] for key in FILTER_IDS]


def read_only_assessment(symbol, metrics=None):
    """Assemble a fail-closed shared assessment from *already cached* metrics.

    This is a pure response builder: the caller must validate the symbol and
    obtain any evidence independently. No broker calls or directional scoring.
    """
    rows = option_filter_rows(metrics)
    has_info = any(row["status"] == "available" for row in rows)
    return {
        "protocol": 2,
        "symbol": symbol,
        "source": "dhan",
        "collection_status": "partial_unverified" if has_info else "not_configured",
        "freshness": "unverified",
        "assessment_filters": rows,
        "factors": {name: {"status": "unavailable", "bullish": None, "bearish": None}
                    for name in ("news", "futures", "options", "candle")},
        "bullish_score": None,
        "bearish_score": None,
        "signal_eligible": False,
        "live_orders_enabled": False,
    }
