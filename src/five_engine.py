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
        direction = vote.get("vote")
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
    # A binary direction is not a measured percentage. Leave strength unavailable.
    return EngineEvidence("options", reason="Validated direction lacks measured bullish/bearish strength")


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
    return EngineEvidence("futures", reason="Validated futures flow lacks measured directional strength")


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
