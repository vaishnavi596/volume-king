"""Strength bars must not advertise NaN or infinite timestamp signals as live."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class StrengthWidgetTimestampTests(unittest.TestCase):
    def test_nonfinite_timestamp_is_historical(self):
        self.assertIn('or not math.isfinite(stamp) or not 0<=datetime.now(timezone.utc).timestamp()-stamp', SOURCE)
        self.assertIn('bull_bar_color=MUTED if historical else GREEN', SOURCE)
        self.assertIn('bear_bar_color=MUTED if historical else RED', SOURCE)

if __name__ == "__main__":
    unittest.main()
