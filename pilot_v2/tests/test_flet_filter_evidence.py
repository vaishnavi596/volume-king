"""Offline source-gated filter display with inert sixth slot."""
import importlib.util
import sys
from pathlib import Path
import unittest

p = Path(__file__).resolve().parents[1] / "android_app" / "src" / "filter_evidence.py"
spec = importlib.util.spec_from_file_location("v2_filter_evidence_test",p)
m = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = m
spec.loader.exec_module(m)

def sample():
    return {key: {"direction":"bullish","source":"dhan","observed_at":1730000000,
                  "eligible":True} for key in m.FILTER_KEYS}

class FilterEvidenceTests(unittest.TestCase):
    def test_default_five_wait_sixth_blank_and_no_percentages(self):
        state=m.LocalFilterEvidence()
        rows=state.rows("NIFTY","1m")
        self.assertEqual(len(rows),6)
        self.assertEqual([s for _,s in rows[:5]],["WAIT"]*5)
        self.assertEqual(rows[5],("",""))
        self.assertFalse(any("%" in val for _, val in rows))

    def test_untrusted_partial_or_invalid_payload_never_activates(self):
        state=m.LocalFilterEvidence()
        v=sample()
        with self.assertRaises(m.FilterEvidenceError):
            state.accept("NIFTY","1m",1,v,allowed_symbols=("NIFTY",))
        with self.assertRaises(m.FilterEvidenceError):
            state.accept("NIFTY","1m",1,{"pcr":v["pcr"]},allowed_symbols=("NIFTY",),trusted_transport=True)
        invalid=sample()
        invalid["news"]={"direction":"bullish","source":"dhan","observed_at":1,"eligible":True}
        with self.assertRaises(m.FilterEvidenceError):
            state.accept("NIFTY","1m",1,invalid,allowed_symbols=("NIFTY",),trusted_transport=True)
        for change in ({"eligible":False},{"source":"rss"},{"observed_at":0},{"direction":"WAIT"}):
            bad=sample()
            bad["pcr"].update(change)
            with self.subTest(change=change),self.assertRaises(m.FilterEvidenceError):
                state.accept("NIFTY","1m",1,bad,allowed_symbols=("NIFTY",),trusted_transport=True)
        self.assertEqual(state.rows("NIFTY","1m")[0][1],"WAIT")

    def test_complete_trusted_snapshot_is_history_only_last_good(self):
        state=m.LocalFilterEvidence()
        self.assertTrue(state.accept("TCS","3m",2,sample(),allowed_symbols=("TCS",),trusted_transport=True))
        self.assertFalse(state.accept("TCS","3m",1,sample(),allowed_symbols=("TCS",),trusted_transport=True))
        self.assertEqual(state.rows("TCS","3m",selected_equities=("TCS",))[0][1],"BULLISH HIST")
        self.assertEqual(state.rows("TCS","1m",selected_equities=("TCS",))[0][1],"WAIT")
        self.assertEqual(state.rows("TCS","3m")[0][1],"WAIT")
        with self.assertRaises(m.FilterEvidenceError):
            state.accept("TCS","3m",3,{"pcr":sample()["pcr"]},allowed_symbols=("TCS",),trusted_transport=True)
        self.assertEqual(state.rows("TCS","3m",selected_equities=("TCS",))[0][1],"BULLISH HIST")
        state.forget_removed(())
        self.assertEqual(state.rows("TCS","3m",selected_equities=("TCS",))[0][1],"WAIT")
        self.assertEqual(state.rows("TCS","3m")[-1],("",""))

    def test_separate_filter_evidence_allows_one_valid_and_four_wait(self):
        state=m.LocalFilterEvidence()
        factor=sample()
        with self.assertRaises(m.FilterEvidenceError):
            state.accept_available("NIFTY","1m",4,{"pcr":factor["pcr"]},
                                   allowed_symbols=("NIFTY",))
        self.assertTrue(state.accept_available("NIFTY","1m",200,
                        {"pcr":factor["pcr"]},allowed_symbols=("NIFTY",),
                        trusted_transport=True))
        result=state.rows("NIFTY","1m")
        self.assertEqual([v for _,v in result[:5]],
                         ["WAIT","WAIT","WAIT","BULLISH HIST","WAIT"])
        self.assertEqual(result[-1],("",""))
        self.assertTrue(state.accept_available("NIFTY","1m",1,
                        {"candle_trend":factor["candle_trend"]},
                        allowed_symbols=("NIFTY",),trusted_transport=True))
        self.assertEqual(state.rows("NIFTY","1m")[4][1],"BULLISH HIST")
        self.assertFalse(state.accept_available("NIFTY","1m",199,
                        {"pcr":factor["pcr"]},allowed_symbols=("NIFTY",),
                        trusted_transport=True))
        self.assertEqual(state.rows("NIFTY","1m")[3][1],"BULLISH HIST")

    def test_partial_invalid_is_atomic_and_removed_symbol_is_wait(self):
        state=m.LocalFilterEvidence()
        good=sample()
        state.accept_available("TCS","3m",1,{"pcr":good["pcr"]},
                               allowed_symbols=("TCS",),trusted_transport=True)
        wrong=dict(good["candle_trend"],eligible=False)
        for proposed in ({"candle_trend":wrong, "oi_support":good["oi_support"]},
                         {"news":good["pcr"]}, {}):
            with self.subTest(proposed=proposed),self.assertRaises(m.FilterEvidenceError):
                state.accept_available("TCS","3m",2,proposed,
                          allowed_symbols=("TCS",),trusted_transport=True)
        self.assertEqual(state.rows("TCS","3m",selected_equities=("TCS",))[3][1],
                         "BULLISH HIST")
        self.assertEqual(state.rows("TCS","3m",selected_equities=("TCS",))[0][1],
                         "WAIT")
        self.assertNotIn("%",state.compact("TCS","3m",selected_equities=("TCS",)))
        state.forget_removed(())
        self.assertEqual([v for _,v in state.rows("TCS","3m",selected_equities=("TCS",))[:5]],
                         ["WAIT"]*5)

    def test_same_five_filter_engine_renders_watchlist_compact(self):
        state=m.LocalFilterEvidence()
        self.assertEqual(state.compact("TCS","3m",selected_equities=("TCS",)),
                         "TCS 3m filters: WAIT (5/5 no eligible evidence)")
        state.accept("TCS","3m",4,sample(),allowed_symbols=("TCS",),trusted_transport=True)
        text=state.compact("TCS","3m",selected_equities=("TCS",))
        self.assertIn("OI Support BULLISH HIST",text)
        self.assertIn("Candle Trend BULLISH HIST",text)
        self.assertNotIn("sixth",text.lower())
        self.assertNotIn("%",text)
        self.assertIn("WAIT",state.compact("TCS","3m",selected_equities=()))
        state.forget_removed(())
        self.assertIn("WAIT",state.compact("TCS","3m",selected_equities=("TCS",)))

if __name__=="__main__":
    unittest.main()
