"""Pure, read-only Batch 4 five-engine evidence contract.

Percentages are directional *evidence ratios*, never win probabilities. An
unverified or unavailable engine cannot vote. This module performs no I/O.
"""
from dataclasses import dataclass
from math import isfinite
from historical_session_window import historical_regular_session_bars
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
        return (self.verified is True and self.bullish is not None and self.bearish is not None
                and self.timestamp is not None and isinstance(self.source, str) and
                bool(self.source.strip()))

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
    eligible = [e for e in evidence if e.eligible and e.source.strip().casefold() == "dhan"]
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
    if any(not isinstance(v, str) for v in votes):
        return EngineEvidence("technical", reason="Malformed technical vote labels")
    labels = [v.strip().upper() for v in votes]
    if any(v not in ("BULLISH", "BUY", "BEARISH", "SELL", "NEUTRAL", "WAIT") for v in labels):
        return EngineEvidence("technical", reason="Unknown technical vote label")
    bullish = sum(v in ("BULLISH", "BUY") for v in labels)
    bearish = sum(v in ("BEARISH", "SELL") for v in labels)
    count = bullish + bearish
    if count < 3:
        return EngineEvidence("technical", reason="Insufficient independent directional technical votes (minimum 3)")
    percent = round(100 * bullish / count)
    return EngineEvidence("technical", percent, 100-percent,
                          verified=verified, timestamp=timestamp, source=source,
                          reason="Technical directional vote ratio; not win probability")


def independent_engine_source_contract():
    """Static source-wiring coverage, not runtime evidence or an error count.

    Report deliberately incomplete adapters as missing implementations rather
    than claiming the user caused a network error or inventing live percentages.
    """
    return {
        "technical": {"adapter": "scanner_snapshot",
                      "readiness": "SOURCE_FRESHNESS_REQUIRED"},
        "candle": {"adapter": "historical_candle_balance",
                   "readiness": "HISTORICAL_ONLY_INDEPENDENT_LIVE_NOT_WIRED"},
        "news": {"adapter": "news_from_headline_cues",
                 "readiness": "RSS_CONTEXT_ONLY_VERIFIED_IMPACT_NOT_WIRED"},
        "futures": {"adapter": "futures_from_component",
                    "readiness": "MEASURED_DIRECTIONAL_STRENGTH_NOT_WIRED"},
        "options": {"adapter": "option_from_component",
                    "readiness": "MEASURED_DIRECTIONAL_STRENGTH_NOT_WIRED"},
    }


def compose_snapshot(*, technical=None, candle=None, news=None, futures=None, options=None):
    """Merge separately sourced engines without treating one as another."""
    provided = dict(technical=technical, candle=candle, news=news,
                    futures=futures, options=options)
    rows = tuple(provided[name] if provided[name] is not None else
                 EngineEvidence(name, reason="Verified "+name+" evidence unavailable")
                 for name in ENGINE_NAMES)
    if any(not isinstance(row, EngineEvidence) or row.name != name
           for name, row in zip(ENGINE_NAMES, rows)):
        raise ValueError("Evidence must be typed and match its engine slot")
    return {"engines": rows, "combined": combine_evidence(rows)}


def snapshot_for_display(snapshot, *, now, max_age_seconds=300, expected_source="Dhan"):
    """Apply a render-time freshness gate to cached five-engine evidence.

    A snapshot from a previous scan/session is never promoted to a current
    signal merely because its saved verified flag was once true.
    """
    if type(now) not in (int, float) or not isfinite(now) or now <= 0:
        raise ValueError("Invalid current time")
    if type(max_age_seconds) not in (int, float) or not isfinite(max_age_seconds) or max_age_seconds <= 0:
        raise ValueError("Invalid freshness limit")
    if not isinstance(expected_source, str) or not expected_source.strip():
        raise ValueError("Invalid expected source")
    if not isinstance(snapshot, dict) or not isinstance(snapshot.get("engines"), (tuple, list)):
        return compose_snapshot()
    rows = snapshot["engines"]
    if len(rows) != len(ENGINE_NAMES) or any(not isinstance(e, EngineEvidence) or e.name != n
                                              for e, n in zip(rows, ENGINE_NAMES)):
        return compose_snapshot()
    gated = tuple(e if e.eligible and e.source == expected_source and e.timestamp is not None and
                  0 <= now - e.timestamp <= max_age_seconds
                  else EngineEvidence(e.name, reason="Cached evidence stale, source mismatch or timestamp unavailable")
                  for e in rows)
    return {"engines": gated, "combined": combine_evidence(gated)}


