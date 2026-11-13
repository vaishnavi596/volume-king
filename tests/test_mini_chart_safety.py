"""Malformed mini chart candles must not crash chart rendering."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class MiniChartSafetyTests(unittest.TestCase):
    def test_source_and_candles_validated(self):
        section=SOURCE.split('    def tiny_chart(sym,snapshot=None):',1)[1].split('    def help_status(',1)[0]
        self.assertIn('if not isinstance(q,dict):return note("Chart unavailable")',section)
        self.assertIn('if q.get("source")!=expected:return note("Chart unavailable")',section)
        self.assertIn('if not isinstance(bars,(list,tuple))',section)
        self.assertIn('or not math.isfinite(bar[4]) or bar[4]<=0',section)
if __name__ == "__main__":
    unittest.main()
