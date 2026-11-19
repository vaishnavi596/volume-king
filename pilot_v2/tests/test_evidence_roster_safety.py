"""Fail-closed app evidence selection before accepting any market-data lane."""
import sys
import unittest
from pathlib import Path

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from evidence_inbox import DeviceEvidenceInbox


class EvidenceRosterSafety(unittest.TestCase):
    def setUp(self):
        self.inbox = DeviceEvidenceInbox()

    def test_unhashable_nonstring_duplicate_or_index_rejected_cleanly(self):
        rejected = (
            ("TCS", ["INFY"]), ("TCS", {"x": 1}), ("TCS", "TCS"),
            ("NIFTY",), ("",), (None,), tuple("EQ" + str(i) for i in range(71)),
        )
        for roster in rejected:
            with self.subTest(roster=str(roster)[:25]):
                with self.assertRaises(ValueError):
                    self.inbox.allowed(roster)
                with self.assertRaises(ValueError):
                    self.inbox.apply_candles("TCS", "3m", 1, [],
                                              selected_equities=roster,
                                              trusted_transport=True)

    def test_valid_roster_preserves_three_independent_indices(self):
        self.assertEqual(self.inbox.allowed(("TCS", "INFY")),
                         ("NIFTY", "BANKNIFTY", "SENSEX", "TCS", "INFY"))

    def test_untrusted_candles_still_fail_closed(self):
        with self.assertRaises(ValueError):
            self.inbox.apply_candles("TCS", "3m", 1, [],
                                      selected_equities=("TCS",),
                                      trusted_transport=False)


if __name__ == "__main__":
    unittest.main()
