"""Super Five may display already-cached exact-5m HIST rows if live ranking is empty.

No new Dhan requests, no cross-timeframe vote or fabricated live ranking.
"""
import ast
from pathlib import Path
import unittest
SRC=(Path(__file__).resolve().parents[1]/"src/main.py").read_text()
TREE=ast.parse(SRC)
def function(name):
    nodes=[n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return ast.get_source_segment(SRC,nodes[0])
class SuperFiveSavedHistory(unittest.TestCase):
    def test_source_and_timeframe_guards(self):
        code=function("super_five_card")
        for marker in ("if not rows and prefs.get(\"source\")==\"Dhan\":",
                       "sym in selected_equities", 'row.get("source")=="Dhan"',
                       'row.get("timeframe")=="5m"', 'math.isfinite(row["timestamp"])',
                       "saved_hist.sort", "rows=saved_hist[:5]"):
            self.assertIn(marker,code)
    def test_restored_rows_cannot_be_labeled_live(self):
        code=function("super_five_card")
        self.assertIn("dict(row,historical=True,live_verified=False,",code)
        self.assertIn('freshness="historical_unverified"',code)
        self.assertIn("if not rows:",code)
        self.assertIn('"DATA UNAVAILABLE"',code)
    def test_no_new_provider_calls_in_presenter(self):
        code=function("super_five_card")
        self.assertNotIn("get_market_data(",code)
        self.assertNotIn("dhan_feed.equity_quotes_for_watchlist(",code)
if __name__=="__main__":
    unittest.main()