def compose_verified_adapter_snapshot(scan_result, *, candle=None, news=None,
                                      futures=None, options=None, now=None,
                                      max_age_seconds=300):
    """Join five independent typed adapters, then gate every vote at render time.

    Missing sources remain WAIT; no simulated news, OI or PCR strength.
    This function makes the data contract usable by a real publisher without
    letting scanner technical votes masquerade as candle/news evidence.
    """
    technical=scanner_snapshot(scan_result)["engines"][0]
    rows={"technical":technical}
    for name, supplied in (("candle",candle),("news",news),
                           ("futures",futures),("options",options)):
        if isinstance(supplied, EngineEvidence) and supplied.name==name:
            rows[name]=supplied
        elif name=="futures":
            rows[name]=futures_from_component(supplied)
        elif name=="options":
            rows[name]=option_from_component(supplied)
        else:
            rows[name]=EngineEvidence(name,reason="Independent verified "+name+" adapter unavailable")
    snapshot=compose_snapshot(**rows)
    if now is None:
        return snapshot
    return snapshot_for_display(snapshot,now=now,max_age_seconds=max_age_seconds)


def scanner_snapshot(scan_result):
    """Adapt existing scanner votes without network calls or false live labels.

    Candle and technical votes originate from the same scanner calculation;
    expose only the technical slot to avoid correlated double counting.
    Independent price-action evidence requires its own validated algorithm.
    """
    if not isinstance(scan_result, dict):
        return compose_snapshot()
    raw = scan_result.get("votes") or []
    if not isinstance(raw, (list, tuple)):
        return compose_snapshot()
    from scanner_engine import OPTION_FILTERS
    from filter_wiring_audit import CANDLE_FILTERS
    technical_names={name.casefold() for name in CANDLE_FILTERS}
    # Match context identities using the same normalization as duplicate detection.
    # Legacy Max Pain is context-only too, never a technical vote.
    context_names={name.casefold() for name in OPTION_FILTERS}|{"news headlines","max pain"}
    labels = []
    seen_filters = set()
    for vote in raw:
        if not isinstance(vote, dict):
            return compose_snapshot()
        name = vote.get("name")
        if not isinstance(name, str) or not name.strip():
            return compose_snapshot()
        canonical_name = name.strip().casefold()
        if canonical_name in seen_filters:
            return compose_snapshot()
        seen_filters.add(canonical_name)
        # Option OI/max-pain and RSS news are independent CONTEXT sources,
        # never extra technical votes even if an upstream row is malformed
        # or accidentally carries a directional integer.
        if canonical_name in context_names:
            continue
        # Only configured candle indicators may supply technical evidence.
        # Unknown or stale plugin labels must not satisfy directional quorum.
        if canonical_name not in technical_names:
            return compose_snapshot()
        direction = vote.get("vote")
        if direction is None:
            # An unavailable filter is not a malformed filter. Retain valid
            # technical evidence while never converting an OI/news/volume
            # data gap into a bullish, bearish or neutral confirmation.
            unavailable = {"OI Support", "OI Resistance", "OI Profile",
                           "Dhan Max Pain", "News Headlines", "VWAP", "Volume"}
            # Context enrichment can replace the literal WAIT text with
            # Dhan expiry/OI details. Only an explicitly known data-dependent
            # filter may remain unavailable; never infer its direction.
            if canonical_name not in {item.casefold() for item in unavailable}:
                return compose_snapshot()
            continue
        if type(direction) is not int or direction not in (-1, 0, 1):
            return compose_snapshot()
        if direction == 1:
            labels.append("BUY")
        elif direction == -1:
            labels.append("SELL")
    source = scan_result.get("source") or ""
    # No directional vote is evidence when the completed-candle analysis
    # itself has no valid timestamp, regardless of a broker status flag.
    timestamp = scan_result.get("timestamp")
    if type(timestamp) not in (int, float) or not isfinite(timestamp) or timestamp <= 0:
        return compose_snapshot()
    verified = (scan_result.get("live_verified") is True and
                scan_result.get("freshness") in ("verified_live", "live_verified") and
                scan_result.get("historical") is False and source == "Dhan")
    technical = technical_from_votes(labels, verified=verified,
                                      timestamp=timestamp, source=source)
    return compose_snapshot(technical=technical)


