"""Offline source contract for optional full-Dhan-catalog Watchlist widget.

No fake catalog is installed; real authenticated producer is still required.
"""
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[1]
MAIN = ROOT / "android_app" / "src" / "main.py"


class CatalogMainWiring(unittest.TestCase):
    def test_catalog_search_is_separate_from_selected_filter(self):
        src = MAIN.read_text()
        self.assertIn('verified_catalog = [None]', src)
        self.assertIn('catalog_search = [""]', src)
        self.assertIn('label="Search Dhan equity catalog"', src)
        self.assertIn('label="Search in selected list"', src)
        self.assertIn('verified_catalog[0].search(catalog_search[0], limit=10)', src)
        self.assertIn('verified_catalog[0].add(state, group[0], item)', src)
        self.assertIn('Verified Dhan catalog not yet connected', src)
        self.assertNotIn('verified_catalog = [EquityCatalog(', src)

    def test_dhan_only_and_no_orders_from_catalog_widget(self):
        src = MAIN.read_text()
        self.assertNotIn('def fetch_catalog_from_yahoo', src)
        self.assertNotIn('def place_live_order', src)


if __name__ == "__main__":
    unittest.main()
