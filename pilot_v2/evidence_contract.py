"""Server-side shape gate for opt-in V2 evidence delivery.

This validates transport size/shape, NOT Dhan provenance. Only a separately
reviewed trusted collector may supply evidence events. No synthetic producer
or quote-to-candle conversion exists in this module.
"""
import json

EVENT_FIELDS = {
    "candles": frozenset(("kind", "symbol", "timeframe", "revision", "bars")),
    "candle_trend": frozenset(("kind", "symbol", "timeframe", "revision", "evidence")),
    "expiries": frozenset(("kind", "symbol", "revision", "available")),
    "options": frozenset(("kind", "payload")),
    "strikes": frozenset(("kind", "payload")),
    "listed_window": frozenset((
        "kind", "symbol", "expiry", "revision", "observed_at", "spot", "listed_rows")),
    "option_factors": frozenset(("kind", "symbol", "timeframe", "revision", "evidence")),
}



def _bounded_json(value, depth=0):
    """Reject pathological provider objects before HTTP serialization."""
    if depth > 12:
        raise ValueError("Source evidence nesting exceeds limit")
    if value is None or type(value) in (bool, int):
        return
    if type(value) is float:
        from math import isfinite
        if not isfinite(value):
            raise ValueError("Nonfinite source number")
        return
    if type(value) is str:
        if len(value.encode("utf-8")) > 1024:
            raise ValueError("Source evidence string oversized")
        return
    if type(value) is list:
        if len(value) > 2000:
            raise ValueError("Source evidence list oversized")
        for item in value:
            _bounded_json(item, depth + 1)
        return
    if type(value) is dict:
        if len(value) > 32:
            raise ValueError("Source evidence record oversized")
        for key, item in value.items():
            if type(key) is not str or len(key) > 64:
                raise ValueError("Invalid source evidence key")
            if key in ("live_verified", "broker_token", "access_token",
                       "private_key", "device_bearer"):
                raise ValueError("Prohibited source evidence field")
            _bounded_json(item, depth + 1)
        return
    raise ValueError("Unsupported source evidence JSON type")


def validate_evidence_envelope(value):
    """Reject extra fields, non-JSON, unbounded and fabricated LIVE metadata."""
    if type(value) is not dict or set(value) != {"events"}:
        raise ValueError("Invalid source evidence envelope")
    events = value["events"]
    if type(events) is not list or not 1 <= len(events) <= 32:
        raise ValueError("Invalid source evidence count")
    for item in events:
        if (type(item) is not dict or type(item.get("kind")) is not str
                or item["kind"] not in EVENT_FIELDS
                or set(item) != EVENT_FIELDS[item["kind"]]):
            raise ValueError("Invalid source evidence event")
        if "symbol" in item and (
                type(item["symbol"]) is not str
                or not 1 <= len(item["symbol"]) <= 40
                or not all(ch.isascii() and (ch.isalnum() or ch in "-_&")
                           for ch in item["symbol"])):
            raise ValueError("Invalid evidence instrument")
        if "revision" in item and (
                type(item["revision"]) is not int or item["revision"] < 0):
            raise ValueError("Invalid evidence revision")
    _bounded_json(value)
    try:
        serialized = json.dumps(value, allow_nan=False, separators=(",", ":"))
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Invalid source evidence encoding") from None
    if len(serialized.encode("utf-8")) > 65536:
        raise ValueError("Source evidence too large")
    return value
