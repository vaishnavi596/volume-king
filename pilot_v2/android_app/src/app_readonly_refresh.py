"""V2 app-side consented, read-only two-lane delivery orchestration.

Uses the already reviewed HTTPS reader and immutable refresh intent; never
creates a broker session, token, Dhan HTTP call, order, timer or new endpoint.
The actual Android app has no verified device login yet and DOES NOT invoke it.
"""
from feed_inbox import DeviceFeedInbox, FeedError, INDEXES
from refresh_intent import RefreshIntent
from secure_https_reader import V2ReadonlyHTTPSReader


def apply_approved_quote_intent(intent, reader, inbox, selected_equities):
    """Independent index and equity reads, preserving last-good data on errors.

    The trusted device login/bearer and origin must be established by the caller
    before constructing V2ReadonlyHTTPSReader. Never infer trust from this API.
    """
    if not isinstance(intent, RefreshIntent):
        raise FeedError("Valid app-owned refresh intent required")
    if not isinstance(reader, V2ReadonlyHTTPSReader):
        raise FeedError("Verified HTTPS reader required")
    if not isinstance(inbox, DeviceFeedInbox):
        raise FeedError("Approved app quote destination required")
    selected = tuple(selected_equities)
    if (len(selected) > 70
            or any(type(symbol) is not str or not symbol or symbol in INDEXES
                   for symbol in selected)
            or len(set(selected)) != len(selected)):
        raise FeedError("Invalid unique equity roster")
    if not intent.permitted:
        return {"status": "SKIPPED", "indexes": "SKIPPED",
                "quotes": "SKIPPED", "requests": 0}
    if (type(intent.permitted) is not bool
            or type(intent.reason) is not str
            or intent.reason not in ("MANUAL_DATA_REQUEST_ONLY", "AUTO_MARKET_CONFIRMED",
                                     "AUTO_OFF_OR_UNCONFIRMED")
            or (intent.permitted and intent.reason not in (
                "MANUAL_DATA_REQUEST_ONLY", "AUTO_MARKET_CONFIRMED"))
            or (not intent.permitted and intent.reason != "AUTO_OFF_OR_UNCONFIRMED")
            or type(intent.equities) is not tuple or intent.equities != selected
            or type(intent.indexes) is not tuple or intent.indexes != INDEXES
            or intent.index_signal_timeframe != "1m"
            or intent.watchlist_candle_timeframe != "3m"
            or type(intent.equity_seconds) is not int
            or intent.equity_seconds not in (180, 300, 600)):
        raise FeedError("Refresh intent no longer matches current app selection")
    lanes = [("indices", ())]
    if selected:
        lanes.append(("quotes", selected))
    results = {"status": "COMPLETED", "indexes": "SKIPPED",
               "quotes": "SKIPPED", "requests": 0}
    for feed, roster in lanes:
        # The HTTPS reader independently verifies status, media type, redirect,
        # request size, bearer-bound endpoint and exact Dhan-only payload.
        results["requests"] += 1
        try:
            changed = reader.refresh(inbox, feed, selected_equities=roster)
            results["indexes" if feed == "indices" else "quotes"] = (
                "HIST" if changed else "UNCHANGED")
        except FeedError:
            # Do not disclose upstream URLs, auth headers, token, or bodies.
            results["indexes" if feed == "indices" else "quotes"] = "WAIT"
            results["status"] = "PARTIAL"
    return results
