"""No-network controls for the Smart Engine research planner."""
import unittest
from src.market_research_planner import ResearchRequest, plan_research


class ResearchPlannerTests(unittest.TestCase):
    def test_one_month_year_two_year_are_supported_without_requests(self):
        for w in ("1m", "1y", "2y"):
            with self.subTest(w=w):
                result = plan_research(ResearchRequest("NIFTY", "2026-11-18", w))
                self.assertEqual(result["broker_requests_executed"], 0)
                self.assertEqual(result["browser_requests_executed"], 0)
                self.assertFalse(result["signal_eligible"])
                self.assertIsNone(result["bullish_score"])
                self.assertEqual(result["end_date"], "2026-11-17")

    def test_cache_first_and_permission_gate(self):
        req = ResearchRequest("HDFCBANK", "2026-11-18", "1m")
        cached = plan_research(req, cached_days=["2026-11-12", "2026-11-17"],
                               broker_history_available=True)
        self.assertEqual(cached["next_source"], "cached_dhan_history")
        self.assertEqual(cached["state"], "CACHE_PRESENT_COVERAGE_UNVERIFIED")
        enabled = plan_research(
            ResearchRequest("HDFCBANK", "2026-11-18", "1m", enable_dhan=True),
            cached_days=["2026-11-17"], broker_history_available=True)
        self.assertEqual(enabled["next_source"], "dhan_historical")
        self.assertEqual(enabled["max_request_chunks"], 2)
        self.assertEqual(enabled["broker_requests_executed"], 0)

    def test_web_research_is_context_not_price_or_causality_proof(self):
        req = ResearchRequest("TCS", "2026-11-18", "2y",
                              category="news_context", enable_online=True)
        inactive = plan_research(req, online_provider_available=False)
        self.assertEqual(inactive["state"], "ONLINE_RESEARCH_NOT_CONFIGURED")
        active = plan_research(req, online_provider_available=True)
        self.assertEqual(active["next_source"], "online_primary_sources")
        self.assertFalse(active["source_verified"])
        self.assertFalse(active["signal_eligible"])
        self.assertIsNone(active["bullish_score"])

    def test_no_implicit_fanout_or_future_data(self):
        req = ResearchRequest("NIFTY", "2026-11-18", "1y", enable_dhan=True)
        result = plan_research(req, broker_history_available=True,
                               cached_days=["2026-11-20", "2026-11-10"])
        self.assertEqual(result["cache_days_known"], 1)
        self.assertEqual(result["broker_requests_executed"], 0)
        with self.assertRaises(ValueError):
            plan_research(req, broker_history_available=True, max_request_chunks=200)
        with self.assertRaises(ValueError):
            ResearchRequest("NIFTY", "2026-11-18", "5y")
        with self.assertRaises(ValueError):
            ResearchRequest("NIFTY", "2026-11-18", "1m", enable_dhan=1)


if __name__ == "__main__":
    unittest.main()
