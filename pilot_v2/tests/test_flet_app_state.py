"""V2 Flet app-owned watchlist state: synthetic, no Flet runtime or broker."""
import importlib.util
from pathlib import Path
import unittest

FILE = Path(__file__).resolve().parents[1] / "android_app" / "src" / "app_state.py"
spec = importlib.util.spec_from_file_location("v2_app_state", FILE)
module = importlib.util.module_from_spec(spec)
import sys
sys.modules[spec.name] = module
spec.loader.exec_module(module)

class AppOwnedWatchlistTests(unittest.TestCase):
    def test_zero_five_fifty_one_seventy_and_separate_indices(self):
        for n in (0, 5, 51, 70):
            with self.subTest(n=n):
                x = module.LocalWatchlists()
                for i in range(n):
                    x.add(i % 5, f"EQ{i:03d}")
                self.assertEqual(len(x.selected), n)
                self.assertEqual(len(x.selection_payload()["watchlists"]), 5)
                self.assertEqual(module.INDEXES, ("NIFTY", "BANKNIFTY", "SENSEX"))

    def test_global_duplicate_cap_invalid_and_remove(self):
        x = module.LocalWatchlists()
        x.add(0, "TCS")
        for i in range(69):
            x.add(1, f"EQ{i:03d}")
        for index, symbol in ((4, "TCS"), (0, "NIFTY"), (2, "INFY"), (5, "SBIN"), (0, "tcs")):
            with self.subTest(symbol=symbol), self.assertRaises(module.SelectionError):
                x.add(index, symbol)
        x.remove(0, "TCS")
        x.add(4, "TCS")
        self.assertEqual(len(x.selected), 70)
        self.assertEqual(x.groups[4], ["TCS"])
        with self.assertRaises(module.SelectionError):
            x.remove(0, "TCS")

    def test_import_rejects_inconsistent_saved_lists_without_mutating_input(self):
        groups = [["TCS"], ["TCS"], [], [], []]
        with self.assertRaises(module.SelectionError):
            module.LocalWatchlists(groups)
        self.assertEqual(groups[0], ["TCS"])
        with self.assertRaises(module.SelectionError):
            module.LocalWatchlists([[]])
        with self.assertRaises(module.SelectionError):
            module.LocalWatchlists([["NIFTY"], [], [], [], []])

    def test_local_save_roundtrip_and_device_owned_snapshot(self):
        x = module.LocalWatchlists()
        x.add(0, "TCS")
        x.add(3, "INFY")
        stored = x.saved_state()
        self.assertEqual(set(stored), {"schema_version", "watchlists"})
        y = module.LocalWatchlists.from_saved(stored)
        self.assertEqual(y.groups, x.groups)
        y.add(1, "SBIN")
        self.assertNotIn("SBIN", x.selected)
        self.assertEqual(len(x.selected), 2)

    def test_corrupt_local_save_is_rejected_without_auto_repair(self):
        x = module.LocalWatchlists()
        x.add(0, "TCS")
        good = x.saved_state()
        malformed = [None, [], {}, {"schema_version": True, "watchlists": good["watchlists"]},
                     {"schema_version": 2, "watchlists": good["watchlists"]},
                     {"schema_version": 1, "watchlists": [["TCS"], ["TCS"], [], [], []]},
                     {"schema_version": 1, "watchlists": [[1], [], [], [], []]},
                     dict(good, token="forbidden")]
        for sample in malformed:
            with self.subTest(sample=repr(sample)), self.assertRaises(module.SelectionError):
                module.LocalWatchlists.from_saved(sample)
        self.assertEqual(module.LocalWatchlists.from_saved(good).selected, ("TCS",))

if __name__ == "__main__":
    unittest.main()
