"""V2 Android read-only HTTP response adapter, offline and not a network client.

The caller must independently verify a trusted HTTPS origin and the current
revocable device session. A boolean attestation is not authentication.
"""
from feed_inbox import DeviceFeedInbox, FeedError


def deliver_readonly_response(inbox, feed, status_code, payload, *, 
                              selected_equities=(), authenticated_session=False):
    """Fail closed on HTTP/auth/context errors; retain previous visible prices."""
    if not isinstance(inbox, DeviceFeedInbox):
        raise FeedError("Invalid app feed destination")
    if (authenticated_session is not True or type(status_code) is not int
            or status_code != 200):
        raise FeedError("Authenticated successful read-only response required")
    if type(feed) is not str or feed not in ("quotes", "indices"):
        raise FeedError("Unsupported read-only response lane")
    # apply_feed validates the complete Dhan-only read schema, per-lane roster,
    # independent revision and last-good retention before mutating the view.
    return inbox.apply_feed(feed, payload, selected_equities)
