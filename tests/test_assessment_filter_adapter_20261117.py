"""No-network regression for the five-filter Dhan metric adapter."""
import unittest
from backend.assessment_filter_adapter import option_filter_rows, FILTER_IDS


class AssessmentAdapterTests(unittest.TestCase):
    def test_only_pcr_and_max_pain_from_unverified_readonly_metrics(self):
        rows = option_filter_rows({"pcr": 0.83, "max_pain": 25100,
                                   "freshness": "unverified", "signal_eligible": False})
        self.assertEqual(tuple(row["id"] for row in rows), FILTER_IDS)
        by_id = {row["id"]: row for row in rows}
        self.assertEqual(by_id["pcr"]["value"], 0.83)
        self.assertEqual(by_id["max_pain"]["value"], 25100)
        self.assertEqual(by_id["pcr"]["verification"], "unverified")
        for key in ("oi_support", "oi_resistance", "candle_trend"):
            self.assertEqual(by_id[key]["status"], "unavailable")

    def test_unsafe_and_missing_context_fails_closed(self):
        for payload in (None, {}, {"pcr": 0.8, "max_pain": 25100},
                        {"pcr": 0.8, "max_pain": 25100,
                         "freshness": "unverified", "signal_eligible": True}):
            with self.subTest(payload=payload):
                self.assertTrue(all(row["status"] == "unavailable"
                                    for row in option_filter_rows(payload)))

    def test_invalid_numbers_never_render(self):
        rows = option_filter_rows({"pcr": float("nan"), "max_pain": -5,
                                   "freshness": "unverified", "signal_eligible": False})
        self.assertTrue(all(row["status"] == "unavailable" for row in rows))


if __name__ == "__main__":
    unittest.main()