def historical_candle_balance(bars, *, sample_size=8):
    """Body-only historical candle direction; never eligible for live engine votes."""
    if type(sample_size) is not int or not 5 <= sample_size <= 20:
        raise ValueError("Invalid historical candle sample")
    if not isinstance(bars, (list, tuple)) or len(bars) < sample_size:
        return None
    bulls = bears = 0
    previous = None
    for candle in bars[-sample_size:]:
        if not isinstance(candle, (list, tuple)) or len(candle) < 5:
            return None
        ts, op, high, low, close = candle[:5]
        if (any(type(x) not in (int, float) or not isfinite(x) or x <= 0
                for x in (ts, op, high, low, close))
                or (previous is not None and ts <= previous)
                or high < max(op, close) or low > min(op, close)):
            return None
        previous = ts
        bulls += close > op
        bears += close < op
    directional = bulls + bears
    if directional < 5:
        return None
    bullish = round(bulls * 100 / directional)
    return {"bullish": bullish, "bearish": 100 - bullish,
            "historical": True, "verified": False, "count": directional}



def completed_timeframe_candle_balance(history, timeframe, *, now):
    """Read-only HIST context for an exact Dhan timeframe and completed bars.

    Never turn the currently forming candle into a vote or relabel 5m as 1m/3m.
    The validated result is display-only, NOT independent/live engine evidence.
    """
    if timeframe not in ("1m", "3m", "5m") or not isinstance(history, dict):
        return None
    if (history.get("source") != "Dhan" or
            history.get("_scanner_timeframe", "5m") != timeframe):
        return None
    if type(now) not in (int, float) or not isfinite(now) or now <= 0:
        return None
    seconds={"1m":60, "3m":180, "5m":300}[timeframe]
    bars=history.get("bars")
    if not isinstance(bars, (list, tuple)) or len(bars) < 8:
        return None
    # HIST-only recovery from a provable after-close suffix.
    # Raw history remains unchanged; any interior gap still fails closed.
    try:
        bars=historical_regular_session_bars(bars,timeframe)
    except (ValueError, OverflowError, OSError):
        return None
    # Only the newest forming bar may be excluded; do not silently skip
    # malformed interior candles and manufacture a clean-looking sample.
    last=bars[-1]
    if (not isinstance(last, (list, tuple)) or len(last) < 6 or
            type(last[0]) not in (int, float) or not isfinite(last[0])):
        return None
    forming=last[0]+seconds > now
    if forming:
        # Exclude only the legitimate current interval. A future-dated or
        # jumped final timestamp is invalid, not a forming candle to skip.
        if (len(bars)<9 or last[0]>now or
                not isinstance(bars[-2], (list, tuple)) or
                len(bars[-2])<6 or type(bars[-2][0]) not in (int,float)
                or not isfinite(bars[-2][0]) or
                last[0]-bars[-2][0]!=seconds):
            return None
    completed=bars[:-1] if forming else bars
    if len(completed) < 8:
        return None
    sample=completed[-8:]
    for index, bar in enumerate(sample):
        if (not isinstance(bar, (list, tuple)) or len(bar) < 6 or
                any(type(v) not in (int,float) or not isfinite(v)
                    for v in bar[:6])
                or min(bar[:5])<=0 or bar[5]<0
                or bar[2]<max(bar[1],bar[4])
                or bar[3]>min(bar[1],bar[4]) or bar[3]>bar[2]
                or bar[0]+seconds>now):
            return None
        if index and bar[0]-sample[index-1][0] != seconds:
            return None
    return historical_candle_balance(sample)


