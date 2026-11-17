"""Pure five-filter response builder regression: never invent live votes."""
import unittest

from backend.assessment_filter_adapter import read_only_assessment, FILTER_IDS


class SharedAssessmentBuilderTests(unittest.TestCase):
    def test_cached_unverified_pcr_and_max_pain_are_informational_only(self):
        payload = read_only_assessment("NIFTY", {
            "pcr": 0.83, "max_pain": 25100,
            "freshness": "unverified", "signal_eligible": False,
        })
        self.assertEqual(payload["collection_status"], "partial_unverified")
        self.assertEqual(tuple(r["id"] for r in payload["assessment_filters"]), FILTER_IDS)
        self.assertEqual([r["id"] for r in payload["assessment_filters"]
                          if r["status"] == "available"], ["max_pain", "pcr"])
        self.assertEqual(payload["factors"].keys(),
                         {"news", "futures", "options", "candle"})
        self.assertTrue(all(v["status"] == "unavailable"
                            for v in payload["factors"].values()))
        self.assertIsNone(payload["bullish_score"])
        self.assertIsNone(payload["bearish_score"])
        self.assertIs(payload["signal_eligible"], False)
        self.assertIs(payload["live_orders_enabled"], False)

    def test_missing_or_unverified_eligibility_fails_closed(self):
        for metrics in (None, {}, {"pcr": 0.8, "max_pain": 25000},
                        {"pcr": 0.8, "max_pain": 25000,
                         "freshness": "unverified", "signal_eligible": True}):
            with self.subTest(metrics=metrics):
                result = read_only_assessment("NIFTY", metrics)
                self.assertEqual(result["collection_status"], "not_configured")
                self.assertTrue(all(row["status"] == "unavailable"
                                    for row in result["assessment_filters"]))
                self.assertIs(result["signal_eligible"], False)


if __name__ == "__main__":
    unittest.main()
