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

    def test_index_poll_is_not_blocked_by_equity_snapshot(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_quote_poll")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn('and not watch_batch_busy[0]):', source)
        self.assertIn('and dhan_feed.connected and not index_refresh_busy[0]):', source)
        self.assertIn('await refresh_dhan_index_quotes()', source)
        self.assertIn('time.monotonic()-quote_auto_last_attempt[0]>=60', source)

    def test_index_candles_are_prioritized_and_reused(self):
        source = self.source
        self.assertIn('symbols=([equities[0]]+indices+equities[1:]) if equities else indices', source)
        self.assertIn('if index_sym in cycle_data:', source)
        self.assertIn('cycle_data[early_index]=early_data', source)
        self.assertIn('dhan_feed.cooldown_remaining("/dhan/intraday")>0', source)

    def test_dhan_has_no_second_automatic_scanner(self):
        source = self.source
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "auto_scan_loop")
        body = ast.get_source_segment(source, fn)
        self.assertIn('if prefs.get("source")=="Dhan":', body)
        self.assertIn('await asyncio.sleep(5)', body)

    def test_equity_and_index_poll_are_both_scheduled(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_quote_poll")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn("await refresh_watch_batch()", source)
        self.assertIn("await refresh_dhan_index_quotes()", source)
        self.assertIn("await asyncio.sleep(10 if not dhan_feed.connected else 10)", source)


if __name__ == "__main__":
    unittest.main()
