"""Option-chain route must fail closed on unverified underlying and bad auth."""
import os
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.server import create_app
from backend.dhan_feed import DhanRateLimitError


class DhanOptionRouteTests(unittest.TestCase):
    def setUp(self):
        self.key = "k" * 40
        self.client = TestClient(create_app(pairing_key=self.key))

    def test_auth_and_mapping_reject_before_dhan_request(self):
        payload = {"symbol": "UNVERIFIEDINDEX", "expiry": "2099-12-31"}
        response = self.client.post("/dhan/option-chain", json=payload)
        self.assertEqual(response.status_code, 403)
        response = self.client.post("/dhan/option-chain", json=payload,
                                    headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 422)

    def test_success_response_is_explicitly_unverified_and_read_only(self):
        chain = {"status": "success", "data": {"oc": {
            "100": {"ce": {"oi": 10}, "pe": {"oi": 5}},
            "110": {"ce": {"oi": 5}, "pe": {"oi": 10}},
        }}}
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}):
            with patch("pathlib.Path.read_text", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_chain", return_value=chain) as feed:
                    response = self.client.post("/dhan/option-chain",
                        json={"symbol": "NIFTY", "expiry": "2099-12-31"},
                        headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 200)
        result = response.json()
        self.assertEqual(result["source"], "dhan")
        self.assertEqual(result["pcr"], 1.0)
        self.assertEqual(result["freshness"], "unverified")
        self.assertFalse(result["signal_eligible"])
        self.assertFalse(result["live_orders_enabled"])
        feed.assert_called_once_with("IDX_I", 13, "2099-12-31")

    def test_option_chain_assessment_handoff_same_symbol_only(self):
        """One successful read-only chain makes only unverified metrics visible."""
        headers = {"X-BotKing-Key": self.key}
        chain = {"status": "success", "data": {"oc": {
            "100": {"ce": {"oi": 100}, "pe": {"oi": 50}},
            "110": {"ce": {"oi": 50}, "pe": {"oi": 100}},
            "120": {"ce": {"oi": 50}, "pe": {"oi": 50}},
        }}}
        before = self.client.get("/v2/assessment/NIFTY", headers=headers)
        self.assertEqual(before.status_code, 200)
        self.assertIsNone(before.json()["bullish_score"])
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}):
            with patch("pathlib.Path.read_text", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_chain", return_value=chain) as feed:
                    posted = self.client.post("/dhan/option-chain",
                        json={"symbol": "NIFTY", "expiry": "2099-12-31"},
                        headers=headers)
        self.assertEqual(posted.status_code, 200)
        after = self.client.get("/v2/assessment/NIFTY", headers=headers)
        self.assertEqual(after.status_code, 200)
        rows = {row["id"]: row for row in after.json()["assessment_filters"]}
        for name in ("pcr", "max_pain"):
            self.assertEqual(rows[name]["status"], "available")
            self.assertEqual(rows[name]["value"], posted.json()[name])
            self.assertEqual(rows[name]["verification"], "unverified")
        self.assertEqual(after.json()["freshness"], "unverified")
        self.assertEqual(after.json()["expiry"], "2099-12-31")
        exact = self.client.get("/v2/assessment/NIFTY?expiry=2099-12-31",
                                headers=headers)
        self.assertEqual(exact.status_code, 200)
        self.assertEqual(exact.json()["collection_status"], "partial_unverified")
        wrong_expiry = self.client.get("/v2/assessment/NIFTY?expiry=2099-12-24",
                                       headers=headers)
        self.assertEqual(wrong_expiry.status_code, 200)
        self.assertEqual(wrong_expiry.json()["collection_status"], "not_configured")
        self.assertTrue(all(x["status"] == "unavailable"
                            for x in wrong_expiry.json()["assessment_filters"]))
        self.assertEqual(self.client.get("/v2/assessment/NIFTY?expiry=bad",
                             headers=headers).status_code, 422)
        self.assertFalse(after.json()["signal_eligible"])
        self.assertIsNone(after.json()["bullish_score"])
        self.assertIsNone(after.json()["bearish_score"])
        self.assertTrue(all(v["status"] == "unavailable"
                            for v in after.json()["factors"].values()))
        other = self.client.get("/v2/assessment/HDFCBANK", headers=headers)
        self.assertEqual(other.status_code, 200)
        self.assertTrue(all(v["status"] == "unavailable"
                            for v in other.json()["assessment_filters"]))
        separate = TestClient(create_app(pairing_key=self.key))
        self.assertEqual(separate.get("/v2/assessment/NIFTY",
            headers=headers).json()["collection_status"], "not_configured")
        feed.assert_called_once()

    def test_provider_rate_limit_returns_retry_after_without_fallback(self):
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}):
            with patch("pathlib.Path.read_text", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_chain",
                           side_effect=DhanRateLimitError("cooldown")):
                    response = self.client.post("/dhan/option-chain",
                        json={"symbol": "NIFTY", "expiry": "2099-12-31"},
                        headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 429)
        self.assertEqual(response.headers["retry-after"], "30")

    def test_incomplete_chain_returns_502_without_fabricated_metrics(self):
        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}):
            with patch("pathlib.Path.read_text", return_value="test-token"):
                with patch("backend.server.DhanFeed.option_chain",
                           return_value={"status": "success", "data": {"oc": {}}}):
                    response = self.client.post("/dhan/option-chain",
                        json={"symbol": "NIFTY", "expiry": "2099-12-31"},
                        headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 502)
        self.assertNotIn("pcr", response.json())

    def test_past_expiry_rejected_for_mapped_nifty(self):
        response = self.client.post("/dhan/option-chain",
                                    json={"symbol": "NIFTY", "expiry": "2020-01-01"},
                                    headers={"X-BotKing-Key": self.key})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
