"""Option premium history must be validated before it enters shared caches."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class OptionHistoryIngressTests(unittest.TestCase):
    def test_history_normalized_before_cache_and_freshness(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("    async def load_option_history():")
        end = source.index("    def option_chart_panel():", start)
        loader = source[start:end]
        self.assertIn("bars=clean_bars(raw_bars)", loader)
        self.assertLess(loader.index("bars=clean_bars(raw_bars)"), loader.index('market_store.put("option_chart"'))
        self.assertLess(loader.index("bars=clean_bars(raw_bars)"), loader.index('state="AVAILABLE"'))
        self.assertIn('if len(bars)<2:raise FeedError("Not enough valid option candles")', loader)


if __name__ == "__main__":
    unittest.main()
