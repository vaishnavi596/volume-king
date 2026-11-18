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

if __name__ == "__main__":
    unittest.main()
