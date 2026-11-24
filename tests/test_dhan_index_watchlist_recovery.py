"""Watchlist index cards must update on manual refresh and Android resume."""
import ast
import unittest
from pathlib import Path


class DhanIndexWatchlistRecovery(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.source)

    def function(self,name):
        node=next(n for n in ast.walk(self.tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name)
        return ast.get_source_segment(self.source,node)

    def test_manual_refresh_includes_indexes(self):
        s=self.function("refresh_all_dhan_quotes")
        self.assertIn("await refresh_watch_batch()",s)
        self.assertIn("await refresh_dhan_index_quotes()",s)
        self.assertIn("page.run_task(refresh_all_dhan_quotes)",self.function("watchlist"))

    def test_resume_refreshes_indexes(self):
        s=self.function("refresh_after_resume")
        self.assertIn("await refresh_watch_batch()",s)
        self.assertIn("await refresh_dhan_index_quotes()",s)

    def test_watchlist_change_detection_includes_indexes(self):
        self.assertIn('visible=tuple(watch_groups[active_watch[0]])+("NIFTY","BANKNIFTY","SENSEX")',
                      self.function("watch_visible_tick"))
        self.assertIn('index_symbols=("NIFTY", "BANKNIFTY", "SENSEX")',self.function("watchlist"))


if __name__=="__main__":
    unittest.main()
