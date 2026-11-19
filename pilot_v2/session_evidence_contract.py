"""V2 offline verified-session to Android evidence-cache integration contract.

This is a TEST/STAGING integration seam, not a deployed server endpoint or
proof that an Android client can authenticate itself. DeviceSessionGateway
is server-owned; it must authenticate and authorize every requested feed before
local delivery can mark transport trusted. No bearer/token is logged/stored.
"""
from .device_sessions import DeviceSessionGateway, SessionDenied

EVENT_PERMISSIONS = {
    "candles": ("candles",),
    "candle_trend": ("candles", "assessment"),
    "expiries": ("options",),
    "options": ("options",),
    "strikes": ("options",),
    "listed_window": ("options",),
    "option_factors": ("options", "assessment"),
}

class SessionEvidenceError(PermissionError):
    pass


def deliver_session_authorized_evidence(
        session_gateway, bearer, inbox, events, selected_equities, *,
        validated_batch_apply):
    """Check every required permission before calling atomic local consumer.

    validated_batch_apply is the existing app_evidence_batch helper injected by
    the integration test, not a new network producer. This gate does not grant
    Master role, device identity, or independent trust to any client.
    """
    if not isinstance(session_gateway, DeviceSessionGateway):
        raise SessionEvidenceError("Server-verified device session gateway required")
    if not callable(validated_batch_apply):
        raise SessionEvidenceError("Approved evidence consumer required")
    if type(events) is not list or not 1 <= len(events) <= 32:
        raise SessionEvidenceError("Invalid bounded evidence delivery")
    permissions = set()
    for item in events:
        if type(item) is not dict or type(item.get("kind")) is not str:
            raise SessionEvidenceError("Invalid evidence kind")
        feeds = EVENT_PERMISSIONS.get(item["kind"])
        if feeds is None:
            raise SessionEvidenceError("Unknown evidence kind")
        permissions.update(feeds)
    # The server must reject expiry, logout, revocation and missing grants.
    # Preflight *all* feeds to protect the all-or-nothing cache delivery.
    try:
        device = session_gateway.identity(bearer)
        for feed in sorted(permissions):
            if session_gateway.check_feed(bearer, feed) != device:
                raise SessionEvidenceError("Device identity changed")
    except (SessionDenied, TypeError, UnicodeError) as exc:
        raise SessionEvidenceError("Device session or feed permission denied") from None
    return validated_batch_apply(
        inbox, events, selected_equities=selected_equities,
        trusted_transport=True)
