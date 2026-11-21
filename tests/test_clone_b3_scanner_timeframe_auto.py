"""B3 auto scanner selected-timeframe scheduling static guard."""
import ast
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")

class SelectedTimeframeAutoScan(unittest.TestCase):
    def test_auto_scan_does_not_permanently_skip_5m(self):
        body=SOURCE.split("    async def auto_scan_loop(generation):",1)[1].split("    scan_live.on_change=auto_scan_changed",1)[0]
        self.assertIn('dhan_history_scan_active[0]',body)
        self.assertNotIn('scan_tf.value=="5m" or dhan_history_scan_active[0]',body)
        self.assertIn("await scan_market()",body)
        self.assertIn("not refresh_hours()",body)
        self.assertIn("current[0]!=3",body)
        self.assertIn("while scan_live.value",body)
    def test_timeframe_options_cover_user_choices(self):
        self.assertIn('["1m","2m","3m","5m","10m","15m","30m","1h"]',SOURCE)
        ast.parse(SOURCE)

if __name__=="__main__":
    unittest.main()
