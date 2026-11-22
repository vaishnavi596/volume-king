"""B2 offline priority tests. No broker connection or auto trade."""
import ast
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from clone_smart_refresh_priority import focused_contexts, priority_equity_batch, accept_newer_dhan_quote


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

    def test_priority_quotes_include_positions_even_outside_watchlist(self):
        self.assertEqual(
            priority_equity_batch(["HDFCBANK","RELIANCE"], ["TCS","RELIANCE"],
                                  verified={"TCS","RELIANCE","HDFCBANK","NIFTY"}),
            ["TCS","RELIANCE","HDFCBANK"])
        self.assertEqual(priority_equity_batch([],[],verified={"RELIANCE"}),[])

    def test_quote_budget_dedup_indices_and_cap(self):
        self.assertEqual(priority_equity_batch(["RELIANCE","HDFCBANK"],
                                               ["NIFTY","TCS","TCS"],
                                               verified={"NIFTY","TCS","RELIANCE","HDFCBANK"},
                                               limit=2),["TCS","RELIANCE"])
        source=(ROOT/"src/main.py").read_text()
        self.assertIn('requested_symbols=priority_equity_batch(',source)
        self.assertIn('dhan_feed.equity_quotes_for_watchlist,requested_symbols',source)
        self.assertIn('if not requested_symbols:',source)

    def test_chart_only_assessment_skipped_no_wrong_timeframe(self):
        source=(ROOT/"src/main.py").read_text()
        ast.parse(source)
        self.assertIn('selected=focused_contexts(',source)
        self.assertIn('if surface=="chart":',source)
        self.assertIn('timeframe=None',source)
        self.assertNotIn('selected=[("overview",index_symbol)',source)


    def test_timestamp_guard_prevents_old_quote_overwriting_new(self):
        last={"source":"Dhan","price":104.0,"quote_timestamp":1800000010}
        self.assertFalse(accept_newer_dhan_quote(last,{"source":"Dhan","price":100.0,"quote_timestamp":1800000009}))
        self.assertFalse(accept_newer_dhan_quote(last,{"source":"Dhan","price":100.0,"quote_timestamp":None}))
        self.assertTrue(accept_newer_dhan_quote(last,{"source":"Dhan","price":106.0,"quote_timestamp":1800000011}))
        self.assertTrue(accept_newer_dhan_quote({"source":"Dhan","price":100},{"source":"Dhan","price":101}))
        for bad in (None,0,True,-1,float("nan"),float("inf")):
            self.assertFalse(accept_newer_dhan_quote({},{"source":"Dhan","price":bad}))
        self.assertFalse(accept_newer_dhan_quote({},{"source":"Yahoo Finance","price":100}))

    def test_revision_guard_is_on_both_login_and_batch_paths(self):
        source=(ROOT/"src/main.py").read_text(encoding="utf-8")
        self.assertIn("if ticker in requested_symbols and accept_newer_dhan_quote(quotes.get(ticker),snapshot):",source)
        self.assertIn("if accept_newer_dhan_quote(quotes.get(symbol),candidate):",source)
        self.assertIn("auto_equity_quote_due(",source)
        self.assertIn("active_quote_view(current[0])",source)

if __name__ == "__main__":
    unittest.main()
