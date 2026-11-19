import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "android_app" / "src"))
from app_state import LocalWatchlists, SelectionError
from equity_catalog import EquityCatalog


def rows(count=2785):
    return [{"symbol": "EQ%04d" % n, "name": "Company %04d" % n,
             "segment": "NSE_EQ", "security_id": n + 1}
            for n in range(count)]


class CatalogSelectionTests(unittest.TestCase):
    def test_search_entire_catalog_then_select_only_demand(self):
        catalog = EquityCatalog(rows())
        self.assertEqual(len(catalog.search("EQ2700")), 1)
        watch = LocalWatchlists()
        for i in range(5):
            catalog.add(watch, 0, "EQ%04d" % i)
        self.assertEqual(len(catalog.selected_demand(watch)), 5)
        self.assertEqual(catalog.selected_demand(watch)[0], "EQ0000")
        self.assertEqual(len(watch.groups), 5)

    def test_zero_and_seventy_boundary(self):
        catalog = EquityCatalog(rows())
        watch = LocalWatchlists()
        self.assertEqual(catalog.selected_demand(watch), ())
        for i in range(70):
            catalog.add(watch, i % 5, "EQ%04d" % i)
        self.assertEqual(len(catalog.selected_demand(watch)), 70)
        with self.assertRaises(SelectionError):
            catalog.add(watch, 0, "EQ0070")

    def test_duplicate_and_unlisted_rejection(self):
        catalog = EquityCatalog(rows(3))
        watch = LocalWatchlists()
        with self.assertRaises(SelectionError):
            catalog.add(watch, 0, "NIFTY")
        catalog.add(watch, 0, "EQ0001")
        with self.assertRaises(SelectionError):
            catalog.add(watch, 1, "EQ0001")
        with self.assertRaises(SelectionError):
            catalog.add(watch, 1, "EQ9999")

    def test_untrusted_rows_fail_closed(self):
        for wrong in (
            [{"symbol": "NIFTY", "segment": "IDX_I", "security_id": 1, "name": "Nifty"}],
            rows(1) + rows(1),
            [{"symbol": "BAD", "segment": "NSE_EQ", "security_id": -1, "name": "Bad"}],
        ):
            with self.assertRaises(ValueError):
                EquityCatalog(wrong)


if __name__ == "__main__":
    unittest.main()
