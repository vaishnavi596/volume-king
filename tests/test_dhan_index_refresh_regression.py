"""Index refresh must be independent of 51-equity snapshot and retain old quotes."""
import ast
import unittest
from pathlib import Path


class DhanIndexRefreshRegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_index_poll_has_three_symbols_and_last_good_retention(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "refresh_dhan_index_quotes")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn('("NIFTY", "BANKNIFTY", "SENSEX")', source)
        self.assertIn("await asyncio.to_thread(dhan_feed.index_batch_quotes)", source)
        self.assertNotIn("dhan_feed.quote,ticker", source)
        self.assertIn('old.get("bars",[])', source)
        self.assertIn('freshness="unverified"', source)
        self.assertIn("generation!=provider_generation[0]", source)

    def test_clone_gateway_index_errors_have_distinct_sanitized_codes(self):
        # The phone must report which Clone stage failed without exposing
        # secret keys, request URLs or arbitrarily supplied upstream bodies.
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "refresh_dhan_index_quotes")
        source = ast.get_source_segment(self.source, fn)
        for code, detail in (
            ("GATEWAY_HTTP_429", "quote lane paced"),
            ("AUTH_OR_ACCESS_403", "session rejected"),
            ("INDEX_BATCH_SCHEMA_REJECTED", "no validated quotes"),
            ("CLONE_GATEWAY_TRANSPORT_UNAVAILABLE", "clone market data unavailable"),
            ("CLONE_MARKET_ROUTE_UNAVAILABLE", "clone market route not ready"),
        ):
            with self.subTest(code=code):
                self.assertIn('"' + code + '"', source)
                self.assertIn('"' + detail + '"', source)
        self.assertIn('"UNCLASSIFIED_FEED_ERROR"', source)
        self.assertIn("diagnostic=str(exc).lower()", source)
        self.assertIn("index_last_result_generation[0]=generation", source)

    def test_doctor_reports_actual_clone_index_route_not_legacy_path(self):
        # Do not direct an operator to the obsolete V1 /dhan index HTTP path.
        self.assertIn('"route":"/clone-v2/market/quotes"', self.source)
        self.assertIn('"/clone-v2/market/quotes",', self.source)
        self.assertIn('src/clone_v2_gateway.py:CloneDhanReadOnly.index_batch_quotes', self.source)
        self.assertIn('actual /clone-v2/market/quotes three-index request', self.source)
        # Legacy cooldown keys can remain internal for compatibility.
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/index-ltp-batch")', self.source)

    def test_index_poll_is_not_blocked_by_equity_snapshot(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_quote_poll")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn('and not watch_batch_busy[0]):', source)
        index_fn = next(node for node in ast.walk(self.tree)
                        if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_index_poll")
        index_source = ast.get_source_segment(self.source, index_fn)
        self.assertIn('and dhan_feed.connected and not index_refresh_busy[0]):', index_source)
        self.assertIn('await refresh_dhan_index_quotes()', index_source)
        self.assertNotIn('await refresh_watch_batch()', index_source)
        self.assertIn('time.monotonic()-max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])>=60', source)

    def test_invalid_index_quote_retains_last_valid_price_but_downgrades_freshness(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "refresh_dhan_index_quotes")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn('snapshot={}', source)
        self.assertIn('provider_status="provider_data_unavailable"', source)
        self.assertIn('freshness="unverified",live_verified=False', source)
        self.assertIn('price=snapshot.get("price")', source)
        self.assertIn('else:\n                    # An invalid OR missing response', source)

    def test_index_candles_are_prioritized_and_reused(self):
        source = self.source
        self.assertIn('symbols=([equities[0]]+indices+equities[1:]) if equities else indices', source)
        self.assertIn('if index_sym in cycle_data:', source)
        self.assertIn('cycle_data[early_index]=early_data', source)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/intraday")>0', source)

    def test_index_candle_timer_is_paced_and_generation_safe(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_index_candle_poll")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn('time.monotonic()-index_candle_last_attempt[0]>=180', source)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/intraday")==0', source)
        self.assertIn('not lifecycle_background[0]', source)
        self.assertIn('generation!=provider_generation[0]', source)
        self.assertIn('market_recent.get(history_key)', source)
        self.assertIn('await asyncio.sleep(1.5)', source)
        self.assertIn('asyncio.to_thread(get_market_data,index_sym,"1m","2d")', source)
        self.assertIn('page.run_task(dhan_index_candle_poll)', self.source)

    def test_index_candle_timer_respects_explicit_scan_lifecycle(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_index_candle_poll")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn("and not dhan_history_scan_active[0]", source)
        self.assertIn("or dhan_history_scan_active[0]", source)
        market = next(node for node in ast.walk(self.tree)
                      if isinstance(node, ast.AsyncFunctionDef) and node.name == "refresh_market")
        market_source = ast.get_source_segment(self.source, market)
        self.assertIn('dhan_history_scan_active[0]=(prefs.get("source")=="Dhan")', market_source)
        self.assertIn("dhan_history_scan_active[0]=False", market_source)
        supervisor = next(node for node in ast.walk(self.tree)
                          if isinstance(node, ast.AsyncFunctionDef) and node.name == "supervised_market_refresh")
        self.assertIn("finally:", ast.get_source_segment(self.source, supervisor))
        self.assertIn("dhan_history_scan_active[0]=False",
                      ast.get_source_segment(self.source, supervisor))

    def test_dhan_selected_timeframes_wait_for_shared_provider_queue(self):
        source = self.source
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "auto_scan_loop")
        body = ast.get_source_segment(source, fn)
        # Block only while the shared historical provider queue is active.
        # A selected 5m scan need not be permanently disabled when queue is idle.
        self.assertIn('if prefs.get("source")=="Dhan" and dhan_history_scan_active[0]:', body)
        self.assertNotIn('scan_tf.value=="5m" or dhan_history_scan_active[0]', body)
        self.assertIn('await asyncio.sleep(5)', body)

    def test_equity_and_index_poll_are_both_scheduled(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_quote_poll")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn("await refresh_watch_batch()", source)
        index_fn = next(node for node in ast.walk(self.tree)
                        if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_index_poll")
        self.assertIn("await refresh_dhan_index_quotes()", ast.get_source_segment(self.source, index_fn))
        self.assertIn("page.run_task(dhan_index_poll)", self.source)
        self.assertIn("await asyncio.sleep(10 if not dhan_feed.connected else 10)", source)


if __name__ == "__main__":
    unittest.main()
