"""Offline HTTPS read-only transport contract; no external network calls."""
import json
import sys
import unittest
from email.message import Message
from pathlib import Path
from urllib.error import HTTPError

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from feed_inbox import DeviceFeedInbox, FeedError
from secure_https_reader import V2ReadonlyHTTPSReader

TOKEN = "a" * 48
ORIGIN = "https://v2.example.test"


def snapshot(revision, symbol, price):
    return {"protocol": "botking-v2-readonly", "schema_version": 1,
            "source": "dhan", "freshness": "unverified",
            "live_orders_enabled": False, "revision": revision,
            "quotes": {symbol: {"price": price, "freshness": "unverified",
                                "live_verified": False, "revision": revision}}}


class FakeResponse:
    def __init__(self, url, payload, status=200, content_type="application/json"):
        self._url, self.status = url, status
        self._body = json.dumps(payload).encode("utf-8")
        self.headers = Message()
        self.headers["Content-Type"] = content_type

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def geturl(self):
        return self._url

    def read(self, count):
        return self._body[:count]


class FakeOpener:
    def __init__(self):
        self.calls = []
        self.next_response = None
        self.fail = None

    def open(self, request, timeout):
        self.calls.append((request, timeout))
        if self.fail is not None:
            raise self.fail
        return self.next_response


