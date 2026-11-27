"""Watchlist historical close must repaint independently of unchanged votes."""
import ast
import pathlib
import unittest

SOURCE=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
TREE=ast.parse(SOURCE)
def function(name):
    nodes=[n for n in ast.walk(TREE) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return ast.get_source_segment(SOURCE,nodes[0])

class WatchHistoricalCloseTick(unittest.TestCase):
    def test_history_close_is_part_of_visible_and_cell_change_signatures(self):
        src=function("watch_visible_tick")
        self.assertGreaterEqual(src.count('watch_price_and_status(sym) if prefs.get("source")=="Dhan" else None'),2)
        self.assertIn('p=watch_price_and_status(sym)[0]',src)
        self.assertIn('label=historical_status or label',src)

    def test_source_is_separate_from_live_quote(self):
        src=function("watch_price_and_status")
        self.assertIn('not dhan_offline()',src)
        self.assertNotIn('and not refresh_hours()',src)
        self.assertIn('if prefs.get("source")=="Dhan":',src)
        self.assertIn('hist_close_for_display(sym)',src)
        self.assertIn('historical_close_display',function('hist_close_for_display'))
        self.assertNotIn('quotes[sym]=',src)
        self.assertNotIn('dhan_feed.',src)

if __name__=="__main__":
    unittest.main()