def verified_candle_evidence(history, timeframe, *, now, symbol):
    """Independent completed OHLC body direction, not technical filter votes."""
    wait = EngineEvidence("candle", reason="Exact-frame verified Dhan candles required")
    if (not isinstance(history, dict) or timeframe not in ("1m", "3m", "5m")
            or history.get("source") != "Dhan"
            or history.get("symbol") != symbol
            or history.get("_scanner_timeframe") != timeframe
            or history.get("live_verified") is not True
            or history.get("historical") is not False
            or history.get("cached")
            or history.get("freshness") not in ("verified_live", "live_verified")
            or type(now) not in (int, float) or not isfinite(now)):
        return wait
    bars = history.get("bars")
    if not isinstance(bars, (list, tuple)) or not bars:
        return wait
    seconds = {"1m": 60, "3m": 180, "5m": 300}[timeframe]
    # LIVE evidence must not use a HIST-only trimmed session suffix.
    # The exact bars used for direction and the revision timestamp must match.
    try:
        if historical_regular_session_bars(bars, timeframe) is not bars:
            return wait
    except (ValueError, OverflowError, OSError):
        return wait
    balance = completed_timeframe_candle_balance(history, timeframe, now=now)
    if balance is None:
        return wait
    last = bars[-1][0]
    stamp = bars[-2][0] if last + seconds > now else last
    if not 0 <= now - (stamp + seconds) <= seconds:
        return wait
    return EngineEvidence("candle", balance["bullish"], balance["bearish"],
                          verified=True, timestamp=stamp + seconds, source="Dhan",
                          reason="Completed OHLC body direction; not technical votes or win probability")


def scanner_snapshot_with_candle(scan_result, history, *, symbol, timeframe, now, timing=None):
    """Join same-symbol/frame independently verified raw candles and T votes."""
    from time import perf_counter
    began=perf_counter()
    # Reject the entire technical lane if its identity does not match the
    # requested context; rejecting only C would still leak a cross-frame T vote.
    matches = (isinstance(scan_result, dict) and isinstance(symbol, str)
               and bool(symbol.strip()) and timeframe in ("1m", "3m", "5m")
               and scan_result.get("symbol") == symbol
               and scan_result.get("timeframe") == timeframe)
    technical = (scanner_snapshot(scan_result)["engines"][0] if matches else
                 EngineEvidence("technical", reason="Matching symbol/timeframe required"))
    technical_ms=(perf_counter()-began)*1000
    began=perf_counter()
    candle = EngineEvidence("candle", reason="Matching verified analysis revision required")
    candle_checked=False
    if (technical.eligible and scan_result.get("symbol") == symbol
            and scan_result.get("timeframe") == timeframe):
        candle_checked=True
        candidate = verified_candle_evidence(history, timeframe, now=now, symbol=symbol)
        seconds = {"1m": 60, "3m": 180, "5m": 300}.get(timeframe)
        if candidate.eligible and technical.timestamp == candidate.timestamp - seconds:
            candle = candidate
    candle_ms=(perf_counter()-began)*1000
    began=perf_counter()
    snapshot=compose_snapshot(technical=technical, candle=candle)
    if timing is not None:
        timing.update(technical_adapter_ms=round(technical_ms,3),
                      candle_adapter_ms=round(candle_ms,3) if candle_checked else None,
                      compose_vote_ms=round((perf_counter()-began)*1000,3),
                      candle_checked=candle_checked,
                      news_adapter_ms=None,futures_adapter_ms=None,options_adapter_ms=None)
    return snapshot


