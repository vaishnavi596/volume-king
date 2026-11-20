"""B2 offline priority tests. No broker connection or auto trade."""
import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from clone_smart_refresh_priority import focused_contexts


class TestB2Priority(unittest.TestCase):
    def test_dashboard_focus_only_index(self):
        self.assertEqual(focused_contexts(0, indices=("NIFTY","BANKNIFTY","SENSEX"),
                                          scanner="HDFCBANK",option="RELIANCE"),
                         [("overview","NIFTY"),("overview","BANKNIFTY"),
                          ("overview","SENSEX")])

    def test_inactive_scanner_pauses_but_position_stays(self):
        self.assertEqual(focused_contexts(4,indices=("NIFTY",),scanner="ICICIBANK",
                                          watch="HDFCBANK",trading=("RELIANCE",)),
                         [("watchlist","HDFCBANK"),("overview","RELIANCE")])

    def test_dedupe_paper_priority_without_all_seventy(self):
        self.assertEqual(focused_contexts(3,indices=("NIFTY",),scanner="HDFCBANK",
                                          trading=("HDFCBANK","HDFCBANK")),
                         [("scanner","HDFCBANK"),("overview","HDFCBANK")])

    def test_inactive_screen_suspends_expensive_local_loops(self):
        source=(ROOT/"src/main.py").read_text()
        ast.parse(source)
        self.assertIn('if not app_active[0] or current[0]!=0:',source)
        self.assertIn('if regular_hours() and app_active[0] and current[0] in (0,3):',source)
        self.assertIn('refresh_shared_analysis(only=scan_symbol.value if current[0]==3 else None)',source)
        self.assertIn('if current[0]!=3:', source)
        self.assertIn('scan_next_refresh[0]=None', source)
        self.assertIn('await asyncio.sleep(2 if app_active[0] and current[0] in (0,3) else 30)',source)

    def test_chart_only_assessment_skipped_no_wrong_timeframe(self):
        source=(ROOT/"src/main.py").read_text()
        ast.parse(source)
        self.assertIn('selected=focused_contexts(',source)
        self.assertIn('if surface=="chart":',source)
        self.assertIn('timeframe=None',source)
        self.assertNotIn('selected=[("overview",index_symbol)',source)


if __name__ == "__main__":
    unittest.main()
