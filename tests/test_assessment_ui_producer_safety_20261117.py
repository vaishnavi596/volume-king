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

    def test_unverified_status_never_promotes_to_trading_signal(self):
        data = payload()
        data["collection_status"] = "legacy_unverified"
        lines = show(data)
        self.assertTrue(any("not a trade signal" in line for line in lines))

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
