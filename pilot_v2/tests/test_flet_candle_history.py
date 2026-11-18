"""V2 completed-candle local cache synthetic regression; no Flet/Dhan calls."""
import importlib.util
import sys
import unittest
from pathlib import Path

file = Path(__file__).resolve().parents[1] / "android_app" / "src" / "candle_history.py"
spec = importlib.util.spec_from_file_location("v2_candle_history_test", file)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)

def bars():
    return [
        {"timestamp": 100, "open": 100, "high": 104, "low": 99,
         "close": 102, "volume": 10, "completed": True},
        {"timestamp": 200, "open": 102, "high": 106, "low": 101,
         "close": 103, "volume": 0, "completed": True},
    ]

class LocalCandleHistoryTests(unittest.TestCase):
    def test_valid_completed_history_timeframe_isolation_and_clone(self):
        c = module.LocalCandleHistory()
        self.assertEqual(c.view("NIFTY","1m")["status"],"WAIT")
        self.assertTrue(c.accept("NIFTY","1m",1,bars(),allowed_symbols=("NIFTY",)))
        self.assertEqual(c.view("NIFTY","1m")["count"],2)
        self.assertEqual(c.view("NIFTY","3m")["status"],"WAIT")
        copy=c.view("NIFTY","1m")["bars"]
        copy[0]["close"]=999
        self.assertEqual(c.view("NIFTY","1m")["bars"][0]["close"],102)
        self.assertFalse(c.accept("NIFTY","1m",1,bars(),allowed_symbols=("NIFTY",)))

    def test_bad_partial_foreign_or_out_of_order_does_not_erase_last_good(self):
        c=module.LocalCandleHistory()
        c.accept("TCS","3m",10,bars(),allowed_symbols=("TCS",))
        bads=[[], bars()[:1], [dict(b,completed=False) for b in bars()],
              [bars()[1],bars()[0]],
              [dict(b,low=300) for b in bars()],
              [dict(b,close=float("nan")) for b in bars()],
              [dict(b,volume=-1) for b in bars()]]
        for sample in bads:
            with self.subTest(data=repr(sample)[:60]),self.assertRaises(module.CandleEvidenceError):
                c.accept("TCS","3m",11,sample,allowed_symbols=("TCS",))
            self.assertEqual(c.view("TCS","3m",selected_equities=("TCS",))["count"],2)
        with self.assertRaises(module.CandleEvidenceError):
            c.accept("TCS","3m",11,bars(),allowed_symbols=("TCS",),source="yahoo")

    def test_higher_revision_with_older_last_bar_does_not_erase_history(self):
        c=module.LocalCandleHistory()
        good=bars()+[{"timestamp":300,"open":103,"high":107,"low":102,
                       "close":105,"volume":4,"completed":True}]
        self.assertTrue(c.accept("NIFTY","1m",5,good,allowed_symbols=("NIFTY",)))
        self.assertFalse(c.accept("NIFTY","1m",99,bars(),
                                  allowed_symbols=("NIFTY",)))
        self.assertEqual(c.view("NIFTY","1m")["count"],3)
        self.assertEqual(c.view("NIFTY","1m")["bars"][-1]["timestamp"],300)
        # The rejected replay must not advance the revision gate.
        self.assertTrue(c.accept("NIFTY","1m",6,good,
                                 allowed_symbols=("NIFTY",)))
        self.assertFalse(c.accept("NIFTY","1m",6,good,
                                  allowed_symbols=("NIFTY",)))
        later=good[1:]+[{"timestamp":400,"open":105,"high":108,"low":104,
                        "close":106,"volume":5,"completed":True}]
        self.assertTrue(c.accept("NIFTY","1m",7,later,
                                 allowed_symbols=("NIFTY",)))
        self.assertEqual(c.view("NIFTY","1m")["bars"][-1]["timestamp"],400)

    def test_independent_index_and_equity_timeframes_unchanged_by_replay(self):
        c=module.LocalCandleHistory()
        extended=bars()+[{"timestamp":300,"open":103,"high":107,"low":102,
                          "close":105,"volume":4,"completed":True}]
        c.accept("NIFTY","1m",50,extended,allowed_symbols=("NIFTY",))
        self.assertTrue(c.accept("NIFTY","3m",1,bars(),
                                 allowed_symbols=("NIFTY",)))
        self.assertTrue(c.accept("TCS","3m",1,bars(),
                                 allowed_symbols=("TCS",)))
        self.assertFalse(c.accept("NIFTY","1m",51,bars(),
                                  allowed_symbols=("NIFTY",)))
        self.assertEqual(c.view("NIFTY","1m")["count"],3)
        self.assertEqual(c.view("NIFTY","3m")["count"],2)
        self.assertEqual(c.view("TCS","3m",selected_equities=("TCS",))["count"],2)
        self.assertEqual(c.view("TCS","3m")["status"],"WAIT")
        self.assertEqual(c.view("BANKNIFTY","1m")["status"],"WAIT")

    def test_removed_equity_not_exposed_and_indices_remain(self):
        c=module.LocalCandleHistory()
        c.accept("TCS","3m",1,bars(),allowed_symbols=("TCS",))
        c.accept("BANKNIFTY","1m",1,bars(),allowed_symbols=("BANKNIFTY",))
        self.assertEqual(c.view("TCS","3m")["status"],"WAIT")
        c.forget_removed(())
        self.assertEqual(c.view("TCS","3m",selected_equities=("TCS",))["status"],"WAIT")
        self.assertEqual(c.view("BANKNIFTY","1m")["status"],"HIST")

if __name__=="__main__":
    unittest.main()
