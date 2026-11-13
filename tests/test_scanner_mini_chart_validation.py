"""Guard the scanner mini chart against invalid persisted candle data."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class MiniChartValidationTests(unittest.TestCase):
    def test_mini_chart_normalizes_before_truncating(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('bars=clean_bars(hist.get("bars") or [])[-35:]', source)
        self.assertNotIn('bars=(hist.get("bars") or [])[-35:]', source)

    def test_clean_bars_checks_ohlc_and_sorts_timestamps(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertIn('if t>0 and all(math.isfinite(x) and x>0', source)
        self.assertIn('rows[t]=(t,o,h,l,c,v)', source)
        self.assertIn('return [rows[t] for t in sorted(rows)]', source)


if __name__ == "__main__":
    unittest.main()
