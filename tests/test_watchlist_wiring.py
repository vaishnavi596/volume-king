"""Offline watchlist wiring regression checks (no broker or UI session required)."""
import ast
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class WatchlistWiringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.functions = {
            node.name: node
            for node in ast.walk(cls.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def test_five_independent_persisted_lists(self):
        self.assertIn('for i in range(1,6)', self.source)
        self.assertIn('prefs["watchlist_"+str(i)]', self.source)
        self.assertIn('for i,group in enumerate(watch_groups,1)', self.source)

    def test_add_captures_target_list_before_async_work(self):
        add = ast.get_source_segment(self.source, self.functions["add_watch"])
        validate = self.functions["validate_and_add"]
        self.assertEqual([arg.arg for arg in validate.args.args], ["sym", "target_list"])
        self.assertIn("target_list=active_watch[0]", add)
        self.assertIn("page.run_task(validate_and_add,sym,target_list)", add)
        body = ast.get_source_segment(self.source, validate)
        self.assertIn("watch_groups[target_list]", body)
        self.assertIn("if active_watch[0]==target_list:", body)
        self.assertIn("if sym not in watch_symbols:", body)

    def test_remove_is_list_scoped_and_persisted(self):
        remove = ast.get_source_segment(self.source, self.functions["remove_stock"])
        self.assertIn("watch_groups[active_watch[0]]", remove)
        self.assertIn("group.remove(sym)", remove)
        self.assertIn("store_watch()", remove)

    def test_search_filter_and_chart_click_wired(self):
        self.assertIn("search.on_change=fill_watch", self.source)
        self.assertIn("watch_filter[0]!=direction", self.source)
        self.assertIn("on_click=lambda e,v=sym:open_stock(v)", self.source)
        self.assertIn("on_click=lambda e,v=sym:remove_stock(v)", self.source)

    def test_dhan_client_allows_only_verified_watchlist_symbols(self):
        feed = (SOURCE.parent / "server_feed.py").read_text(encoding="utf-8")
        allowed = '("NIFTY", "RELIANCE", "HDFCBANK", "ICICIBANK")'
        self.assertIn("if symbol not in " + allowed + ":", feed)
        self.assertIn("if symbol not in " + allowed + " or interval not in", feed)
        self.assertIn('quote_timestamp": None', feed)
        self.assertIn('"freshness": "unverified"', feed)

    def test_known_symbols_are_unique(self):
        assign = next(node for node in ast.walk(self.tree)
                      if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "watch_symbols"
                              for t in node.targets))
        symbols = ast.literal_eval(assign.value)
        self.assertEqual(len(symbols), 50)
        self.assertEqual(len(set(symbols)), len(symbols))


if __name__ == "__main__":
    unittest.main()
