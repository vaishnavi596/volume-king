"""V2 FT2 offline protected HTTP response to exact Flet quote-inbox contract."""
import sys
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from pilot_v2.api_contract import make_snapshot
from pilot_v2.device_sessions import VerifiedDevice
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.http_gateway import create_pilot_app

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from feed_inbox import DeviceFeedInbox
from quote_view import FeedError
from read_delivery import deliver_readonly_response

MASTER = "master_device_000001"
SECOND = "second_device_00001"


def row(price, revision):
    return {"price": price, "freshness": "unverified",
            "live_verified": False, "revision": revision}


class ReadDeliveryTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.now = [1000.0]
        self.sessions = DurableDeviceSessions(
            Path(tmp.name) / "sessions.db", clock=lambda: self.now[0], ttl=60)
        self.sessions.bootstrap(MASTER, authorize_bootstrap=lambda identity: identity == MASTER)
        self.master = self.sessions.issue_verified(VerifiedDevice(MASTER))
        self.sessions.master_grant(self.master, SECOND, ["quotes"])
        self.second = self.sessions.issue_verified(VerifiedDevice(SECOND))
        self.calls = []
        self.revision = [1]
        def provider(device, feed):
            self.calls.append((device, feed))
            symbol = "TCS" if feed == "quotes" else "NIFTY"
            return make_snapshot(self.revision[0], {symbol: row(100 if feed == "quotes" else 25000,
                                                                self.revision[0])})
        self.client = TestClient(create_pilot_app(
            enabled=True, sessions=self.sessions, snapshot_provider=provider))
        self.inbox = DeviceFeedInbox()

    def request(self, feed, token=None):
        header = {"Authorization": "Bearer " + token} if token else {}
        return self.client.get("/v2-pilot/" + feed, headers=header)

    def deliver(self, feed, response, selected=("TCS",), authenticated=True):
        return deliver_readonly_response(
            self.inbox, feed, response.status_code, response.json(),
            selected_equities=selected, authenticated_session=authenticated)

    def test_auth_errors_never_read_provider_or_mutate_app_cache(self):
        denied = self.request("quotes")
        self.assertEqual(denied.status_code, 401)
        with self.assertRaises(FeedError):
            self.deliver("quotes", denied)
        forbidden = self.request("indices", self.second)
        self.assertEqual(forbidden.status_code, 403)
        with self.assertRaises(FeedError):
            self.deliver("indices", forbidden)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["status"], "WAIT")

    def test_independent_index_equity_and_last_good_on_denial(self):
        equity = self.request("quotes", self.second)
        self.assertTrue(self.deliver("quotes", equity))
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)
        self.assertEqual(self.inbox.visible("NIFTY", ())["status"], "WAIT")
        self.revision[0] = 2
        index = self.request("indices", self.master)
        self.assertTrue(self.deliver("indices", index))
        self.assertEqual(self.inbox.visible("NIFTY", ())["price"], 25000)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)
        self.sessions.master_grant(self.master, SECOND, ["indices"])
        denied = self.request("quotes", self.second)
        self.assertEqual(denied.status_code, 403)
        with self.assertRaises(FeedError):
            self.deliver("quotes", denied)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["status"], "HIST")

    def test_trust_missing_malformed_schema_and_bad_lane_fail_closed(self):
        quote = self.request("quotes", self.second)
        with self.assertRaises(FeedError):
            self.deliver("quotes", quote, authenticated=False)
        with self.assertRaises(FeedError):
            deliver_readonly_response(self.inbox, "orders", 200, quote.json(),
                                      selected_equities=("TCS",),
                                      authenticated_session=True)
        with self.assertRaises(FeedError):
            deliver_readonly_response(self.inbox, "quotes", True, quote.json(),
                                      selected_equities=("TCS",),
                                      authenticated_session=True)
        corrupted = dict(quote.json(), live_orders_enabled=True)
        with self.assertRaises(FeedError):
            deliver_readonly_response(self.inbox, "quotes", 200, corrupted,
                                      selected_equities=("TCS",),
                                      authenticated_session=True)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["status"], "WAIT")

    def test_expired_or_revoked_session_cannot_replace_last_good(self):
        quote = self.request("quotes", self.second)
        self.deliver("quotes", quote)
        self.now[0] += 60
        response = self.request("quotes", self.second)
        self.assertEqual(response.status_code, 403)
        with self.assertRaises(FeedError):
            self.deliver("quotes", response)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)


if __name__ == "__main__":
    unittest.main()
