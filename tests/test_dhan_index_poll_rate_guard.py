"""Batch 1 safety: index LTP refresh must not overlap or flood the Dhan gateway."""
import ast
import unittest
from pathlib import Path


class IndexPollRateGuard(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        cls.tree=ast.parse(cls.source)

    def test_serialized_and_bounded(self):
        fn=next(n for n in ast.walk(self.tree)
                if isinstance(n,ast.AsyncFunctionDef) and n.name=="refresh_dhan_index_quotes")
        code=ast.get_source_segment(self.source,fn)
        self.assertIn("if index_refresh_busy[0]:",code)
        self.assertIn("now-index_last_attempt[0]<60",code)
        self.assertIn("index_refresh_generation[0]==generation",code)
        self.assertIn('for ticker in ("NIFTY", "BANKNIFTY", "SENSEX"):',code)
        self.assertIn("index_refresh_busy[0]=False",code)
        self.assertIn("finally:",code)
        self.assertIn("await asyncio.to_thread(dhan_feed.quote,ticker)",code)
        self.assertNotIn("asyncio.gather(",code)

    def test_missing_index_message_is_not_stale_mapping_claim(self):
        fn=next(n for n in ast.walk(self.tree)
                if isinstance(n,ast.FunctionDef) and n.name=="dashboard_index_analysis")
        code=ast.get_source_segment(self.source,fn)
        self.assertIn("Index Dhan LTP unavailable",code)
        self.assertNotIn("instrument mapping not verified",code)


if __name__=="__main__":
    unittest.main()
