"""Offline classification checks for the three OPEN release lanes only."""
import importlib.util
from pathlib import Path
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "audit_oracle_three_open_lanes_readonly.py"
spec = importlib.util.spec_from_file_location("bk_three_open_lanes", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class ThreeOpenLaneTests(unittest.TestCase):
    def test_readonly_snapshot_reports_three_independent_gaps(self):
        readiness = (200, {
            "collector": {"configured_enabled": True, "status": "recently_collected",
                          "interval_seconds": 90, "last_success_age_seconds": 31},
            "news": {"status": "feed_not_configured"},
            "scoring": {"status": "unverified"},
        })
        snapshot = (200, {"collection_status": "recently_collected",
                          "age_seconds": 31, "quotes": {"RELIANCE": {"ltp": 100}},
                          "live_orders_enabled": False})
        assessments = {name: (200, {
            "status": "incomplete", "news_status": "feed_not_configured",
            "cache_status": "available", "filters_status": "partial",
            "signal_eligible": False, "bullish_score": None, "bearish_score": None,
            "factors": {"options": {"status": "unavailable"},
                        "futures": {"status": "unavailable"}}
        }) for name in module.SYMBOLS}
        result = module.classify(readiness, snapshot, assessments)
        self.assertEqual(set(result), {"lane_A_options_futures",
                                      "lane_B_news_scoring",
                                      "lane_C_collector_freshness", "notes"})
        self.assertEqual(result["lane_A_options_futures"]["NIFTY"]["options"],
                         "unavailable")
        self.assertFalse(result["lane_B_news_scoring"]["indices"]["SENSEX"]["score_present"])
        self.assertEqual(result["lane_C_collector_freshness"]["cached_equity_count"], 1)
        self.assertTrue(result["lane_C_collector_freshness"]["snapshot_orders_off"])
        self.assertEqual(result["notes"]["direct_dhan_calls"], 0)

    def test_missing_authorization_and_data_never_becomes_pass(self):
        result = module.classify((0, {}), (0, {}), {})
        self.assertEqual(result["lane_C_collector_freshness"]["readiness_http"], 0)
        self.assertIsNone(result["lane_C_collector_freshness"]["cached_equity_count"])
        self.assertFalse(result["lane_B_news_scoring"]["indices"]["NIFTY"]["score_present"])
        self.assertFalse(result["lane_B_news_scoring"]["indices"]["NIFTY"]["signal_eligible"])
        self.assertFalse(result["lane_C_collector_freshness"]["snapshot_orders_off"])

    def test_all_routes_allowlisted_and_redirect_blocked(self):
        self.assertEqual(len(module.ROUTES), 5)
        self.assertIsNone(module.NoRedirect().redirect_request(
            None, None, 302, "redirect", {}, "https://outside.invalid"))
        with self.assertRaises(ValueError):
            module._get("https://outside.invalid", "not-a-real-key")


if __name__ == "__main__":
    unittest.main()
