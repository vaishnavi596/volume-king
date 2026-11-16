"""Read-only Oracle shared assessment and readiness regression."""
import unittest
from unittest.mock import patch
from server_feed import ServerDhanReadOnly
from market_feed import FeedError

def sample():
    return {"symbol": "NIFTY", "bullish_score": None, "bearish_score": None,
            "signal_eligible": False, "live_orders_enabled": False,
            "factors": {name: {"status": "unavailable"}
                        for name in ("news", "futures", "options", "candle")},
            "assessment_filters": [{"id": x, "status": "unavailable"}
               for x in ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")]}

class AssessmentReadOnlyTests(unittest.TestCase):
    def setUp(self):
        self.client = ServerDhanReadOnly()

    def test_contract_and_endpoint(self):
        with patch.object(self.client, "_call", return_value=sample()) as request:
            self.assertEqual(len(self.client.assessment("NIFTY")["assessment_filters"]), 5)
            request.assert_called_once_with("/v2/assessment/NIFTY")

    def test_invalid_or_unsafe_response(self):
        changes = ({"symbol": "RELIANCE"}, {"signal_eligible": True},
                   {"bullish_score": 75}, {"live_orders_enabled": True},
                   {"factors": {}}, {"assessment_filters": []})
        for entry in changes:
            with self.subTest(entry=entry), patch.object(self.client, "_call",
                 return_value={**sample(), **entry}):
                with self.assertRaises(FeedError):
                    self.client.assessment("NIFTY")

    def test_path_injection_fails_before_request(self):
        with patch.object(self.client, "_call", side_effect=AssertionError("network")):
            for symbol in ("", "BAD SYMBOL", "../orders", "X" * 41):
                with self.subTest(symbol=symbol), self.assertRaises(FeedError):
                    self.client.assessment(symbol)

    def test_readiness_execution_locked(self):
        ok = {"live_orders_enabled": False, "orders":
              {"live_orders_enabled": False, "broker_submission_allowed": False}}
        # The real API requires an authenticated server session before an
        # Oracle readiness check, even when transport is mocked.
        with patch.object(self.client, "_call", side_effect=AssertionError("network")):
            with self.assertRaises(FeedError):
                self.client.server_readiness()
        self.client._origin = "https://example.org"
        self.client._pairing_key = "unit-test-only"
        with patch.object(self.client, "_call", return_value=ok) as request:
            self.assertFalse(self.client.server_readiness()["orders"]["broker_submission_allowed"])
            request.assert_called_once_with("/v2/server-readiness")
        for bad in ({**ok, "live_orders_enabled": True}, {"orders": {}},
                    {"live_orders_enabled": False, "orders": {"live_orders_enabled": False, "broker_submission_allowed": True}}):
            # Each independent invalid-response case must reach the mocked
            # transport, not consume the previously cached valid readiness.
            self.client._lane_coordinator.invalidate("context", "server-readiness")
            with patch.object(self.client, "_call", return_value=bad) as request:
                with self.assertRaises(FeedError):
                    self.client.server_readiness()
                request.assert_called_once_with("/v2/server-readiness")

if __name__ == "__main__":
    unittest.main()

