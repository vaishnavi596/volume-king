"""Offline protected HTTP shell tests, zero Dhan/Oracle calls."""
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient
from pilot_v2.api_contract import make_snapshot
from pilot_v2.http_gateway import create_pilot_app
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.device_sessions import VerifiedDevice

M="master_device_000001"
D="second_device_00001"

def row(price):
    return {"price":price,"freshness":"unverified","live_verified":False,"revision":1}

class HTTPTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory();self.addCleanup(temp.cleanup)
        self.s=DurableDeviceSessions(Path(temp.name)/"auth.sqlite",clock=lambda:1000.)
        self.s.bootstrap(M,authorize_bootstrap=lambda _:True)
        self.master=self.s.issue_verified(VerifiedDevice(M))
        self.s.master_grant(self.master,D,["quotes"])
        self.second=self.s.issue_verified(VerifiedDevice(D))
        self.calls=[]
        def provider(device,feed):
            self.calls.append((device,feed))
            if feed=="indices":
                return make_snapshot(1,{"NIFTY":row(25000)})
            return make_snapshot(1,{"TCS":row(100)})
        self.provider=provider

    def test_flag_off_removes_routes(self):
        c=TestClient(create_pilot_app())
        for p in ("/v2-pilot/quotes","/v2-pilot/indices","/openapi.json",
                  "/v2-pilot/orders","/v2-pilot/master"):
            self.assertEqual(c.get(p).status_code,404)
        self.assertEqual(self.calls,[])

    def test_enabling_requires_trusted_components(self):
        with self.assertRaises(ValueError):
            create_pilot_app(enabled=True)
        with self.assertRaises(ValueError):
            create_pilot_app(enabled=True,sessions=self.s)

    def test_missing_or_wrong_bearer_does_not_call_provider(self):
        c=TestClient(create_pilot_app(enabled=True,sessions=self.s,snapshot_provider=self.provider))
        self.assertEqual(c.get("/v2-pilot/quotes").status_code,401)
        self.assertEqual(c.get("/v2-pilot/quotes",headers={"Authorization":"Bearer wrong"}).status_code,403)
        self.assertEqual(self.calls,[])

    def test_delegated_feed_scope_revoke_and_no_order_routes(self):
        c=TestClient(create_pilot_app(enabled=True,sessions=self.s,snapshot_provider=self.provider))
        headers={"Authorization":"Bearer "+self.second}
        x=c.get("/v2-pilot/quotes",headers=headers)
        self.assertEqual(x.status_code,200)
        self.assertFalse(x.json()["live_orders_enabled"])
        self.assertEqual(c.get("/v2-pilot/indices",headers=headers).status_code,403)
        self.assertEqual(c.post("/v2-pilot/orders",headers=headers).status_code,404)
        self.assertEqual(self.calls,[(D,"quotes")])
        self.s.master_grant(self.master,D,["quotes"],enabled=False)
        self.assertEqual(c.get("/v2-pilot/quotes",headers=headers).status_code,403)

    def test_master_index_and_invalid_snapshot_fail_closed(self):
        c=TestClient(create_pilot_app(enabled=True,sessions=self.s,snapshot_provider=self.provider))
        r=c.get("/v2-pilot/indices",headers={"Authorization":"Bearer "+self.master})
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.json()["quotes"]["NIFTY"]["price"],25000)
        def unsafe(device,feed):
            return dict(make_snapshot(1,{"TCS":row(100)}),token="private")
        c=TestClient(create_pilot_app(enabled=True,sessions=self.s,snapshot_provider=unsafe))
        with self.assertRaises(Exception):
            c.get("/v2-pilot/quotes",headers={"Authorization":"Bearer "+self.master})
if __name__=="__main__":
    unittest.main()
