"""Independent UI-contract regression for all five assessment filter slots."""
import unittest
from shared_assessment_ui import FILTER_NAMES, assessment_lines


class AssessmentFiveSlotTests(unittest.TestCase):
    def test_all_five_unavailable_slots_keep_wait_without_fake_percentages(self):
        payload = {
            "symbol": "NIFTY",
            "live_orders_enabled": False,
            "signal_eligible": False,
            "collection_status": "partial",
            "factors": {key: {"status": "unavailable"} for key in
                        ("news", "futures", "options", "candle")},
            "assessment_filters": [{"id": key, "status": "unavailable",
                                    "reason": "not_configured"} for key in FILTER_NAMES],
        }
        lines = assessment_lines("NIFTY", {"NIFTY": {"fetched": 100, "data": payload}}, now=110)
        self.assertEqual(len(FILTER_NAMES), 5)
        for label in ("OI Support", "OI Resistance", "Max Pain", "PCR", "Candle"):
            self.assertTrue(any(line.startswith(label + ": WAIT") for line in lines), label)
        self.assertFalse(any("BULLISH %" in line or "BEARISH %" in line for line in lines))
        # Sixth slot is visible but inert; backend still sends exactly five IDs.
        self.assertEqual(lines.count("Filter 6: "), 1)
        self.assertFalse(any("Filter 6: WAIT" in line or
                             "Filter 6: 0" in line for line in lines))
        self.assertTrue(any("not a trade signal" in line for line in lines))

    def test_duplicate_filter_id_is_rejected(self):
        ids = list(FILTER_NAMES)
        ids[-1] = ids[0]
        payload = {
            "symbol": "NIFTY", "live_orders_enabled": False,
            "signal_eligible": False,
            "factors": {key: {"status": "unavailable"} for key in
                        ("news", "futures", "options", "candle")},
            "assessment_filters": [{"id": key, "status": "unavailable"} for key in ids],
        }
        lines = assessment_lines("NIFTY", {"NIFTY": {"fetched": 100, "data": payload}}, now=110)
        self.assertIn("incomplete filters", lines[0])


if __name__ == "__main__":
    unittest.main()
