"""Strength bars must not color cached cross-provider votes as live."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class StrengthWidgetSourceTests(unittest.TestCase):
    def test_historical_on_provider_source_mismatch(self):
        self.assertIn('historical=row.get("historical") or row.get("source")!=({"Broker API":"Angel One","Dhan":"Dhan"}.get(prefs.get("source"),"Yahoo Finance"))', SOURCE)
        self.assertIn('bull_bar_color=MUTED if historical else GREEN', SOURCE)
if __name__ == "__main__":
    unittest.main()
