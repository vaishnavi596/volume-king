"""Assessment UI must reject unsafe producer states and invented scores."""
import unittest
from src.shared_assessment_ui import assessment_lines

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

    def test_unknown_producer_status_fails_closed(self):
        data = payload()
        data["collection_status"] = "live"
        self.assertEqual(len(show(data)), 1)
        self.assertIn("WAIT", show(data)[0])

    def test_fabricated_bullish_score_fails_closed(self):
        data = payload()
        data["bullish_score"] = 85
        self.assertIn("WAIT", show(data)[0])

    def test_factor_score_fails_closed(self):
        data = payload()
        data["factors"]["options"]["bullish"] = 95
        self.assertIn("WAIT", show(data)[0])

    def test_partial_without_evidence_fails_closed(self):
        data = payload()
        data["assessment_filters"][3] = {"id": "pcr", "status": "unavailable"}
        self.assertIn("WAIT", show(data)[0])


if __name__ == "__main__":
    unittest.main()
