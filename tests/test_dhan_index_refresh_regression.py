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

    def test_equity_and_index_poll_are_both_scheduled(self):
        fn = next(node for node in ast.walk(self.tree)
                  if isinstance(node, ast.AsyncFunctionDef) and node.name == "dhan_quote_poll")
        source = ast.get_source_segment(self.source, fn)
        self.assertIn("await refresh_watch_batch()", source)
        self.assertIn("await refresh_dhan_index_quotes()", source)
        self.assertIn("await asyncio.sleep(10 if not dhan_feed.connected else 30)", source)


if __name__ == "__main__":
    unittest.main()
