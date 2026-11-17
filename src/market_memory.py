"""BOT KING read-only historical market-memory analytics (no feeds, file I/O or trades).

A memory record is a *completed session's observation*, never a verified
prediction or an explanation of causality. Persist validated records using
the separately governed storage layer; do not confuse historical evidence
with live five-engine eligibility.
"""
from dataclasses import dataclass
from datetime import date
from math import isfinite
from statistics import median


@dataclass(frozen=True)
class MarketSession:
    symbol: str
    day: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    source: str = "Dhan"
    completed: bool = True
    explanation: str = "Observed price and volume only; cause not established"

    def __post_init__(self):
        if not isinstance(self.symbol, str) or not self.symbol or not self.symbol.isascii():
            raise ValueError("Invalid symbol")
        if not isinstance(self.day, str) or date.fromisoformat(self.day).isoformat() != self.day:
            raise ValueError("Invalid market date")
        if self.source != "Dhan" or self.completed is not True:
            raise ValueError("Only completed Dhan source sessions may enter memory")
        values = (self.open, self.high, self.low, self.close, self.volume)
        if any(type(v) not in (int, float) or not isfinite(v) for v in values):
            raise ValueError("Non-finite or malformed session values")
        if min(self.open, self.high, self.low, self.close) <= 0 or self.volume < 0:
            raise ValueError("Nonpositive prices or negative volume")
        if self.high < max(self.open, self.close, self.low) or self.low > min(self.open, self.close, self.high):
            raise ValueError("Invalid OHLC geometry")
        if self.explanation != "Observed price and volume only; cause not established":
            raise ValueError("Unsupported explanation/causal attribution")


def remember_session(existing, observation, *, max_sessions=31):
    """Return a new bounded immutable history; reject conflicting history revisions.

    Calendar window is decided by session dates, not by local device clock.
    The caller must persist the resulting tuple transactionally, if desired.
    """
    if type(max_sessions) is not int or not 2 <= max_sessions <= 62:
        raise ValueError("Invalid retention")
    if not isinstance(observation, MarketSession):
        raise ValueError("Expected validated session")
    if not isinstance(existing, (list, tuple)) or any(
        not isinstance(x, MarketSession) or x.symbol != observation.symbol for x in existing
    ):
        raise ValueError("Memory mixed symbols or unvalidated")
    by_day = {}
    for session in existing:
        if session.day in by_day and by_day[session.day] != session:
            raise ValueError("Conflicting session versions")
        by_day[session.day] = session
    previous = by_day.get(observation.day)
    if previous is not None and previous != observation:
        raise ValueError("Historical change needs explicit reconciliation")
    by_day[observation.day] = observation
    return tuple(by_day[d] for d in sorted(by_day)[-max_sessions:])


def analyze_memory(history, *, symbol, as_of, lookback=30):
    """Describe past observations and *conditional scenarios*, never trade signals.

    Only observations whose date is strictly before as_of are used: no
    look-ahead bias, no assumed holiday candles or forecast probabilities.
    """
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("Invalid symbol")
    if not isinstance(as_of, str) or date.fromisoformat(as_of).isoformat() != as_of:
        raise ValueError("Invalid as_of date")
    if type(lookback) is not int or not 2 <= lookback <= 62:
        raise ValueError("Invalid lookback")
    if not isinstance(history, (list, tuple)) or any(
        not isinstance(x, MarketSession) or x.symbol != symbol for x in history
    ):
        raise ValueError("Invalid history")
    by_day = {}
    for item in history:
        if item.day in by_day and item != by_day[item.day]:
            raise ValueError("Conflicting historical sessions")
        by_day[item.day] = item
    rows = [by_day[d] for d in sorted(by_day) if d < as_of][-lookback:]
    base = {
        "symbol": symbol, "as_of": as_of, "historical": True,
        "verified_live": False, "signal_eligible": False,
        "bullish_score": None, "bearish_score": None,
        "forecast_probability": None, "causal_explanation_verified": False,
        "session_count": len(rows),
    }
    if len(rows) < 5:
        return dict(base, status="INSUFFICIENT_HISTORY",
                    interpretation="Not enough completed sessions for historical context",
                    conditions=[], provenance="Completed Dhan OHLCV; historical/unverified")
    last = rows[-1]
    first = rows[0]
    change = (last.close / first.close - 1) * 100
    ranges = [(x.high - x.low) / x.close * 100 for x in rows]
    median_range = median(ranges)
    median_volume = median(x.volume for x in rows)
    last_range = ranges[-1]
    conditions = []
    if change > 2:
        conditions.append("Past-window upward close-to-close drift")
    elif change < -2:
        conditions.append("Past-window downward close-to-close drift")
    else:
        conditions.append("Past-window range-bound drift")
    if median_range > 0 and last_range > median_range * 1.5:
        conditions.append("Latest completed session range above its historical median")
    if median_volume > 0 and last.volume > median_volume * 1.5:
        conditions.append("Latest completed session volume above its historical median")
    prior_high = max(x.high for x in rows[:-1])
    prior_low = min(x.low for x in rows[:-1])
    if last.close > prior_high:
        conditions.append("Latest close above preceding observed highs")
    elif last.close < prior_low:
        conditions.append("Latest close below preceding observed lows")
    return dict(base, status="HISTORICAL_CONTEXT", last_session=last.day,
                observations=conditions, sample_start=first.day,
                sample_end=last.day, median_range_pct=round(median_range, 3),
                drift_pct=round(change, 3),
                scenarios=[
                    "If movement persists with independently verified fresh volume, continuation is possible",
                    "If recent breakout fails or volatility rises, reversal or consolidation is possible",
                ],
                provenance="Completed Dhan OHLCV; historical/unverified",
                interpretation="Observed conditions only; why it happened is unproven without independently sourced evidence")
