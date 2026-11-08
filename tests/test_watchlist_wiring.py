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
        self.assertIn("DHAN_VERIFIED_SYMBOLS = frozenset(", feed)
        self.assertIn("if symbol not in DHAN_VERIFIED_SYMBOLS:", feed)
        self.assertIn("if symbol not in DHAN_VERIFIED_SYMBOLS or interval not in", feed)
        self.assertIn('quote_timestamp": None', feed)
        self.assertIn('"freshness": "unverified"', feed)

    def test_dhan_batch_ltp_survives_history_refresh(self):
        self.assertIn('latest=dhan_batch_cache["quotes"].get(sym)', self.source)
        self.assertIn('data=dict(data,price=latest["price"],quote_timestamp=None,', self.source)
        self.assertIn('freshness="unverified",fetched_at=time.time())', self.source)

    def test_dhan_connect_settings_displays_partial_count(self):
        self.assertIn('" equity LTP quotes returned • timestamps unverified"+',self.source)
        self.assertIn('(" • PARTIAL" if dhan_batch_issue[0] else "")',self.source)
        self.assertIn('connection_status.color=GOLD if dhan_batch_issue[0] else GREEN',self.source)

    def test_dhan_connect_keeps_batch_in_new_scan_generation(self):
        self.assertIn('dhan_batch_cache["generation"]=provider_generation[0]',self.source)
        self.assertIn('provider_generation[0]+=1',self.source)
        connect=self.source.index('dhan_batch_cache.update(generation=provider_generation[0]')
        bump=self.source.index('provider_generation[0]+=1',connect)
        keep=self.source.index('dhan_batch_cache["generation"]=provider_generation[0]',bump)
        self.assertLess(connect,bump)
        self.assertLess(bump,keep)

    def test_dhan_connect_fetches_watchlist_batch(self):
        self.assertIn('batch=await asyncio.to_thread(dhan_feed.batch_quotes)', self.source)
        self.assertIn("log_error('dhan_batch_after_connect',exc)", self.source)
        self.assertIn('failed_symbols.clear()', self.source)

    def test_batch_quote_health_is_not_overwritten_by_candle_failures(self):
        self.assertIn('batch_count=len(dhan_batch_cache["quotes"])', self.source)
        self.assertIn('historical candles unavailable', self.source)
        self.assertIn('watchlist batch failed:', self.source)

    def test_known_symbols_are_unique(self):
        assign = next(node for node in ast.walk(self.tree)
                      if isinstance(node, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == "watch_symbols"
                              for t in node.targets))
        symbols = ast.literal_eval(assign.value)
        self.assertEqual(len(symbols), 51)
        self.assertEqual(len(set(symbols)), len(symbols))


if __name__ == "__main__":
    unittest.main()
