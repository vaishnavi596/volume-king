"""FT3 offline candle/options/filter dependency gate, no invented broker data."""
import importlib.util
from pathlib import Path
import sys
import unittest

from pilot_v2.collector_readiness import ProviderCapabilities

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
def load(name):
    spec=importlib.util.spec_from_file_location("ft3_"+name,ROOT/(name+".py"))
    module=importlib.util.module_from_spec(spec)
    sys.modules[spec.name]=module
    spec.loader.exec_module(module)
    return module

candle=load("candle_history")
filters=load("filter_evidence")

def bars():
    return [
        {"timestamp":100,"open":100,"high":104,"low":99,"close":102,"volume":11,"completed":True},
        {"timestamp":200,"open":102,"high":105,"low":101,"close":103,"volume":10,"completed":True},
    ]

class FT3SourceDependencyTests(unittest.TestCase):
    def setUp(self):
        self.candles=candle.LocalCandleHistory()
        self.filters=filters.LocalFilterEvidence()

    def test_candle_history_alone_never_unlocks_option_dependent_five_filters(self):
        self.candles.accept("TCS","3m",1,bars(),allowed_symbols=("TCS",))
        self.assertEqual(self.candles.view("TCS","3m",selected_equities=("TCS",))["status"],"HIST")
        self.assertEqual([v for _,v in self.filters.rows("TCS","3m",selected_equities=("TCS",))[:5]],
                         ["WAIT"]*5)
        self.assertEqual(self.filters.rows("TCS","3m",selected_equities=("TCS",))[-1],("",""))

    def test_missing_real_option_capability_cannot_be_inferred_from_candles(self):
        cap=ProviderCapabilities(False,False,False,False,True,False,False)
        self.assertFalse(cap.observed_on_oracle)
        self.assertFalse(cap.option_chain)
        self.candles.accept("NIFTY","1m",1,bars(),allowed_symbols=("NIFTY",))
        self.assertEqual(self.candles.view("NIFTY","1m")["status"],"HIST")
        self.assertEqual(self.filters.rows("NIFTY","1m")[0][1],"WAIT")

    def test_partial_option_or_untrusted_filter_rows_do_not_clear_candles(self):
        self.candles.accept("NIFTY","1m",5,bars(),allowed_symbols=("NIFTY",))
        partial={"pcr":{"direction":"bullish","source":"dhan","observed_at":100,"eligible":True}}
        with self.assertRaises(filters.FilterEvidenceError):
            self.filters.accept("NIFTY","1m",6,partial,
                                allowed_symbols=("NIFTY",),trusted_transport=True)
        with self.assertRaises(candle.CandleEvidenceError):
            self.candles.accept("NIFTY","1m",6,[],
                                allowed_symbols=("NIFTY",))
        self.assertEqual(self.candles.view("NIFTY","1m")["count"],2)
        self.assertEqual(self.filters.rows("NIFTY","1m")[3][1],"WAIT")

    def test_no_equity_leak_after_removal(self):
        self.candles.accept("TCS","3m",1,bars(),allowed_symbols=("TCS",))
        self.candles.forget_removed(())
        self.filters.forget_removed(())
        self.assertEqual(self.candles.view("TCS","3m",selected_equities=("TCS",))["status"],"WAIT")
        self.assertEqual(self.filters.rows("TCS","3m",selected_equities=("TCS",))[0][1],"WAIT")

if __name__=="__main__":
    unittest.main()
