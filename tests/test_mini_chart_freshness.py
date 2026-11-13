"""Historical or disconnected Dhan mini chart cannot appear live."""
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
class MiniChartFreshnessTests(unittest.TestCase):
    def test_dhan_chart_historical_or_offline(self):
        section=SOURCE.split('    def tiny_chart(sym,snapshot=None):',1)[1].split('    def help_status(',1)[0]
        self.assertIn('prefs.get("source")=="Dhan" and (dhan_offline() or q.get("historical"))',section)
        self.assertIn('return note("Chart cached / unverified")',section)
if __name__=="__main__":unittest.main()
