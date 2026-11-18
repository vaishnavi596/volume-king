"""V2 FT3 app-owned completed candle -> evidence-gated trend bridge.

Transport trust is established by the future authenticated caller, not here.
This contract never derives a trading direction from OHLCV and never calls Dhan.
"""
from candle_history import CandleEvidenceError
from filter_evidence import FilterEvidenceError


def accept_candle_trend(candles, filters, symbol, timeframe, revision, evidence,
                        *, selected_equities=(), trusted_transport=False):
    """Bind a producer-calculated direction to the exact retained final bar.

    A historical candle alone cannot authorize a bullish/bearish factor.
    Require caller-authenticated evidence from the same symbol/timeframe and
    same final completed bar, then use the existing per-factor replay guard.
    """
    allowed = ("NIFTY", "BANKNIFTY", "SENSEX") + tuple(selected_equities)
    if (trusted_transport is not True or type(symbol) is not str
            or symbol not in allowed or timeframe not in ("1m", "3m", "5m")):
        raise FilterEvidenceError("Untrusted candle trend context")
    snapshot = candles.view(symbol, timeframe, selected_equities=selected_equities)
    if snapshot["status"] != "HIST" or not snapshot["bars"]:
        raise CandleEvidenceError("No retained completed candle history")
    if (type(evidence) is not dict
            or type(evidence.get("observed_at")) is not int
            or evidence["observed_at"] != snapshot["bars"][-1]["timestamp"]):
        raise FilterEvidenceError("Candle trend observation must match last completed bar")
    return filters.accept_available(
        symbol, timeframe, revision, {"candle_trend": evidence},
        allowed_symbols=allowed, trusted_transport=True)
