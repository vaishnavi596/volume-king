"""FT-2 offline protected HTTP -> actual Flet quote consumer parity.

TestClient only: never contacts Oracle/Dhan, initiates renewal or builds APK.
The session identities below are synthetic test grants, NOT real Android login.
"""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

from fastapi.testclient import TestClient
from pilot_v2.api_contract import make_snapshot
from pilot_v2.device_sessions import VerifiedDevice
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.http_gateway import create_pilot_app

M = "master_device_000001"
A = "second_device_00001"

file = Path(__file__).resolve().parents[1] / "android_app" / "src" / "quote_view.py"
spec = importlib.util.spec_from_file_location("ft2_http_flet_quote", file)
quote_view = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = quote_view
spec.loader.exec_module(quote_view)

def row(price, revision):
    return {"price": price, "freshness": "unverified", "live_verified": False,
            "revision": revision}

class AuthorizedHTTPToFletTests(unittest.TestCase):
    def setUp(self):
        t = tempfile.TemporaryDirectory()
        self.addCleanup(t.cleanup)
        self.now = [1000.0]
        self.sessions = DurableDeviceSessions(Path(t.name) / "session.db",
                          clock=lambda: self.now[0], ttl=60)
        self.sessions.bootstrap(M, authorize_bootstrap=lambda ident: ident == M)
        self.master = self.sessions.issue_verified(VerifiedDevice(M))
        self.sessions.master_grant(self.master, A, ["quotes"])
        self.delegated = self.sessions.issue_verified(VerifiedDevice(A))
        self.calls = []
        self.version = [1]
        def provider(device, feed):
            self.calls.append((device, feed))
            symbol = "NIFTY" if feed == "indices" else "TCS"
            return make_snapshot(self.version[0],
                        {symbol: row(25000 if feed == "indices" else 100,
                                     self.version[0])})
        self.client = TestClient(create_pilot_app(
            enabled=True, sessions=self.sessions, snapshot_provider=provider))
        self.view = quote_view.DeviceQuoteView()

    def get(self, path, bearer=None):
        headers = ({"Authorization": "Bearer " + bearer} if bearer else {})
        return self.client.get("/v2-pilot/" + path, headers=headers)

    def test_protected_gateway_to_actual_flet_consumer(self):
        self.assertEqual(self.get("quotes").status_code, 401)
        self.assertEqual(self.get("indices", self.delegated).status_code, 403)
        self.assertEqual(self.calls, [])
        response = self.get("quotes", self.delegated)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(self.view.apply(response.json(), ("TCS",)))
        self.assertEqual(self.view.visible("TCS", ("TCS",))["price"], 100)
        self.assertEqual(self.view.visible("TCS", ("TCS",))["status"], "HIST")
        self.assertEqual(self.calls, [(A, "quotes")])
        self.version[0] = 2
        index = self.get("indices", self.master)
        self.assertEqual(index.status_code, 200)
        self.assertTrue(self.view.apply(index.json(), ("TCS",)))
        self.assertEqual(self.view.visible("NIFTY", ())["status"], "HIST")
        self.assertEqual(self.view.visible("TCS", ("TCS",))["price"], 100)

    def test_permission_change_and_expiry_deny_before_provider(self):
        self.assertEqual(self.get("quotes", self.delegated).status_code, 200)
        self.assertEqual(len(self.calls), 1)
        self.sessions.master_grant(self.master, A, ["indices"])
        self.assertEqual(self.get("quotes", self.delegated).status_code, 403)
        self.assertEqual(len(self.calls), 1)
        fresh = self.sessions.issue_verified(VerifiedDevice(A))
        self.assertEqual(self.get("quotes", fresh).status_code, 403)
        self.assertEqual(self.get("indices", fresh).status_code, 200)
        self.now[0] += 60
        self.assertEqual(self.get("indices", fresh).status_code, 403)
        self.assertEqual(len(self.calls), 2)

    def test_disabled_and_no_order_route_even_with_master(self):
        self.sessions.master_grant(self.master, A, ["quotes"], enabled=False)
        self.assertEqual(self.get("quotes", self.delegated).status_code, 403)
        self.assertEqual(self.calls, [])
        self.assertEqual(self.client.post("/v2-pilot/orders",
              headers={"Authorization": "Bearer " + self.master}).status_code, 404)
        self.assertEqual(self.client.get("/openapi.json").status_code, 404)

if __name__ == "__main__":
    unittest.main()
