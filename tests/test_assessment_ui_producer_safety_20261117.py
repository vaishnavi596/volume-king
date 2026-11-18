"""Assessment UI must reject unsafe producer states and invented scores."""
import unittest
from src.shared_assessment_ui import assessment_lines, compact_assessment_summary

IDS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")


def payload():
    return {
        "symbol": "NIFTY", "live_orders_enabled": False, "signal_eligible": False,
        "collection_status": "partial_unverified", "freshness": "unverified",
        "assessment_filters": [
            {"id": key, "status": "available", "value": 0.8}
            if key == "pcr" else {"id": key, "status": "unavailable", "reason": "not_configured"}
            for key in IDS
        ],
        "factors": {key: {"status": "unavailable", "bullish": None, "bearish": None}
                    for key in ("news", "futures", "options", "candle")},
        "bullish_score": None, "bearish_score": None,
    }


def show(data):
    return assessment_lines("NIFTY", {"NIFTY": {"fetched": 100, "data": data}}, now=101)


class AssessmentUiProducerSafetyTests(unittest.TestCase):
    def test_valid_informational_pcr_is_not_signal(self):
        lines = show(payload())
        self.assertTrue(any("PCR: 0.800" in line for line in lines))
        self.assertTrue(any("not a trade signal" in line for line in lines))

    def test_unverified_status_never_promotes_to_trading_signal(self):
        data = payload()
        data["collection_status"] = "legacy_unverified"
        lines = show(data)
        self.assertTrue(any("not a trade signal" in line for line in lines))

    def test_candle_direction_available_is_informational_not_score(self):
        data = payload()
        data["factors"]["candle"] = {
            "status": "direction_available", "direction": "bullish",
            "bullish": None, "bearish": None
        }
        shown = show(data)
        self.assertGreater(len(shown), 1)
        self.assertTrue(any("PCR: 0.800" in line for line in shown))
        self.assertTrue(any("not a trade signal" in line for line in shown))
        self.assertFalse(any("BULLISH %" in line or "BEARISH %" in line for line in shown))
        self.assertEqual(shown.count("Filter 6: "), 1)

    def test_historical_candle_context_is_separate_from_five_filter_votes(self):
        data = payload()
        data["factors"]["candle"] = {
            "status": "direction_available", "direction": "bearish"}
        # Even with source candle context, all five filter slots remain WAIT.
        for item in data["assessment_filters"]:
            item.update(status="unavailable", value=None)
        shown = show(data)
        self.assertEqual(sum(line.endswith("WAIT") or ": WAIT" in line
                             for line in shown[1:6]), 5)
        self.assertIn("Candle: WAIT", shown)
        self.assertIn("Candle factor: historical direction context • unverified", shown)
        compact = compact_assessment_summary(shown)
        self.assertIn("0 context / 5 WAIT", compact)
        self.assertIn("candle history context", compact)
        self.assertNotIn("BEARISH", compact)
        self.assertEqual(shown.count("Filter 6: "), 1)
        self.assertEqual(compact_assessment_summary(show(payload())).count(
            "candle history context"), 0)

    def test_direction_available_only_allowed_for_candle_factor(self):
        for factor in ("news", "futures", "options"):
            with self.subTest(factor=factor):
                data = payload()
                data["factors"][factor]["status"] = "direction_available"
                self.assertIn("incomplete factors", show(data)[0])
        data = payload()
        data["factors"]["candle"]["status"] = "live_verified"
        self.assertIn("incomplete factors", show(data)[0])

    def test_foreign_source_and_mislabeled_freshness_wait(self):
        for field, value in (("source", "yahoo"),
                             ("source", "angel"),
                             ("freshness", "live_verified"),
                             ("freshness", "stale")):
            with self.subTest(field=field, value=value):
                data = payload()
                data[field] = value
                shown = show(data)
                self.assertEqual(len(shown), 1)
                self.assertIn("WAIT", shown[0])
        data = payload()
        data["source"] = "dhan"
        self.assertTrue(any("PCR: 0.800" in line for line in show(data)))

    def test_unverified_percentages_never_advertised_as_scores(self):
        for field in ("bullish_score", "bearish_score"):
            with self.subTest(field=field):
                data = payload()
                data[field] = 95
                shown = show(data)
                self.assertEqual(len(shown), 1)
                self.assertIn("WAIT", shown[0])

    def test_missing_live_orders_flag_fails_closed(self):
        data = payload()
        data.pop("live_orders_enabled")
        self.assertIn("WAIT", show(data)[0])

    def test_signal_eligible_true_fails_closed(self):
        data = payload()
        data["signal_eligible"] = True
        self.assertIn("WAIT", show(data)[0])

    def test_missing_factor_fails_closed(self):
        data = payload()
        del data["factors"]["options"]
        self.assertIn("WAIT", show(data)[0])


if __name__ == "__main__":
    unittest.main()
