"""Pure, read-only Batch 4 five-engine evidence contract.

Percentages are directional *evidence ratios*, never win probabilities. An
unverified or unavailable engine cannot vote. This module performs no I/O.
"""
from dataclasses import dataclass
from math import isfinite
from typing import Optional

ENGINE_NAMES = ("technical", "candle", "news", "futures", "options")


@dataclass(frozen=True)
class EngineEvidence:
    name: str
    bullish: Optional[int] = None
    bearish: Optional[int] = None
    verified: bool = False
    reason: str = "Data unavailable"
    timestamp: Optional[float] = None
    source: str = ""

    def __post_init__(self):
        if self.name not in ENGINE_NAMES:
            raise ValueError("Unsupported engine")
        if self.bullish is None or self.bearish is None:
            if self.bullish is not None or self.bearish is not None:
                raise ValueError("Both directions must be present or absent")
        elif (type(self.bullish) is not int or type(self.bearish) is not int or
              not 0 <= self.bullish <= 100 or not 0 <= self.bearish <= 100 or
              self.bullish + self.bearish != 100):
            raise ValueError("Directional evidence must be complementary integer percentages")
        if self.timestamp is not None and (isinstance(self.timestamp, bool) or
             not isinstance(self.timestamp, (int, float)) or not isfinite(self.timestamp) or
             self.timestamp <= 0):
            raise ValueError("Invalid evidence timestamp")

    @property
    def eligible(self):
        return (self.verified and self.bullish is not None and self.bearish is not None
                and self.timestamp is not None and bool(self.source))

    def display(self):
        if not self.eligible:
            return {"bullish": None, "bearish": None, "state": "WAIT", "reason": self.reason}
        return {"bullish": self.bullish, "bearish": self.bearish,
                "state": "BULLISH" if self.bullish > self.bearish else
                         "BEARISH" if self.bearish > self.bullish else "NEUTRAL",
                "reason": self.reason}


def combine_evidence(evidence, *, min_engines=3, min_margin=10):
    """Require independent, eligible engine agreement; never treat missing as zero.

    A 3/5 quorum is necessary but not sufficient: at least 2/3 of eligible
    directional engines must agree and the average margin must exceed threshold.
    """
    if (type(min_engines) is not int or not 1 <= min_engines <= len(ENGINE_NAMES) or
            type(min_margin) is not int or not 0 <= min_margin <= 100):
        raise ValueError("Invalid coverage or margin policy")
    if not isinstance(evidence, (list, tuple)) or len(evidence) != len(ENGINE_NAMES):
        raise ValueError("Exactly five engine entries required")
    if (any(not isinstance(e, EngineEvidence) for e in evidence) or
            tuple(e.name for e in evidence) != ENGINE_NAMES):
        raise ValueError("Engines must be unique and in canonical order")
    eligible = [e for e in evidence if e.eligible]
    coverage = len(eligible)
    base = {"state": "WAIT", "coverage": coverage, "required": min_engines,
            "bullish": None, "bearish": None, "reason": "Insufficient verified engines"}
    if coverage < min_engines:
        return base
    bulls = sum(e.bullish > e.bearish for e in eligible)
    bears = sum(e.bearish > e.bullish for e in eligible)
    leader = "BULLISH" if bulls > bears else "BEARISH" if bears > bulls else None
    agreements = max(bulls, bears)
    if leader is None or agreements * 3 < coverage * 2:
        return dict(base, reason="Conflicting engine directions")
    bull = round(sum(e.bullish for e in eligible) / coverage)
    bear = 100 - bull
    if abs(bull - bear) < min_margin or (leader == "BULLISH" and bull <= bear) or (leader == "BEARISH" and bear <= bull):
        return dict(base, reason="Directional margin insufficient or conflicting")
    return {"state": leader, "coverage": coverage, "required": min_engines,
            "bullish": bull, "bearish": bear, "reason": "Verified directional agreement; not win probability"}


def empty_evidence(reason="Awaiting verified data"):
    """Canonical five-engine placeholder; never invent missing percentages."""
    return tuple(EngineEvidence(name=name, reason=reason) for name in ENGINE_NAMES)


def technical_from_votes(votes, *, timestamp=None, source="", verified=False):
    """Convert independent technical votes only, never daily LTP change.

    Accept a collection of normalized bullish/bearish/neutral vote labels.
    Neutral and unknown votes do not contribute directional percentages.
    Historical or unverified votes remain WAIT even if numerical counts exist.
    """
    if not isinstance(votes, (list, tuple)):
        raise ValueError("Technical votes must be a sequence")
    labels = [str(v).strip().upper() for v in votes]
    bullish = sum(v in ("BULLISH", "BUY") for v in labels)
    bearish = sum(v in ("BEARISH", "SELL") for v in labels)
    count = bullish + bearish
    if not count:
        return EngineEvidence("technical", reason="No independent directional technical votes")
    percent = round(100 * bullish / count)
    return EngineEvidence("technical", percent, 100-percent,
                          verified=verified, timestamp=timestamp, source=source,
                          reason="Technical directional vote ratio; not win probability")


def compose_snapshot(*, technical=None, candle=None, news=None, futures=None, options=None):
    """Merge separately sourced engines without treating one as another."""
    provided = dict(technical=technical, candle=candle, news=news,
                    futures=futures, options=options)
    rows = tuple(provided[name] if provided[name] is not None else
                 EngineEvidence(name, reason="Verified "+name+" evidence unavailable")
                 for name in ENGINE_NAMES)
    if any(row.name != name for name, row in zip(ENGINE_NAMES, rows)):
        raise ValueError("Evidence engine name mismatch")
    return {"engines": rows, "combined": combine_evidence(rows)}


def scanner_snapshot(scan_result):
    """Adapt existing scanner votes without network calls or false live labels.

    Candle and technical votes originate from the same scanner calculation;
    expose only the technical slot to avoid correlated double counting.
    Independent price-action evidence requires its own validated algorithm.
    """
    if not isinstance(scan_result, dict):
        return compose_snapshot()
    raw = scan_result.get("votes") or []
    labels = []
    for vote in raw:
        if not isinstance(vote, dict):
            continue
        direction = vote.get("vote")
        if type(direction) is int and direction == 1:
            labels.append("BUY")
        elif type(direction) is int and direction == -1:
            labels.append("SELL")
    source = scan_result.get("source") or ""
    verified = (scan_result.get("live_verified") is True and
                scan_result.get("freshness") in ("verified_live", "live_verified") and
                scan_result.get("historical") is False and source == "Dhan")
    technical = technical_from_votes(labels, verified=verified,
                                      timestamp=scan_result.get("timestamp"), source=source)
    return compose_snapshot(technical=technical)
