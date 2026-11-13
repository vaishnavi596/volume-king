"""Unspecified market source must not silently select Yahoo."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class DhanMarketDefaultTests(unittest.TestCase):
    def test_uncached_market_source_defaults_to_dhan(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("    def fetch_market_data_uncached(")
        end = source.index("    def ", start + 5)
        body = source[start:end]
        self.assertIn('selected=prefs.get("source","Dhan")', body)
        self.assertNotIn('selected=prefs.get("source","Yahoo Finance")', body)
        self.assertIn('elif selected=="Dhan":', body)


if __name__ == "__main__":
    unittest.main()
