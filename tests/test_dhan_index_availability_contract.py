"""Regression guard: Dhan index availability must match returned valid quotes."""
import ast
import unittest
from pathlib import Path


class IndexAvailabilityContract(unittest.TestCase):
    def test_partial_provider_response_is_validated(self):
        source = (Path(__file__).resolve().parents[1] / "src" / "server_feed.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        method = next(n for n in ast.walk(tree)
                      if isinstance(n, ast.FunctionDef) and n.name == "index_batch_quotes")
        code = ast.get_source_segment(source, method)
        self.assertIn('result.get("unavailable")', code)
        self.assertIn("set(unavailable).intersection(quotes)", code)
        self.assertIn("set(unavailable).union(quotes) != DHAN_VERIFIED_INDEX_SYMBOLS", code)
        self.assertIn('raise FeedError("Inconsistent Dhan index availability response")', code)
        self.assertIn('raise FeedError("No valid Dhan index batch quotes")', code)


if __name__ == "__main__":
    unittest.main()