def selected_verified_frame_snapshot(result, history, *, symbol, timeframe, now):
    """Selected 1m/3m publisher: no inferred identity, no HIST promotion.

    The selected scanner supplies its own analysis revision; authenticated
    exact-frame history must independently qualify before any T/C vote.
    """
    if (timeframe not in ("1m","3m") or not isinstance(result,dict)
            or not isinstance(history,dict) or history.get("symbol")!=symbol
            or history.get("_scanner_timeframe")!=timeframe
            or history.get("source")!="Dhan" or history.get("cached")
            or history.get("live_verified") is not True
            or history.get("historical") is not False
            or history.get("freshness") not in ("exchange_verified","verified_live","live_verified")):
        return None
    if (result.get("symbol",symbol)!=symbol
            or result.get("timeframe",timeframe)!=timeframe
            or result.get("historical") is True
            or result.get("live_verified") is False):
        return None
    normalized=dict(history,freshness="verified_live")
    candle=verified_candle_evidence(normalized,timeframe,now=now,symbol=symbol)
    seconds={"1m":60,"3m":180}[timeframe]
    if not candle.eligible or result.get("timestamp")!=candle.timestamp-seconds:
        return None
    scan=dict(result,symbol=symbol,timeframe=timeframe,source="Dhan",
              historical=False,live_verified=True,freshness="verified_live")
    return scanner_snapshot_with_candle(scan,normalized,symbol=symbol,
                                        timeframe=timeframe,now=now)

def measured_directional_evidence(name, component, *, required_basis):
    """Accept only measured, authenticated Dhan directional percentages.

    Context such as OI, PCR, headline counts and inferred build-up never votes.
    """
    if not isinstance(component, dict):
        return EngineEvidence(name, reason="Measured Dhan directional evidence unavailable")
    if (component.get("source") != "Dhan" or component.get("verified") is not True
            or component.get("direction_basis") != required_basis
            or component.get("historical") is True
            or component.get("live_verified") is False
            or not isinstance(component.get("contract"), str)
            or not component["contract"].strip()):
        return EngineEvidence(name, reason="Verified Dhan directional provenance unavailable")
    bull, bear = component.get("bullish"), component.get("bearish")
    timestamp = component.get("timestamp")
    if (type(bull) is not int or type(bear) is not int or
            not 0 <= bull <= 100 or bull + bear != 100 or
            type(timestamp) not in (int, float) or not isfinite(timestamp) or timestamp <= 0):
        return EngineEvidence(name, reason="Measured directional strength or timestamp unavailable")
    return EngineEvidence(name, bull, bear, verified=True, timestamp=timestamp,
                          source="Dhan", reason="Measured authenticated Dhan directional strength")


def option_from_component(component):
    """Adapt authenticated directional option flow; OI/volume alone never votes.

    Existing app option snapshots are empty until a real broker adapter is wired.
    Even a reported BULLISH/BEARISH bias needs validated trade flow and Dhan
    provenance; a generic option-chain PCR is not directional trade flow.
    """
    if not isinstance(component, dict):
        return EngineEvidence("options", reason="Verified Dhan option flow unavailable")
    if (component.get("available") is not True or
            component.get("source") != "Dhan" or
            component.get("direction_basis") != "validated_trade_flow" or
            component.get("verified") is not True or
            component.get("bias") not in ("BULLISH", "BEARISH")):
        return EngineEvidence("options", reason="Validated Dhan option trade flow unavailable")
    timestamp = component.get("timestamp")
    if type(timestamp) not in (int, float) or not isfinite(timestamp) or timestamp <= 0:
        return EngineEvidence("options", reason="Option flow timestamp unavailable")
    # A supplied expiry must name a canonical non-expired contract relative
    # to this measured evidence, not a date parsed from phone wall-clock time.
    expiry=component.get("expiry")
    if expiry is not None:
        from datetime import date, datetime, timezone, timedelta
        try:
            expiry_day=date.fromisoformat(expiry)
            measured_day=datetime.fromtimestamp(
                timestamp,timezone(timedelta(hours=5,minutes=30))).date()
            if type(expiry) is not str or expiry_day.isoformat()!=expiry or expiry_day<measured_day:
                raise ValueError("Expired or noncanonical option contract")
        except (TypeError, ValueError, OverflowError, OSError):
            return EngineEvidence("options", reason="Option contract expiry invalid or expired")
    # A supplied BULLISH/BEARISH label may not contradict the independently
    # measured trade-side strengths; otherwise it could mislead the 3/5 vote.
    measured = measured_directional_evidence(
        "options", component, required_basis="validated_trade_flow")
    if measured.eligible and (
            (component["bias"]=="BULLISH" and measured.bullish<=measured.bearish)
            or (component["bias"]=="BEARISH" and measured.bearish<=measured.bullish)):
        return EngineEvidence("options", reason="Option flow bias conflicts with measured direction")
    return measured


