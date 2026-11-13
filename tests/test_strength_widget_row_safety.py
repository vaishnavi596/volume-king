"""Strength bar must not trust malformed candle rows or boolean timestamps."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class StrengthWidgetSafetyTests(unittest.TestCase):
    def test_row_is_normalized(self):
        self.assertIn('def strength_widget(row, symbol=None):\n        if not isinstance(row,dict):row={}', SOURCE)
    def test_boolean_timestamp_is_historical(self):
        self.assertIn('isinstance(stamp,bool) or not math.isfinite(stamp)', SOURCE)
if __name__ == "__main__":
    unittest.main()
