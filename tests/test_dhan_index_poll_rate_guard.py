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
        self.assertIn("await asyncio.to_thread(dhan_feed.index_batch_quotes)",code)
        self.assertNotIn("dhan_feed.quote,ticker",code)
        self.assertNotIn("asyncio.gather(",code)

    def test_closed_market_first_index_load_once_per_generation(self):
        self.assertIn("closed_index_bootstrap_generation=[None]",self.source)
        self.assertIn('closed_index_bootstrap=(not refresh_hours()',self.source)
        self.assertIn('closed_index_bootstrap_generation[0]!=provider_generation[0]',self.source)
        self.assertIn('and closed_index_bootstrap and prefs.get("source")=="Dhan"',self.source)
        self.assertIn('await refresh_dhan_index_quotes(force=True)',self.source)
        self.assertIn('closed_index_bootstrap_generation[0]=provider_generation[0]',self.source)

    def test_closed_market_equity_recovery_once_then_normal_market_poll(self):
        self.assertIn("closed_equity_bootstrap_generation=[None]",self.source)
        self.assertIn("closing_bootstrap=(not refresh_hours()",self.source)
        self.assertIn("watch_batch_success_generation[0]!=provider_generation[0]",self.source)
        self.assertIn("if received==total_symbols:",self.source)
        self.assertIn("watch_batch_success_generation[0]=generation",self.source)
        self.assertIn("login_equity_complete=",self.source)
        self.assertIn("if login_equity_complete:",self.source)
        self.assertNotIn("and not any(isinstance(quotes.get(sym),dict)",self.source)

        self.assertIn("closed_equity_bootstrap_generation[0]!=provider_generation[0]",self.source)
        self.assertIn("and closing_bootstrap and prefs.get(\"source\")==\"Dhan\"",self.source)
        self.assertIn("closed_equity_bootstrap_generation[0]=provider_generation[0]",self.source)
        self.assertIn('time.monotonic()-max(quote_auto_last_attempt[0],watch_batch_last_attempt[0])>=60',self.source)
        self.assertIn("await refresh_watch_batch()",self.source)

    def test_missing_index_message_is_not_stale_mapping_claim(self):
        fn=next(n for n in ast.walk(self.tree)
                if isinstance(n,ast.FunctionDef) and n.name=="dashboard_index_analysis")
        code=ast.get_source_segment(self.source,fn)
        self.assertIn("Index Dhan LTP unavailable",code)
        self.assertNotIn("instrument mapping not verified",code)


if __name__=="__main__":
    unittest.main()