def news_from_headline_cues(cues):
    """RSS phrase matches are unverified context, not independent market evidence.

    Keep the count for diagnostics elsewhere; neither headline count nor a
    POSITIVE/NEGATIVE keyword classification is a measured directional ratio.
    """
    if not isinstance(cues, dict):
        return EngineEvidence("news", reason="News headlines unavailable")
    if cues.get("bias") in ("POSITIVE", "NEGATIVE", "MIXED", "UNCLASSIFIED"):
        return EngineEvidence("news", reason="Experimental headline cues; impact unverified")
    return EngineEvidence("news", reason="Verified news evidence unavailable")


def futures_from_component(component):
    """Fail-closed futures adapter: OI/price/volume are context, not traded-side proof.

    A broker-reported futures build-up is an inference, not independently
    measured bullish/bearish percentages. Do not turn it into a fusion vote.
    """
    if not isinstance(component, dict):
        return EngineEvidence("futures", reason="Verified Dhan futures contract unavailable")
    if component.get("source") != "Dhan" or component.get("verified") is not True:
        return EngineEvidence("futures", reason="Dhan futures provenance unverified")
    if not isinstance(component.get("contract"), str) or not component["contract"].strip():
        return EngineEvidence("futures", reason="Mapped futures contract unavailable")
    timestamp = component.get("timestamp")
    if type(timestamp) not in (int, float) or not isfinite(timestamp) or timestamp <= 0:
        return EngineEvidence("futures", reason="Futures timestamp unavailable")
    if component.get("direction_basis") != "validated_trade_flow":
        return EngineEvidence("futures", reason="Futures OI/price build-up is inferred, not validated directional flow")
    return measured_directional_evidence(
        "futures", component, required_basis="validated_trade_flow")


def deduplicate_news_context(headlines, *, symbol, now, max_age_seconds=600):
    """Return bounded, instrument-tagged headline context; never a market vote.

    Headlines require explicit symbol tagging, publisher and publication time.
    Deduplication prevents repeated syndicated titles inflating coverage.
    """
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Symbol required")
    if type(now) not in (int, float) or not isfinite(now) or now <= 0:
        raise ValueError("Invalid current time")
    if type(max_age_seconds) not in (int, float) or not isfinite(max_age_seconds) or max_age_seconds <= 0:
        raise ValueError("Invalid news freshness limit")
    if not isinstance(headlines, (list, tuple)):
        return ()
    selected, seen = [], set()
    target = symbol.strip().casefold()
    for item in headlines:
        if not isinstance(item, dict):
            continue
        title, publisher, published = item.get("title"), item.get("publisher"), item.get("published_at")
        tags = item.get("symbols")
        if (not isinstance(title, str) or not title.strip() or
                not isinstance(publisher, str) or not publisher.strip() or
                type(published) not in (int, float) or not isfinite(published) or
                not 0 <= now - published <= max_age_seconds or
                not isinstance(tags, (list, tuple)) or
                target not in {tag.strip().casefold() for tag in tags if isinstance(tag, str)}):
            continue
        # Syndicated copies of the same headline count once, regardless of publisher.
        key = " ".join(title.split()).casefold()
        if key in seen:
            continue
        seen.add(key)
        selected.append({"title": title.strip(), "publisher": publisher.strip(),
                         "published_at": published})
        if len(selected) >= 20:
            break
    return tuple(selected)


