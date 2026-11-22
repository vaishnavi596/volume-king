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

    def test_duplicate_and_malformed_filter_ids_fail_closed(self):
        for bad_id in ("unknown", ["pcr"], None):
            with self.subTest(bad_id=repr(bad_id)):
                cache = cached_assessment("pcr", 1.25)
                cache["NIFTY"]["data"]["assessment_filters"][0]["id"] = bad_id
                lines = assessment_lines("NIFTY", cache, now=110)
                self.assertIn("WAIT", lines[0])
        cache = cached_assessment("pcr", 1.25)
        cache["NIFTY"]["data"]["assessment_filters"][0]["id"] = "pcr"
        self.assertIn("WAIT", assessment_lines("NIFTY", cache, now=110)[0])

    def test_placeholder_cannot_claim_available_values(self):
        cache = cached_assessment("pcr", 1.25)
        cache["NIFTY"]["data"]["collection_status"] = "not_configured"
        self.assertIn("WAIT", assessment_lines("NIFTY", cache, now=110)[0])
        cache["NIFTY"]["data"]["assessment_filters"][3]["status"] = "unavailable"
        self.assertIn("server producer not configured",
                      assessment_lines("NIFTY", cache, now=110)[0])

    def test_closed_market_expiry_is_explained_without_live_claim(self):
        cache = cached_assessment("pcr", 1.25)
        closed = assessment_lines("NIFTY", cache, now=500, market_open=False)
        self.assertIn("market closed", closed[0])
        self.assertIn("expired", closed[0])
        self.assertIn("WAIT", closed[0])
        opened = assessment_lines("NIFTY", cache, now=500, market_open=True)
        self.assertIn("cached assessment expired", opened[0])
        self.assertNotIn("market closed", opened[0])
        fresh = assessment_lines("NIFTY", cache, now=110, market_open=False)
        self.assertIn("PCR: 1.250", fresh)
        self.assertNotIn("market closed", fresh[0])

    def test_stale_and_unsafe_payloads_wait(self):
        cache = cached_assessment("pcr", 1.25)
        self.assertIn("WAIT", assessment_lines("NIFTY", cache, now=500)[0])
        cache["NIFTY"]["data"]["signal_eligible"] = True
        self.assertIn("WAIT", assessment_lines("NIFTY", cache, now=110)[0])


if __name__ == "__main__":
    unittest.main()
