"""Mini charts must not silently plot invalid or unordered candle times."""
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
class MiniChartTimestampTests(unittest.TestCase):
    def test_candle_timestamps_are_valid_and_ordered(self):
        section=SOURCE.split('    def tiny_chart(sym,snapshot=None):',1)[1].split('    def help_status(',1)[0]
        self.assertIn('not math.isfinite(bar[0]) or bar[0]<=0',section)
        self.assertIn('recent[i][0]>=recent[i+1][0]',section)
        self.assertIn('return note("Chart unavailable")',section)
if __name__=="__main__":unittest.main()
