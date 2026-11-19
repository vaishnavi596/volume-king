"""FT-3 app-only option evidence → directional filter gate; no signal generator.

The upstream factor producer must independently authenticate transport and
compute directional evidence. PCR/Max Pain alone do not imply a direction.
"""
from filter_evidence import FilterEvidenceError
from option_evidence import OptionEvidenceError

OPTION_FACTORS = frozenset(("oi_support", "oi_resistance", "max_pain", "pcr"))


def accept_option_factors(filters, options, expiries, symbol, timeframe,
                          revision, factors, *, selected_equities=(),
                          trusted_transport=False):
    """Only attach separately computed factors to matching expiry/observation.

    Rejecting this update keeps last-good option metrics and earlier filters
    untouched. The selected expiry must be a trusted available roster member.
    """
    if (trusted_transport is not True or type(factors) is not dict
            or not factors or not set(factors).issubset(OPTION_FACTORS)
            or type(symbol) is not str or type(timeframe) is not str
            or timeframe not in ("1m", "3m", "5m", "15m", "30m")
            or type(revision) is not int or revision < 0):
        raise FilterEvidenceError("Untrusted or unsupported option factor update")
    selected = expiries.selected(symbol, selected_equities=selected_equities)
    if selected is None:
        raise OptionEvidenceError("No trusted selected option expiry")
    metrics = options.visible(symbol, selected, selected_equities=selected_equities)
    if (metrics.get("status") != "HIST"
            or metrics.get("source") != "dhan"
            or metrics.get("eligible") is not True):
        raise OptionEvidenceError("Matching eligible option metrics unavailable")
    # An option score must belong to the exact accepted option observation;
    # no stale or cross-expiry mix, and no direction inferred from PCR.
    observed = metrics["observed_at"]
    for evidence in factors.values():
        if (type(evidence) is not dict
                or type(evidence.get("observed_at")) is not int
                or evidence["observed_at"] != observed):
            raise FilterEvidenceError("Option filter observation mismatch")
    allowed = ("NIFTY", "BANKNIFTY", "SENSEX") + tuple(selected_equities)
    return filters.accept_available(
        symbol, timeframe, revision, factors,
        allowed_symbols=allowed, trusted_transport=True)



def select_option_expiry(filters, expiries, symbol, expiry, *,
                         selected_equities=()):
    """App-owned expiry choice; invalidate option factors only after success."""
    previous = expiries.selected(symbol, selected_equities=selected_equities)
    # Choose first: an unverified expiry must not erase accepted last-good.
    expiries.choose(symbol, expiry, selected_equities=selected_equities)
    if previous != expiry:
        filters.invalidate_option_factors(symbol)
    return previous != expiry


def accept_expiry_roster(filters, expiries, symbol, revision, available, *,
                         allowed_symbols, selected_equities=(),
                         trusted_transport=False):
    """When a new trusted roster removes the selected expiry, retire its signals."""
    previous = expiries.selected(symbol, selected_equities=selected_equities)
    updated = expiries.accept(
        symbol, revision, available, allowed_symbols=allowed_symbols,
        trusted_transport=trusted_transport)
    if updated and previous != expiries.selected(symbol, selected_equities=selected_equities):
        filters.invalidate_option_factors(symbol)
    return updated


def accept_option_metrics(filters, options, expiries, payload, *,
                          selected_equities=(), trusted_transport=False):
    """Accept a normalized option observation; retire stale *directional* factors.

    A new revision with identical metrics is harmless. A changed observation,
    PCR, OI or max pain for the currently selected expiry invalidates all
    option-derived factors, but not an independently validated candle trend.
    Validation/revision rejection must happen before any invalidation.
    """
    if trusted_transport is not True or type(payload) is not dict:
        raise OptionEvidenceError("Authenticated normalized option evidence required")
    symbol = payload.get("symbol")
    expiry = payload.get("expiry")
    # Read previous validated evidence without trusting incoming symbol/expiry.
    previous = options.visible(symbol, expiry, selected_equities=selected_equities)
    selected = expiries.selected(symbol, selected_equities=selected_equities)
    updated = options.accept(
        payload, selected_equities=selected_equities, trusted_transport=True)
    if not updated:
        return False
    current = options.visible(symbol, expiry, selected_equities=selected_equities)
    fields = ("observed_at", "ce_oi", "pe_oi", "pcr", "max_pain")
    if (selected == expiry and current.get("status") == "HIST"
            and (previous.get("status") != "HIST"
                 or any(previous.get(name) != current.get(name) for name in fields))):
        filters.invalidate_option_factors(symbol)
    return True
