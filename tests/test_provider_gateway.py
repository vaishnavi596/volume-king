"""Provider gateway offline contract tests."""
import unittest
from fastapi.testclient import TestClient
from backend.provider_gateway import create_provider_app

KEY = "owner-access-key-" * 3


class ProviderGatewayTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(create_provider_app(KEY))
        self.headers = {"X-BotKing-Key": KEY}

    def test_access_control_and_no_orders(self):
        self.assertEqual(self.client.get("/v2/providers/capabilities").status_code, 403)
        self.assertEqual(self.client.post("/v2/providers/select", json={}).status_code, 403)
        self.assertEqual(self.client.post("/v2/orders", json={}, headers=self.headers).status_code, 404)
        self.assertFalse(self.client.get("/v2/providers/capabilities", headers=self.headers).json()["dhan_login_enabled"])

    def test_fresh_dhan_selected(self):
        payload = {"preferred": "Dhan", "now": 1000, "states": [
            {"provider": "Dhan", "status": "CONNECTED", "quote_timestamp": 999},
            {"provider": "Yahoo Finance", "status": "CONNECTED", "quote_timestamp": 995}]}
        result = self.client.post("/v2/providers/select", json=payload, headers=self.headers)
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()["provider"], "Dhan")

    def test_expired_dhan_falls_back_with_label(self):
        payload = {"preferred": "Dhan", "now": 1000, "states": [
            {"provider": "Dhan", "status": "EXPIRED", "quote_timestamp": 999},
            {"provider": "Yahoo Finance", "status": "CONNECTED", "quote_timestamp": 995}]}
        result = self.client.post("/v2/providers/select", json=payload, headers=self.headers)
        self.assertEqual(result.json()["provider"], "Yahoo Finance")
        self.assertTrue(result.json()["fallback"])

    def test_duplicate_provider_rejected(self):
        payload = {"now": 1000, "states": [
            {"provider": "Dhan", "status": "CONNECTED", "quote_timestamp": 999},
            {"provider": "Dhan", "status": "CONNECTED", "quote_timestamp": 999}]}
        self.assertEqual(self.client.post("/v2/providers/select", json=payload, headers=self.headers).status_code, 422)


if __name__ == "__main__":
    unittest.main()
