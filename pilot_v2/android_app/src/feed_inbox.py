"""Offline FT-2: independent read-only equity/index revisions in the Flet app.

No sockets, credentials, server settings, Dhan token, or transport trust inferred.
The future authenticated HTTPS client must explicitly identify the authorized feed.
"""
from quote_view import DeviceQuoteView, FeedError, INDEXES, validate_readonly_snapshot


class DeviceFeedInbox:
    """One app-owned renderer with two isolated, validated provider feed lanes."""

    def __init__(self):
        self._equity = DeviceQuoteView()
        self._index = DeviceQuoteView()

    def revision_for(self, feed):
        if feed == "quotes":
            return self._equity.revision
        if feed == "indices":
            return self._index.revision
        raise FeedError("Unknown read-only feed")

    def apply_feed(self, feed, payload, selected_equities):
        if type(feed) is not str or feed not in ("quotes", "indices"):
            raise FeedError("Unknown read-only feed")
        equities = tuple(selected_equities)
        if (any(type(s) is not str or s in INDEXES for s in equities)
                or len(set(equities)) != len(equities)
                or len(equities) > 70):
            raise FeedError("Invalid app-owned equity roster")
        if feed == "quotes":
            # Equity-only endpoint must never inject index prices.
            validate_readonly_snapshot(payload, equities)
            return self._equity.apply(payload, equities)
        # Index-only endpoint must never inject unselected equity prices.
        validate_readonly_snapshot(payload, INDEXES)
        return self._index.apply(payload, ())

    def changed_for(self, feed):
        """Data-only UI invalidation hint; never initiates a fetch or redraw."""
        if feed == "quotes":
            return self._equity.last_changed
        if feed == "indices":
            return self._index.last_changed
        raise FeedError("Unknown read-only feed")

    def visible(self, symbol, selected_equities):
        if symbol in INDEXES:
            return self._index.visible(symbol, ())
        return self._equity.visible(symbol, selected_equities)

    def display(self, symbol, selected_equities):
        if symbol in INDEXES:
            return self._index.display(symbol, ())
        return self._equity.display(symbol, selected_equities)

    def forget_removed(self, selected_equities):
        self._equity.forget_removed(selected_equities)
        self._index.forget_removed(())
