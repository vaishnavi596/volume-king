"""Unknown providers must never silently fall through to Angel One."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class ExplicitProviderSelectionTests(unittest.TestCase):
    def test_angel_history_requires_explicit_broker_selection(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("    def fetch_market_data_uncached(")
        end = source.index("    def ", start + 5)
        body = source[start:end]
        self.assertIn('elif selected=="Broker API" and angel_feed.connected:', body)
        self.assertNotIn('elif angel_feed.connected:', body)
        self.assertIn('elif selected=="Dhan":', body)
        self.assertIn('if selected=="Yahoo Finance":', body)


if __name__ == "__main__":
    unittest.main()
