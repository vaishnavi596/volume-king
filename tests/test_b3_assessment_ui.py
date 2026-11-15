"""Oracle assessment view must preserve value, symbol, expiry and verification boundaries."""
import unittest
from shared_assessment_ui import assessment_lines

def make(symbol="NIFTY"):
    return {"symbol": symbol, "live_orders_enabled": False, "signal_eligible": False,
            "factors": {n: {"status": "unavailable"} for n in ("news", "futures", "options", "candle")},
            "assessment_filters": [{"id": key, "status": "available", "value": value}
                for key, value in (("oi_support", 25000.0), ("oi_resistance", 25200.0),
                    ("max_pain", 25100.0), ("pcr", 0.83049), ("candle_trend", "bullish"))]}

class AssessmentViewTests(unittest.TestCase):
    def test_values_are_read_only_not_signal(self):
        lines = assessment_lines("NIFTY", {"NIFTY": {"fetched": 100, "data": make()}}, now=120)
        self.assertTrue(any("25,000" in s for s in lines))
        self.assertTrue(any("0.830" in s for s in lines))
        self.assertTrue(any("historical/unverified" in s for s in lines))
        self.assertTrue(any("not a trade signal" in s for s in lines))

    def test_symbol_and_ttl_isolation(self):
        cache = {"NIFTY": {"fetched": 100, "data": make()}}
        self.assertIn("not requested", assessment_lines("BANKNIFTY", cache, now=110)[0])
        self.assertIn("expired", assessment_lines("NIFTY", cache, now=400)[0])
        self.assertIn("mismatched", assessment_lines("RELIANCE", {"RELIANCE": cache["NIFTY"]}, now=110)[0])

    def test_unsafe_or_missing_factors_fail_closed(self):
        d = make()
        d["signal_eligible"] = True
        self.assertIn("unsafe", assessment_lines("NIFTY", {"NIFTY": {"fetched": 1, "data": d}}, now=2)[0])
        d = make()
        d["factors"].pop("news")
        self.assertIn("incomplete", assessment_lines("NIFTY", {"NIFTY": {"fetched": 1, "data": d}}, now=2)[0])

if __name__ == "__main__":
    unittest.main()
