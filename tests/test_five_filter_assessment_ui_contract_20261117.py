"""Independent UI-contract regression for all five assessment filter slots."""
import unittest
from shared_assessment_ui import FILTER_NAMES, assessment_lines, compact_assessment_summary


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

    def test_compact_summary_uses_same_five_validated_rows(self):
        data = {
            "symbol": "NIFTY", "source": "dhan", "freshness": "unverified",
            "live_orders_enabled": False, "signal_eligible": False,
            "collection_status": "partial_unverified",
            "assessment_filters": [
                {"id": key, "status": "available", "value": 0.84}
                if key == "pcr" else
                {"id": key, "status": "unavailable", "reason": "not_configured"}
                for key in FILTER_NAMES
            ],
            "factors": {key: {"status": "unavailable"} for key in
                        ("news", "futures", "options", "candle")}
        }
        lines = assessment_lines("NIFTY", {"NIFTY": {"fetched": 100,
                                                     "data": data}}, now=110)
        compact = compact_assessment_summary(lines)
        self.assertIn("1 context / 4 WAIT", compact)
        self.assertIn("unverified", compact)
        self.assertNotIn("Filter 6", compact)
        self.assertNotIn("BULLISH", compact)
        self.assertEqual(compact_assessment_summary(["Oracle • WAIT • missing"]),
                         "Oracle • WAIT • missing")

    def test_compact_summary_malformed_rows_fail_closed(self):
        self.assertIn("WAIT", compact_assessment_summary([]))
        self.assertIn("WAIT", compact_assessment_summary([
            "Oracle informational", "not-a-filter-row", "a", "b", "c", "d"]))
        self.assertIn("WAIT", compact_assessment_summary([
            "Oracle informational", "OI Support: WAIT", "OI Resistance: WAIT",
            "Max Pain: WAIT", "PCR: WAIT", "Candle: WAIT"]))

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
