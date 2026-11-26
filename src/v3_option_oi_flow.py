"""Measured option-chain OI-change positioning component (J2). No requests.

Policy (owner-approved 26 Nov 2026): Dhan does not supply trade-side flow, so
the O box may use a *measured* directional ratio derived from the exact-expiry,
exact-underlying Dhan option-chain window: change in open interest since the
previous session close (``oi - previous_oi``) on the seven listed strikes.

  bullish pressure = put OI build-up + call OI unwinding
  bearish pressure = call OI build-up + put OI unwinding

This is a positioning heuristic, not an exchange trade-side measurement; it is
labelled ``measured_oi_change`` and never ``validated_trade_flow``. PCR, Max
Pain, raw OI, volume and LTP alone never vote. It is eligible only while the
chain was observed from authenticated Dhan within the freshness window AND the
underlying quote carries a Dhan last-trade timestamp that is itself fresh.
"""
from datetime import date
from math import isfinite

BASIS = "measured_oi_change"
MAX_AGE_SECONDS = 90
# Net |change| must be at least this share of the window's total OI, so a
# quiet chain cannot manufacture a direction from rounding-level moves.
MIN_CHANGE_SHARE = 0.01


def _number(value, *, allow_zero=True):
    return (type(value) in (int, float) and isfinite(value)
            and (value >= 0 if allow_zero else value > 0))


def underlying_quote_live(quote, *, symbol, now):
    """True only for an uncached Dhan quote with a fresh last-trade timestamp."""
    if (not isinstance(quote, dict) or not _number(now, allow_zero=False)
            or quote.get("source") != "Dhan" or quote.get("cached")
            or quote.get("symbol") not in (None, symbol)
            or quote.get("timestamp_origin") != "DHAN_QUOTE_LAST_TRADE_TIME"
            or quote.get("freshness") != "exchange_verified"
            or quote.get("live_verified") is not True):
        return False
    stamp = quote.get("quote_timestamp")
    return _number(stamp, allow_zero=False) and 0 <= now - stamp <= MAX_AGE_SECONDS


def window_oi_change(metrics):
    """Direction share from previous-session OI change over the seven strikes.

    No freshness or underlying-quote checks here: callers decide whether the
    result is a LIVE component (``oi_change_component``) or a HIST display.
    Returns ``((bullish, bearish), reason)`` or ``(None, reason)``.
    """
    window = metrics.get("atm_window") if isinstance(metrics, dict) else None
    rows = window.get("rows") if isinstance(window, dict) else None
    if (not isinstance(window, dict) or window.get("source") != "dhan"
            or not isinstance(rows, (list, tuple)) or len(rows) != 7):
        return None, "Seven listed strikes unavailable"
    delta = {"ce": 0.0, "pe": 0.0}
    total_oi = 0.0
    strikes = []
    for row in rows:
        strike = row.get("strike") if isinstance(row, dict) else None
        if not _number(strike, allow_zero=False):
            return None, "Invalid strike"
        strikes.append(strike)
        for side in ("ce", "pe"):
            leg = row.get(side)
            oi = leg.get("oi") if isinstance(leg, dict) else None
            previous = leg.get("previous_oi") if isinstance(leg, dict) else None
            if not _number(oi) or not _number(previous):
                return None, "Previous OI missing for a listed leg"
            delta[side] += oi - previous
            total_oi += oi
    if strikes != sorted(set(strikes)) or window.get("atm") != strikes[3]:
        return None, "Invalid ATM strike ordering"
    bull = max(delta["pe"], 0.0) + max(-delta["ce"], 0.0)
    bear = max(delta["ce"], 0.0) + max(-delta["pe"], 0.0)
    pressure = bull + bear
    if total_oi <= 0 or pressure <= 0 or pressure < MIN_CHANGE_SHARE * total_oi:
        return None, "OI change too small to measure direction"
    bullish = min(100, max(0, round(100 * bull / pressure)))
    bearish = 100 - bullish
    if bullish == bearish:
        return None, "OI change balanced"
    return (bullish, bearish), "OK"


def oi_change_component(metrics, *, quote, symbol, timeframe, generation,
                        observed_at, now):
    """Return ``(component, reason)``; component is None whenever evidence fails."""
    if timeframe not in ("1m", "3m", "5m"):
        return None, "Unsupported frame"
    if type(generation) is not int:
        return None, "Generation missing"
    if not _number(now, allow_zero=False) or not _number(observed_at, allow_zero=False):
        return None, "Observation time missing"
    if not 0 <= now - observed_at <= MAX_AGE_SECONDS:
        return None, "Option chain observation stale"
    if (not isinstance(metrics, dict) or metrics.get("source") != "dhan"
            or metrics.get("symbol") != symbol or metrics.get("historical") is True):
        return None, "Option chain identity or provenance mismatch"
    expiry = metrics.get("expiry")
    try:
        if type(expiry) is not str or date.fromisoformat(expiry).isoformat() != expiry:
            raise ValueError("expiry")
    except (TypeError, ValueError):
        return None, "Option expiry invalid"
    if not underlying_quote_live(quote, symbol=symbol, now=now):
        return None, "Underlying Dhan last-trade timestamp not fresh"
    measured, why = window_oi_change(metrics)
    if measured is None:
        return None, why
    bullish, bearish = measured
    return ({"source": "Dhan", "verified": True, "available": True,
             "direction_basis": BASIS,
             "bias": "BULLISH" if bullish > bearish else "BEARISH",
             "bullish": bullish, "bearish": bearish,
             "symbol": symbol, "underlying": symbol, "timeframe": timeframe,
             "generation": generation, "expiry": expiry,
             "contract": symbol + " " + expiry + " 7-strike OI window",
             "timestamp": observed_at, "mapping_verified": True,
             "live_verified": True, "historical": False}, "OK")
