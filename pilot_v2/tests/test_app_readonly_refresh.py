"""Offline integration of V2 HTTPS quote lanes and selected-only intent."""
import io
import json
import sys
import unittest
from email.message import Message
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
# Import the tested app modules only when tests execute, after unittest's
# discovery has loaded all prior test modules. An earlier legacy regression
# intentionally reloads smart_data during module discovery.
def setUpModule():
    global LocalWatchlists, SmartDataSettings, make_refresh_intent
    global DeviceFeedInbox, FeedError, V2ReadonlyHTTPSReader
    global apply_approved_quote_intent
    from app_state import LocalWatchlists as _Watchlists
    from smart_data import SmartDataSettings as _Smart
    from refresh_intent import make_refresh_intent as _Intent
    from feed_inbox import DeviceFeedInbox as _Inbox, FeedError as _FeedError
    from secure_https_reader import V2ReadonlyHTTPSReader as _Reader
    from app_readonly_refresh import apply_approved_quote_intent as _Apply
    LocalWatchlists, SmartDataSettings = _Watchlists, _Smart
    make_refresh_intent = _Intent
    DeviceFeedInbox, FeedError = _Inbox, _FeedError
    V2ReadonlyHTTPSReader, apply_approved_quote_intent = _Reader, _Apply

class Response:
    status = 200
    def __init__(self, url, payload):
        self.url = url
        self.data = io.BytesIO(json.dumps(payload).encode("utf-8"))
        self.headers = Message()
        self.headers["Content-Type"] = "application/json"
    def geturl(self):
        return self.url
    def read(self, size):
        return self.data.read(size)
    def __enter__(self):
        return self
    def __exit__(self, *args):
        self.data.close()

class FakeOpener:
    def __init__(self, payloads, fail=()):
        self.payloads = payloads
        self.fail = set(fail)
        self.calls = []
    def open(self, request, timeout):
        path = request.full_url.rsplit("/", 1)[-1]
        self.calls.append(path)
        if path in self.fail:
            raise OSError("private-server-error")
        return Response(request.full_url, self.payloads[path])

def payload(revision, quotes):
    return {"protocol": "botking-v2-readonly", "schema_version": 1,
            "source": "dhan", "freshness": "unverified",
            "live_orders_enabled": False, "revision": revision,
            "quotes": {symbol: {"price": price, "freshness": "unverified",
                                "live_verified": False, "revision": revision}
                       for symbol, price in quotes.items()}}

def intent_for(count):
    w = LocalWatchlists()
    for i in range(count):
        w.add(i % 5, f"EQ{i:03d}")
    return w, make_refresh_intent(
        w, SmartDataSettings(),
        datetime(2026, 11, 19, 18, 0, tzinfo=ZoneInfo("Asia/Kolkata")),
        manual=True, confirmed_session=False)

