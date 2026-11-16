"""BK-5F presentation-only fail-closed regression fixtures."""
import unittest
from shared_assessment_ui import assessment_lines

FILTERS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")


def cached_assessment(key, value):
    rows = [{"id": name, "status": "available" if name == key else "unavailable",
             "value": value if name == key else None} for name in FILTERS]
    return {"NIFTY": {"fetched": 100.0, "data": {
        "symbol": "NIFTY", "live_orders_enabled": False,
        "signal_eligible": False, "collection_status": "partial",
        "assessment_filters": rows,
        "factors": {name: {"status": "unavailable"}
                    for name in ("news", "futures", "options", "candle")}
    }}}


class AssessmentMetricDisplayTests(unittest.TestCase):
    def test_invalid_numeric_metrics_remain_wait(self):
        for key in FILTERS[:-1]:
            for invalid in (0, -1, float("nan"), float("inf"), True, "100"):
                with self.subTest(key=key, invalid=str(invalid)):
                    lines = assessment_lines("NIFTY", cached_assessment(key, invalid), now=110)
                    label = next(line for line in lines if line.startswith({
                        "oi_support": "OI Support:", "oi_resistance": "OI Resistance:",
                        "max_pain": "Max Pain:", "pcr": "PCR:"}[key]))
                    self.assertTrue(label.endswith("WAIT"), label)

    def test_positive_context_is_not_trading_signal(self):
        lines = assessment_lines("NIFTY", cached_assessment("pcr", 1.25), now=110)
        self.assertIn("PCR: 1.250", lines)
        self.assertIn("not a trade signal", lines[-1])

    def test_stale_and_unsafe_payloads_wait(self):
        cache = cached_assessment("pcr", 1.25)
        self.assertIn("WAIT", assessment_lines("NIFTY", cache, now=500)[0])
        cache["NIFTY"]["data"]["signal_eligible"] = True
        self.assertIn("WAIT", assessment_lines("NIFTY", cache, now=110)[0])


if __name__ == "__main__":
    unittest.main()
