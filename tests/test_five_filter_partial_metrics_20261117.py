"""Offline regression: partial five-filter metrics must fail closed independently."""
import copy
import unittest

from backend.assessment_filter_adapter import FILTER_IDS, option_filter_rows


class PartialMetricContractTests(unittest.TestCase):
    def test_one_valid_metric_does_not_enable_other_four(self):
        source = {"pcr": 0.82, "max_pain": float("nan"),
                  "freshness": "unverified", "signal_eligible": False}
        rows = option_filter_rows(source)
        self.assertEqual(tuple(row["id"] for row in rows), FILTER_IDS)
        self.assertEqual([row["id"] for row in rows if row["status"] == "available"], ["pcr"])
        self.assertEqual(next(row for row in rows if row["id"] == "pcr")["verification"], "unverified")
        self.assertFalse(any("bullish" in row or "bearish" in row or "score" in row for row in rows))

    def test_does_not_mutate_cached_source_or_share_result_rows(self):
        source = {"pcr": 1.2, "max_pain": 25100,
                  "freshness": "unverified", "signal_eligible": False}
        original = copy.deepcopy(source)
        first = option_filter_rows(source)
        first[0]["reason"] = "changed_by_ui"
        second = option_filter_rows(source)
        self.assertEqual(source, original)
        self.assertEqual(second[0]["reason"], "not_configured")

    def test_boolean_and_infinite_metrics_are_rejected(self):
        rows = option_filter_rows({"pcr": True, "max_pain": float("inf"),
                                   "freshness": "unverified", "signal_eligible": False})
        self.assertTrue(all(row["status"] == "unavailable" for row in rows))


if __name__ == "__main__":
    unittest.main()