class ApprovedQuoteRefreshTests(unittest.TestCase):
    def make_reader(self, count, fail=()):
        quotes = {f"EQ{i:03d}": 100 + i for i in range(count)}
        opener = FakeOpener({
            "quotes": payload(1, quotes),
            "indices": payload(1, {"NIFTY": 20000, "BANKNIFTY": 46000,
                                    "SENSEX": 80000})}, fail=fail)
        reader = V2ReadonlyHTTPSReader(
            "https://example.test", "x" * 32, opener=opener)
        return reader, opener

    def test_adaptive_selected_roster_and_index_isolation(self):
        for count in (0, 5, 70):
            with self.subTest(count=count):
                w, intent = intent_for(count)
                reader, opener = self.make_reader(count)
                inbox = DeviceFeedInbox()
                result = apply_approved_quote_intent(
                    intent, reader, inbox, w.selected)
                self.assertEqual(result["requests"], 2 if count else 1)
                self.assertEqual(opener.calls, ["indices", "quotes"]
                                 if count else ["indices"])
                self.assertEqual(inbox.visible("NIFTY", ())["status"], "HIST")
                if count:
                    self.assertEqual(inbox.visible(w.selected[0],
                                                   w.selected)["status"], "HIST")
                self.assertEqual(inbox.visible("EQ099", w.selected)["status"], "WAIT")

    def test_global_revision_only_does_not_claim_new_visible_prices(self):
        w, intent = intent_for(5)
        reader, opener = self.make_reader(5)
        inbox = DeviceFeedInbox()
        first = apply_approved_quote_intent(intent, reader, inbox, w.selected)
        self.assertEqual(first["indexes"], "HIST")
        self.assertEqual(first["quotes"], "HIST")
        old_price = inbox.visible("EQ000", w.selected)["price"]
        # Both envelopes advance, but every included per-symbol revision stays
        # at 1. Neither lane has fresh visible observations.
        opener.payloads["indices"] = payload(2, {"NIFTY": 1})
        opener.payloads["indices"]["quotes"]["NIFTY"]["revision"] = 1
        opener.payloads["quotes"] = payload(2, {"EQ000": 1})
        opener.payloads["quotes"]["quotes"]["EQ000"]["revision"] = 1
        second = apply_approved_quote_intent(intent, reader, inbox, w.selected)
        self.assertEqual(second["status"], "COMPLETED")
        self.assertEqual(second["indexes"], "UNCHANGED")
        self.assertEqual(second["quotes"], "UNCHANGED")
        self.assertEqual(inbox.revision_for("indices"), 2)
        self.assertEqual(inbox.revision_for("quotes"), 2)
        self.assertEqual(inbox.visible("EQ000", w.selected)["price"], old_price)
        self.assertEqual(inbox.visible("NIFTY", ())["price"], 20000)
        opener.payloads["quotes"] = payload(3, {"EQ000": 155})
        third = apply_approved_quote_intent(intent, reader, inbox, w.selected)
        self.assertEqual(third["indexes"], "UNCHANGED")
        self.assertEqual(third["quotes"], "HIST")
        self.assertEqual(inbox.visible("EQ000", w.selected)["price"], 155)

    def test_failed_equity_lane_retains_previous_and_index_continues(self):
        w, intent = intent_for(5)
        reader, opener = self.make_reader(5)
        inbox = DeviceFeedInbox()
        apply_approved_quote_intent(intent, reader, inbox, w.selected)
        before = inbox.visible(w.selected[0], w.selected)
        reader2, opener2 = self.make_reader(5, fail=("quotes",))
        result = apply_approved_quote_intent(
            intent, reader2, inbox, w.selected)
        self.assertEqual(result["status"], "PARTIAL")
        self.assertEqual(result["indexes"], "UNCHANGED")
        self.assertEqual(result["quotes"], "WAIT")
        self.assertEqual(inbox.visible(w.selected[0], w.selected), before)
        self.assertEqual(opener2.calls, ["indices", "quotes"])

    def test_untrusted_or_stale_request_does_not_fetch(self):
        w, intent = intent_for(5)
        reader, opener = self.make_reader(5)
        inbox = DeviceFeedInbox()
        with self.assertRaises(FeedError):
            apply_approved_quote_intent(intent, reader, inbox, ())
        with self.assertRaises(FeedError):
            apply_approved_quote_intent(intent, object(), inbox, w.selected)
        self.assertEqual(opener.calls, [])

    def test_invalid_roster_and_forged_refresh_contract_never_fetch(self):
        from refresh_intent import RefreshIntent
        w, intent = intent_for(5)
        reader, opener = self.make_reader(5)
        inbox = DeviceFeedInbox()
        for invalid in (("TCS", ["INFY"]), ("TCS", {"x": 1}),
                        ("NIFTY",), ("TCS", "TCS"), ("tcs",),
                        ("TCS/INVALID",), ("TCS ",), None, "TCS",
                        (s for s in ("TCS",)),
                        tuple(f"EQ{i:03d}" for i in range(71))):
            with self.subTest(roster=str(invalid)[:30]), self.assertRaises(FeedError):
                apply_approved_quote_intent(intent, reader, inbox, invalid)
        variations = (
            {"reason": "UNKNOWN"},
            {"reason": "AUTO_OFF_OR_UNCONFIRMED"},
            {"reason": "AUTO_MARKET_CONFIRMED", "permitted": False},
            {"permitted": 1},
            {"indexes": ("NIFTY",)},
            {"index_signal_timeframe": "5m"},
            {"watchlist_candle_timeframe": "1m"},
            {"equity_seconds": True},
        )
        from dataclasses import replace
        for edits in variations:
            with self.subTest(intent=str(edits)), self.assertRaises(FeedError):
                apply_approved_quote_intent(
                    replace(intent, **edits), reader, inbox, w.selected)
        self.assertEqual(opener.calls, [])
        self.assertEqual(inbox.revision_for("quotes"), -1)
        self.assertEqual(inbox.revision_for("indices"), -1)

    def test_no_real_transport_wired_into_app_before_login(self):
        main = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertNotIn("apply_approved_quote_intent(", main)
        self.assertNotIn("V2ReadonlyHTTPSReader(", main)
        self.assertNotIn("ServerAngelFeed", main)

if __name__ == "__main__":
    unittest.main()