class HTTPSReaderTests(unittest.TestCase):
    def setUp(self):
        self.opener = FakeOpener()
        self.inbox = DeviceFeedInbox()
        self.reader = V2ReadonlyHTTPSReader(ORIGIN, TOKEN, opener=self.opener)

    def offer(self, feed, revision, symbol, price, *, response_url=None):
        url = response_url or ORIGIN + "/v2-pilot/" + feed
        self.opener.next_response = FakeResponse(url, snapshot(revision, symbol, price))

    def test_two_authorized_lanes_are_get_only_and_independent(self):
        self.offer("quotes", 1, "TCS", 100)
        self.assertTrue(self.reader.refresh(self.inbox, "quotes", selected_equities=("TCS",)))
        self.offer("indices", 1, "NIFTY", 25000)
        self.assertTrue(self.reader.refresh(self.inbox, "indices", selected_equities=("TCS",)))
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)
        self.assertEqual(self.inbox.visible("NIFTY", ())["price"], 25000)
        self.assertEqual([item[0].get_method() for item in self.opener.calls],
                         ["GET", "GET"])
        self.assertEqual([item[0].full_url for item in self.opener.calls],
                         [ORIGIN + "/v2-pilot/quotes", ORIGIN + "/v2-pilot/indices"])
        self.assertIn(TOKEN, self.opener.calls[0][0].get_header("Authorization"))

    def test_denied_http_and_redirect_preserve_last_good_without_secret_leak(self):
        self.offer("quotes", 1, "TCS", 100)
        self.reader.refresh(self.inbox, "quotes", selected_equities=("TCS",))
        self.opener.fail = HTTPError(ORIGIN + "/v2-pilot/quotes", 403, TOKEN, {}, None)
        with self.assertRaises(FeedError) as err:
            self.reader.refresh(self.inbox, "quotes", selected_equities=("TCS",))
        self.assertNotIn(TOKEN, str(err.exception))
        self.opener.fail = None
        self.offer("quotes", 2, "TCS", 999,
                   response_url="https://attacker.example/v2-pilot/quotes")
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "quotes", selected_equities=("TCS",))
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)

    def test_revoked_or_expired_session_ends_local_bearer_and_prevents_retry(self):
        for code in (401, 403):
            with self.subTest(code=code):
                opener = FakeOpener()
                reader = V2ReadonlyHTTPSReader(ORIGIN, TOKEN, opener=opener)
                inbox = DeviceFeedInbox()
                opener.next_response = FakeResponse(
                    ORIGIN + "/v2-pilot/quotes", snapshot(1, "TCS", 100))
                self.assertTrue(reader.refresh(
                    inbox, "quotes", selected_equities=("TCS",)))
                self.assertTrue(reader.session_active)
                opener.fail = HTTPError(ORIGIN + "/v2-pilot/quotes",
                                        code, TOKEN, {}, None)
                with self.assertRaises(FeedError) as error:
                    reader.refresh(inbox, "quotes", selected_equities=("TCS",))
                self.assertNotIn(TOKEN, str(error.exception))
                self.assertFalse(reader.session_active)
                prior = len(opener.calls)
                with self.assertRaises(FeedError):
                    reader.refresh(inbox, "quotes", selected_equities=("TCS",))
                self.assertEqual(len(opener.calls), prior)
                self.assertEqual(inbox.visible("TCS", ("TCS",))["price"], 100)

    def test_explicit_auth_error_response_without_http_exception_invalidates(self):
        self.opener.next_response = FakeResponse(
            ORIGIN + "/v2-pilot/indices", snapshot(1, "NIFTY", 25000),
            status=403)
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "indices")
        self.assertFalse(self.reader.session_active)
        before = len(self.opener.calls)
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "indices")
        self.assertEqual(len(self.opener.calls), before)
        self.assertEqual(self.inbox.visible("NIFTY", ())["status"], "WAIT")

    def test_rate_limit_does_not_erase_signed_in_reader(self):
        self.opener.fail = HTTPError(
            ORIGIN + "/v2-pilot/indices", 429, TOKEN, {}, None)
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "indices")
        self.assertTrue(self.reader.session_active)
        self.reader.invalidate()
        self.assertFalse(self.reader.session_active)
        count = len(self.opener.calls)
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "indices")
        self.assertEqual(len(self.opener.calls), count)

    def test_direct_reader_malformed_selected_roster_has_zero_http_calls(self):
        invalid = (None, "TCS", {"TCS"}, (x for x in ("TCS",)),
                   ("TCS", ["INFY"]), ("TCS", {"symbol": "INFY"}),
                   ("TCS", "TCS"), ("NIFTY",), ("tcs",), ("TCS ",),
                   tuple(f"EQ{i:03d}" for i in range(71)))
        for selected in invalid:
            with self.subTest(roster=repr(selected)[:80]):
                with self.assertRaises(FeedError):
                    self.reader.refresh(self.inbox, "quotes",
                                        selected_equities=selected)
        self.assertEqual(self.opener.calls, [])
        self.assertEqual(self.inbox.revision_for("quotes"), -1)
        self.assertEqual(self.inbox.revision_for("indices"), -1)
        # Authorized empty index lane and explicitly selected equity are valid.
        self.offer("indices", 1, "NIFTY", 25000)
        self.assertTrue(self.reader.refresh(self.inbox, "indices"))
        self.offer("quotes", 1, "TCS", 100)
        self.assertTrue(self.reader.refresh(
            self.inbox, "quotes", selected_equities=("TCS",)))
        self.assertEqual(len(self.opener.calls), 2)

    def test_logout_during_http_read_discards_late_snapshot(self):
        self.offer("quotes", 1, "TCS", 100)
        owner = self.reader
        upstream = self.opener

        class LogoutInFlight:
            def __init__(self):
                self.calls = 0

            def open(self, request, timeout):
                self.calls += 1
                owner.invalidate()  # Revoke locally before response is delivered.
                return upstream.next_response

        wrapped = LogoutInFlight()
        owner._opener = wrapped  # Dependency-injected fake transport only.
        with self.assertRaisesRegex(FeedError, "session ended"):
            owner.refresh(self.inbox, "quotes",
                          selected_equities=("TCS",))
        self.assertEqual(wrapped.calls, 1)
        self.assertFalse(owner.session_active)
        self.assertEqual(self.inbox.revision_for("quotes"), -1)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["status"], "WAIT")
        with self.assertRaises(FeedError):
            owner.refresh(self.inbox, "quotes", selected_equities=("TCS",))
        self.assertEqual(wrapped.calls, 1)

    def test_invalid_https_origins_and_bearers_are_rejected(self):
        for origin in ("http://v2.example.test", "https://user:pass@v2.example.test",
                       "https://v2.example.test/secret", "https://v2.example.test/?q=1",
                       "https://v2.example.test/#x", "https://v2.example.test:invalid",
                       "https://v2.example.test:0"):
            with self.subTest(origin=origin), self.assertRaises(FeedError):
                V2ReadonlyHTTPSReader(origin, TOKEN, opener=self.opener)
        for bearer in ("bad", "x" * 45 + "\n", "x" * 45 + "\r"):
            with self.subTest(bearer=bearer), self.assertRaises(FeedError):
                V2ReadonlyHTTPSReader(ORIGIN, bearer, opener=self.opener)

    def test_bad_feed_schema_and_content_type_do_not_clear_cache(self):
        self.offer("quotes", 1, "TCS", 100)
        self.reader.refresh(self.inbox, "quotes", selected_equities=("TCS",))
        self.offer("quotes", 2, "NIFTY", 999)
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "quotes", selected_equities=("TCS",))
        self.opener.next_response = FakeResponse(
            ORIGIN + "/v2-pilot/quotes", snapshot(2, "TCS", 999),
            content_type="text/html")
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "quotes", selected_equities=("TCS",))
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "orders", selected_equities=("TCS",))

    def test_oversized_and_wrong_status_are_rejected(self):
        self.opener.next_response = FakeResponse(
            ORIGIN + "/v2-pilot/indices", snapshot(1, "NIFTY", 25000),
            status=206)
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "indices")
        self.opener.next_response = FakeResponse(
            ORIGIN + "/v2-pilot/indices", {"oversized": "x" * 70000})
        with self.assertRaises(FeedError):
            self.reader.refresh(self.inbox, "indices")
        self.assertEqual(self.inbox.visible("NIFTY", ())["status"], "WAIT")


if __name__ == "__main__":
    unittest.main()
