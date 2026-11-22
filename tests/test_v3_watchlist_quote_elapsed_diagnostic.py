"""Watchlist local elapsed time diagnostic: source-contract, no Dhan calls."""
import ast
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
TREE=ast.parse(SOURCE)

def function(name):
    funcs=[n for n in ast.walk(TREE) if isinstance(n,ast.AsyncFunctionDef)
           and n.name==name]
    if len(funcs)!=1:raise AssertionError(name)
    return ast.get_source_segment(SOURCE,funcs[0])

class WatchlistElapsedDiagnostics(unittest.TestCase):
    def test_measure_only_local_real_work(self):
        s=function("refresh_watch_batch")
        self.assertIn('watch_batch_last_attempt[0]=time.monotonic()',s)
        self.assertIn('await asyncio.to_thread(dhan_feed.equity_quotes_for_watchlist,requested_symbols)',s)
        self.assertIn('watch_batch_last_duration_ms[0]=round(',s)
        self.assertIn('max(0.0,time.monotonic()-watch_batch_last_attempt[0])*1000,1)',s)
        self.assertIn('if generation==provider_generation[0]:',s)
        self.assertIn('watch_batch_last_result[0]="FAILED"',s)
        self.assertIn('"COMPLETE" if received==total_symbols else "PARTIAL"',s)
        self.assertNotIn('dhan_feed.market_quotes(',s)
    def test_diagnostic_reports_duration_without_faking_live(self):
        self.assertIn('"equity_last_local_duration_ms":watch_batch_last_duration_ms[0]',SOURCE)
        self.assertIn('"equity_last_result":watch_batch_last_result[0]',SOURCE)
        self.assertIn('watch_batch_last_duration_ms=[None]',SOURCE)
        self.assertIn('watch_batch_last_result=["NOT_ATTEMPTED"]',SOURCE)

if __name__=="__main__":
    unittest.main()
