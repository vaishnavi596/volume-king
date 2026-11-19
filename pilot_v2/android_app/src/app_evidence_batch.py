"""V2 offline atomic source-evidence batch staging; no network or auth issuer.

Only the independently authenticated delivery adapter may pass
trusted_transport=True. This boolean does not prove login by itself.
Existing per-lane validators are run against a deep copy; any failed event
leaves every live cache untouched, including expiry-dependent factor resets.
"""
from copy import deepcopy
from evidence_inbox import DeviceEvidenceInbox

EVENT_FIELDS = {
    "candles": frozenset(("kind", "symbol", "timeframe", "revision", "bars")),
    "candle_trend": frozenset(("kind", "symbol", "timeframe", "revision", "evidence")),
    "expiries": frozenset(("kind", "symbol", "revision", "available")),
    "options": frozenset(("kind", "payload")),
    "strikes": frozenset(("kind", "payload")),
    "listed_window": frozenset(("kind", "symbol", "expiry", "revision",
                                  "observed_at", "spot", "listed_rows")),
    "option_factors": frozenset(("kind", "symbol", "timeframe", "revision",
                                  "evidence")),
}
CACHE_FIELDS = (
    ("candles", "_entries"),
    ("filters", "_values"),
    ("options", "_rows"),
    ("expiries", "_available"),
    ("expiries", "_selected"),
    ("strikes", "_cache"),
)


class EvidenceBatchError(ValueError):
    pass


def apply_staged_evidence_batch(inbox, events, *, selected_equities=(),
                                trusted_transport=False):
    """Apply independently validated ordered events atomically to existing inbox.

    Valid order: completed candles and expiry roster before their dependent
    trend/options/factors. Expiry selection remains a separate user action.
    This is a local helper, never an HTTP route or live-feed producer.
    """
    if not isinstance(inbox, DeviceEvidenceInbox) or trusted_transport is not True:
        raise EvidenceBatchError("Authenticated evidence delivery caller required")
    allowed = inbox.allowed(selected_equities)
    if (type(events) is not list or not 1 <= len(events) <= 32):
        raise EvidenceBatchError("Invalid bounded evidence batch")
    staged = deepcopy(inbox)
    outcomes = []
    for event in events:
        if (type(event) is not dict or
                type(event.get("kind")) is not str or
                event["kind"] not in EVENT_FIELDS or
                set(event) != EVENT_FIELDS[event["kind"]]):
            raise EvidenceBatchError("Unknown or malformed evidence event")
        kind = event["kind"]
        if kind in ("options", "strikes"):
            payload = event["payload"]
            if type(payload) is not dict or payload.get("symbol") not in allowed:
                raise EvidenceBatchError("Evidence symbol outside selected roster")
        else:
            if event["symbol"] not in allowed:
                raise EvidenceBatchError("Evidence symbol outside selected roster")
        common = {"selected_equities": selected_equities, "trusted_transport": True}
        if kind == "candles":
            result = staged.apply_candles(
                event["symbol"], event["timeframe"], event["revision"],
                event["bars"], **common)
        elif kind == "candle_trend":
            result = staged.apply_candle_trend(
                event["symbol"], event["timeframe"], event["revision"],
                event["evidence"], **common)
        elif kind == "expiries":
            result = staged.apply_expiries(
                event["symbol"], event["revision"], event["available"],
                **common)
        elif kind == "options":
            result = staged.apply_options(event["payload"], **common)
        elif kind == "strikes":
            result = staged.apply_option_strikes(event["payload"], **common)
        elif kind == "listed_window":
            result = staged.apply_listed_option_window(
                symbol=event["symbol"], expiry=event["expiry"],
                revision=event["revision"],
                observed_at=event["observed_at"], spot=event["spot"],
                listed_rows=event["listed_rows"], **common)
        else:
            result = staged.apply_option_factors(
                event["symbol"], event["timeframe"], event["revision"],
                event["evidence"], **common)
        outcomes.append(bool(result))
    # Reuse the original cache holders: existing Flet UI and scanner references
    # must never become detached by swapping out evidence_inbox.candles, etc.
    for name, field in CACHE_FIELDS:
        setattr(getattr(inbox, name), field,
                deepcopy(getattr(getattr(staged, name), field)))
    return {"events": len(events), "updated": sum(outcomes),
            "status": "HIST_UNVERIFIED", "live_verified": False}
