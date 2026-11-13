"""Ensure cached option chart data is validated before rendering."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class OptionChartCacheValidationTests(unittest.TestCase):
    def test_cached_option_bars_are_normalized(self):
        source = SOURCE.read_text(encoding="utf-8")
        start = source.index("    def option_chart_panel():")
        end = source.index("    def ", start + 5)
        panel = source[start:end]
        self.assertIn("bars=clean_bars(bars)", panel)
        self.assertLess(panel.index("bars=clean_bars(bars)"), panel.index("if bars:"))
        self.assertIn("age_label(bars[-1][0])", panel)

    def test_normalizer_deduplicates_and_orders_timestamps(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn("rows[t]=(t,o,h,l,c,v)", source)
        self.assertIn("return [rows[t] for t in sorted(rows)]", source)


if __name__ == "__main__":
    unittest.main()