def futures_market_context(component, *, now, max_age_seconds=300):
    """Validate read-only Dhan futures fields; never infer cash flow or trade side.

    Contract mapping must be supplied by a separately verified broker resolver.
    This normalizer cannot establish such a mapping or promote data to a vote.
    """
    if type(now) not in (int, float) or not isfinite(now) or now <= 0:
        raise ValueError("Invalid current time")
    if type(max_age_seconds) not in (int, float) or not isfinite(max_age_seconds) or max_age_seconds <= 0:
        raise ValueError("Invalid freshness limit")
    if not isinstance(component, dict) or component.get("source") != "Dhan" or component.get("verified") is not True:
        return None
    if component.get("mapping_verified") is not True:
        return None
    contract = component.get("contract")
    timestamp = component.get("timestamp")
    if (not isinstance(contract, str) or not contract.strip() or
            type(timestamp) not in (int, float) or not isfinite(timestamp) or
            not 0 <= now - timestamp <= max_age_seconds):
        return None
    fields = ("ltp", "open_interest", "volume")
    values = [component.get(k) for k in fields]
    if any(type(v) not in (int, float) or not isfinite(v) or v < 0 for v in values) or values[0] <= 0:
        return None
    return {"contract": contract.strip(), "timestamp": timestamp,
            "ltp": values[0], "open_interest": values[1], "volume": values[2],
            "source": "Dhan", "direction": None, "direction_verified": False}


def resolve_verified_futures_contract(rows, *, symbol, expiry):
    """Resolve exactly one broker-master futures contract; no symbol guesses.

    Only normalized records from an authenticated, verified Dhan instrument
    master are eligible. Ambiguity fails closed, including duplicate IDs.
    """
    from datetime import date
    if not isinstance(symbol, str) or not symbol.strip():
        raise ValueError("Underlying symbol required")
    if not isinstance(expiry, date) or isinstance(expiry, __import__("datetime").datetime):
        raise ValueError("Contract expiry must be a date")
    if not isinstance(rows, (list, tuple)):
        return None
    matches = []
    for row in rows:
        if not isinstance(row, dict) or row.get("source") != "Dhan" or row.get("master_verified") is not True:
            continue
        if row.get("instrument_type") != "FUT" or row.get("exchange_segment") != "NSE_FNO":
            continue
        underlying = row.get("underlying")
        if not isinstance(underlying, str) or underlying.strip().casefold() != symbol.strip().casefold():
            continue
        if row.get("expiry") != expiry.isoformat():
            continue
        sid = row.get("security_id")
        contract = row.get("contract")
        if (not isinstance(sid, str) or not sid.isascii() or not sid.isdecimal() or
                int(sid) <= 0 or not isinstance(contract, str) or not contract.strip()):
            return None
        matches.append({"source": "Dhan", "exchange_segment": "NSE_FNO",
                        "security_id": sid, "contract": contract.strip(),
                        "underlying": symbol.strip().upper(), "expiry": expiry.isoformat(),
                        "mapping_verified": True})
        if len(matches) > 1:
            return None
    return matches[0] if len(matches) == 1 else None


