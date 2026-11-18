"""FT-2 protected offline HTTP fixture -> Flet dual revision feed inbox.

No network request leaves FastAPI TestClient; no Dhan token/Oracle/APK.
"""
import sys
import tempfile
from pathlib import Path
import unittest
from fastapi.testclient import TestClient
from pilot_v2.api_contract import make_snapshot
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.device_sessions import VerifiedDevice
from pilot_v2.http_gateway import create_pilot_app

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from feed_inbox import DeviceFeedInbox, FeedError  # noqa: E402

MASTER = "master_device_000001"
SECOND = "second_device_00001"

def row(value, revision):
    return {"price": value, "freshness": "unverified",
            "live_verified": False, "revision": revision}

class ProtectedTwoLaneParityTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.clock = [1000.]
        sessions = DurableDeviceSessions(Path(tmp.name) / "two_lanes.db",
                                          clock=lambda: self.clock[0], ttl=60)
        sessions.bootstrap(MASTER, authorize_bootstrap=lambda device: device == MASTER)
        self.master = sessions.issue_verified(VerifiedDevice(MASTER))
        sessions.master_grant(self.master, SECOND, ["quotes"])
        self.second = sessions.issue_verified(VerifiedDevice(SECOND))
        self.calls = []
        self.rev = {"indices": 200, "quotes": 1}
        def provider(device, feed):
            self.calls.append((device, feed))
            if feed == "indices":
                return make_snapshot(self.rev[feed],
                     {"NIFTY": row(25000, self.rev[feed])})
            return make_snapshot(self.rev[feed],
                     {"TCS": row(100, self.rev[feed])})
        self.client = TestClient(create_pilot_app(enabled=True, sessions=sessions,
                                                   snapshot_provider=provider))
        self.inbox = DeviceFeedInbox()
        self.sessions = sessions

    def get(self, feed, token):
        return self.client.get("/v2-pilot/" + feed,
                         headers={"Authorization": "Bearer " + token})

    def test_index_200_before_equity_1_and_independent_revisions(self):
        index = self.get("indices", self.master)
        self.assertEqual(index.status_code, 200)
        self.assertTrue(self.inbox.apply_feed("indices", index.json(), ("TCS",)))
        quote = self.get("quotes", self.second)
        self.assertEqual(quote.status_code, 200)
        self.assertTrue(self.inbox.apply_feed("quotes", quote.json(), ("TCS",)))
        self.assertEqual(self.inbox.revision_for("quotes"), 1)
        self.assertEqual(self.inbox.revision_for("indices"), 200)
        self.assertEqual(self.inbox.visible("NIFTY", ())["price"], 25000)
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["price"], 100)
        self.assertEqual(self.calls, [(MASTER, "indices"), (SECOND, "quotes")])

    def test_denied_wrong_scope_and_expiry_do_not_dispatch(self):
        denied = self.get("indices", self.second)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.calls, [])
        self.clock[0] += 60
        expired = self.get("quotes", self.second)
        self.assertEqual(expired.status_code, 403)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.inbox.visible("TCS", ("TCS",))["status"], "WAIT")

    def test_invalid_cross_lane_injection_does_not_mutate_last_good(self):
        baseline = self.get("indices", self.master)
        self.inbox.apply_feed("indices", baseline.json(), ("TCS",))
        with self.assertRaises(FeedError):
            self.inbox.apply_feed("quotes", baseline.json(), ("TCS",))
        self.assertEqual(self.inbox.visible("NIFTY", ())["price"], 25000)
        self.assertEqual(self.inbox.revision_for("quotes"), -1)
        self.assertEqual(self.inbox.revision_for("indices"), 200)

if __name__ == "__main__":
    unittest.main()
