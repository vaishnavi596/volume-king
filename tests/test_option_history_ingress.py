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
        # Old Angel historical premium ingress is retired in Dhan-only V3.
        self.assertIn("Dhan historical CE/PE premium candle adapter not yet available",loader)
        self.assertIn("no broker request sent",loader)
        self.assertNotIn("angel_feed.",loader)
        self.assertNotIn('market_store.put("option_chart"',loader)
        self.assertNotIn('state="AVAILABLE"',loader)


if __name__ == "__main__":
    unittest.main()
