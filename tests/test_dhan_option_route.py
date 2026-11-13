"""Option-chain route must fail closed on unverified underlying and bad auth."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.server import create_app


class DhanOptionRouteTests(unittest.TestCase):
    def setUp(self):
        self.key = "k" * 40
        self.client = TestClient(create_app(pairing_key=self.key))

    def test_auth_and_mapping_reject_before_dhan_request(self):
        payload = {"symbol": "BANKNIFTY", "expiry": "2099-12-31"}
        response = self.client.post("/dhan/option-chain", json=payload)
        self.assertEqual(response.status_code, 403)
        response = self.client.post("/dhan/option-chain", json=payload,
                                    headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 422)

    def test_past_expiry_rejected_for_mapped_nifty(self):
        response = self.client.post("/dhan/option-chain",
                                    json={"symbol": "NIFTY", "expiry": "2020-01-01"},
                                    headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