def option_chain_display_context(metrics):
    """Attach Dhan option-chain context to a UI snapshot, never an engine vote.

    This is intentionally separate from compose_snapshot's five voting slots.
    An unverified chain cannot prove direction, market freshness or trade flow.
    """
    if not isinstance(metrics, dict) or metrics.get("source") != "dhan":
        return {"available": False, "reason": "Dhan option context unavailable"}
    if metrics.get("freshness") != "unverified" or metrics.get("signal_eligible") is not False:
        return {"available": False, "reason": "Unsupported option freshness or eligibility"}
    window = metrics.get("atm_window")
    rows = window.get("rows") if isinstance(window, dict) else None
    if (not isinstance(window, dict) or window.get("source") != "dhan"
            or window.get("freshness") != "unverified"
            or window.get("signal_eligible") is not False
            or not isinstance(rows, (list, tuple)) or len(rows) != 7):
        return {"available": False, "reason": "Seven listed Dhan strikes unavailable"}
    result = []
    for row in rows:
        if not isinstance(row, dict):
            return {"available": False, "reason": "Invalid option strike row"}
        strike = row.get("strike")
        if type(strike) not in (int, float) or not isfinite(strike) or strike <= 0:
            return {"available": False, "reason": "Invalid option strike"}
        legs = {}
        for side in ("ce", "pe"):
            leg = row.get(side)
            if not isinstance(leg, dict):
                return {"available": False, "reason": "Missing option leg"}
            values = {}
            for field in ("oi", "volume", "last_price", "previous_oi"):
                value = leg.get(field)
                if field == "oi" or value is not None:
                    if type(value) not in (int, float) or not isfinite(value) or value < 0:
                        return {"available": False, "reason": "Invalid option leg value"}
                    values[field] = float(value)
            legs[side] = values
        result.append({"strike": float(strike), **legs})
    strikes = [row["strike"] for row in result]
    if strikes != sorted(set(strikes)) or window.get("atm") != strikes[3]:
        return {"available": False, "reason": "Invalid ATM strike ordering"}
    return {"available": True, "source": "Dhan", "atm": strikes[3],
            "rows": tuple(result), "freshness": "unverified",
            "signal_eligible": False, "direction": "WAIT"}


def compose_snapshot_with_option_context(*, option_metrics=None, technical=None,
                                         candle=None, news=None, futures=None,
                                         options=None):
    """Combine evidence while keeping broker option-chain rows display-only.

    The optional option-chain payload cannot overwrite any engine slot or
    upgrade an unverified context into a directional signal.
    """
    snapshot = compose_snapshot(technical=technical, candle=candle, news=news,
                                futures=futures, options=options)
    return {**snapshot, "option_context": option_chain_display_context(option_metrics)}


class ContextualFiveEngineCache:
    """Read-only evidence store keyed by symbol, timeframe and provider generation.

    No provider I/O. A change of scanner timeframe or login generation cannot
    reuse another snapshot. Actual live eligibility remains a separate
    freshness, market-session and source check at read time.
    """

    def __init__(self):
        self._snapshots = {}

    @staticmethod
    def _key(symbol, timeframe, generation):
        if (not isinstance(symbol, str) or not symbol.strip() or
                timeframe not in ("1m", "2m", "3m", "5m") or
                type(generation) is not int or generation < 0):
            raise ValueError("Explicit symbol, supported timeframe and generation required")
        return (symbol.strip().upper(), timeframe, generation)

    def publish(self, *, symbol, timeframe, generation, snapshot):
        key = self._key(symbol, timeframe, generation)
        if (not isinstance(snapshot, dict) or
                not isinstance(snapshot.get("engines"), (tuple, list)) or
                len(snapshot["engines"]) != len(ENGINE_NAMES) or
                any(not isinstance(e, EngineEvidence) or e.name != name
                    for e, name in zip(snapshot["engines"], ENGINE_NAMES))):
            raise ValueError("Canonical five-engine snapshot required")
        # Detach caller-owned mutable engine lists and recompute the aggregate
        # from the canonical evidence rather than trusting a supplied summary.
        rows = tuple(snapshot["engines"])
        self._snapshots[key] = {**snapshot, "engines": rows,
                                "combined": combine_evidence(rows)}

    def peek(self, *, symbol, timeframe, generation):
        """Read cached evidence before LIVE/session gating; never certify it."""
        return self._snapshots.get(self._key(symbol, timeframe, generation))

    def read(self, *, symbol, timeframe, generation, now, connected,
             market_open, expected_source="Dhan", max_age_seconds=300):
        key = self._key(symbol, timeframe, generation)
        if connected is not True or market_open is not True:
            return compose_snapshot()
        return snapshot_for_display(
            self._snapshots.get(key), now=now,
            max_age_seconds=max_age_seconds, expected_source=expected_source)

    def clear(self):
        self._snapshots.clear()

    def __len__(self):
        return len(self._snapshots)
