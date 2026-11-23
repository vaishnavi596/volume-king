"""STANDARD-2: classify real source spacing faults without creating votes."""
import unittest
from datetime import datetime, timedelta, timezone
from scanner_engine import analyze

IST = timezone(timedelta(hours=5, minutes=30))

def bar(hour, minute):
    stamp = int(datetime(2026, 11, 23, hour, minute, tzinfo=IST).timestamp())
    return [stamp, 25366.4, 25366.4, 25366.4, 25366.4, 916.0]

class V3SourceSpacingDoctorTests(unittest.TestCase):
    def test_after_close_extra_row_is_identified_but_not_scored(self):
        result = analyze([bar(15, 29), bar(15, 34)], ["RSI 14"], "1m")
        self.assertEqual(result["bias"], "WAIT")
        self.assertEqual(result["votes"], [])
        info = result["spacing_diagnostic"]
        self.assertEqual(info["delta_seconds"], 300)
        self.assertTrue(info["regular_cash_session_boundary"])
        self.assertTrue(info["current_ist"].endswith("+05:30"))
        self.assertEqual(info["raw_dhan_provenance"], "UNVERIFIED")

    def test_in_session_missing_bar_is_distinct_and_still_waits(self):
        result = analyze([bar(14, 20), bar(14, 25)], ["EMA 9/21"], "1m")
        self.assertEqual(result["bias"], "WAIT")
        self.assertFalse(result["spacing_diagnostic"]["regular_cash_session_boundary"])
        self.assertEqual(result["spacing_diagnostic"]["expected_seconds"], 60)
        self.assertEqual(result["spacing_diagnostic"]["delta_seconds"], 300)

if __name__ == "__main__":
    unittest.main()
