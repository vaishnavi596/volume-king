"""V2 standalone gateway fails closed: offline synthetic HTTP ASGI probes."""
import importlib.util
from pathlib import Path
import unittest

from fastapi.testclient import TestClient

SRC = Path(__file__).resolve().parents[1] / "isolated_gateway_app.py"
spec = importlib.util.spec_from_file_location("isolated_v2_gateway", SRC)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class IsolatedGatewayTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(module.create_app())

    def test_local_health_not_live(self):
        r = self.client.get("/v2-pilot/health")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "staged_disabled")
        self.assertFalse(r.json()["live_data"])
        self.assertFalse(r.json()["live_orders_enabled"])

    def test_auth_routes_exist_but_no_bootstrap(self):
        for route in ("challenge", "login"):
            r = self.client.post("/v2-pilot/auth/" + route,
                                 json={"device_id": "untrusted"})
            self.assertEqual(r.status_code, 503)
            self.assertEqual(r.headers.get("cache-control"), "no-store")
            self.assertNotIn("untrusted", r.text)

    def test_auth_rejects_large_input(self):
        r = self.client.post("/v2-pilot/auth/login",
                             content=b"x" * 1025,
                             headers={"Content-Type": "application/json"})
        self.assertEqual(r.status_code, 413)

    def test_read_feeds_require_verified_device(self):
        for route in ("quotes", "indices"):
            r = self.client.get("/v2-pilot/" + route)
            self.assertEqual(r.status_code, 401)
            r = self.client.get("/v2-pilot/" + route,
                                headers={"Authorization": "Bearer " + "x" * 48})
            self.assertEqual(r.status_code, 503)
            self.assertNotIn('"quotes":', r.text)

    def test_no_v1_or_order_routes(self):
        for route in ("/health", "/dhan/ltp", "/orders", "/v2-pilot/orders"):
            self.assertEqual(self.client.get(route).status_code, 404)


if __name__ == "__main__":
    unittest.main()
