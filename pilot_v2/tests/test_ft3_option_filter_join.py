"""Offline FT-3 joint expiry/metric/factor safety without a Dhan request."""
from pathlib import Path
import sys
import unittest

src = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(src))
from option_evidence import LocalExpiryChoices, LocalOptionEvidence, OptionEvidenceError
from filter_evidence import LocalFilterEvidence, FilterEvidenceError
from option_filter_gate import accept_option_factors


def metrics(symbol="NIFTY", revision=1, expiry="2026-11-26"):
    return {"symbol":symbol, "expiry":expiry, "revision":revision,
            "observed_at":1795000000, "source":"dhan", "ce_oi":100,
            "pe_oi":125, "pcr":1.25, "max_pain":25000, "eligible":True}

def factor(observed=1795000000, direction="neutral"):
    return {"direction":direction, "source":"dhan",
            "observed_at":observed, "eligible":True}

class OptionFilterJoinTests(unittest.TestCase):
    def setUp(self):
        self.exp = LocalExpiryChoices()
        self.opt = LocalOptionEvidence()
        self.flt = LocalFilterEvidence()

    def join(self, factors, symbol="NIFTY", revision=1, timeframe="1m", selected=()):
        return accept_option_factors(
            self.flt, self.opt, self.exp, symbol, timeframe, revision, factors,
            selected_equities=selected, trusted_transport=True)

    def test_metrics_without_source_expiry_never_activate_factors(self):
        with self.assertRaises(OptionEvidenceError):
            self.join({"pcr":factor()})
        self.opt.accept(metrics(), trusted_transport=True)
        with self.assertRaises(OptionEvidenceError):
            self.join({"pcr":factor()})
        self.assertEqual([x for _,x in self.flt.rows("NIFTY","1m")[:5]], ["WAIT"]*5)

    def test_matching_expiry_metric_observation_allows_only_supplied_factors(self):
        self.exp.accept("NIFTY",1,["2026-11-26","2026-12-03"],
                        allowed_symbols=("NIFTY",),trusted_transport=True)
        self.exp.choose("NIFTY","2026-11-26")
        self.opt.accept(metrics(),trusted_transport=True)
        self.assertTrue(self.join({"pcr":factor()}))
        self.assertEqual([x for _,x in self.flt.rows("NIFTY","1m")[:5]],
                         ["WAIT","WAIT","WAIT","NEUTRAL HIST","WAIT"])
        self.assertEqual(self.flt.rows("NIFTY","1m")[5],("",""))
        self.assertFalse(self.join({"pcr":factor()},revision=1))
        self.assertNotIn("%",self.flt.compact("NIFTY","1m"))

    def test_cross_expiry_and_mismatched_timestamp_rejected_without_erasure(self):
        self.exp.accept("NIFTY",1,["2026-11-26","2026-12-03"],
                        allowed_symbols=("NIFTY",),trusted_transport=True)
        self.exp.choose("NIFTY","2026-11-26")
        self.opt.accept(metrics(),trusted_transport=True)
        self.join({"pcr":factor()})
        self.exp.choose("NIFTY","2026-12-03")
        with self.assertRaises(OptionEvidenceError):
            self.join({"max_pain":factor()},revision=2)
        self.exp.choose("NIFTY","2026-11-26")
        for invalid in ({"pcr":factor(1795000001)},
                        {"pcr":factor(),"candle_trend":factor()},
                        {"pcr":factor(),"max_pain":factor(0)}):
            with self.subTest(invalid=invalid),self.assertRaises(FilterEvidenceError):
                self.join(invalid,revision=2)
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"NEUTRAL HIST")
        self.assertEqual(self.flt.rows("NIFTY","1m")[2][1],"WAIT")

    def test_equity_removal_must_not_leak_metric_or_filter(self):
        self.exp.accept("TCS",1,["2026-11-26"],allowed_symbols=("TCS",),
                        trusted_transport=True)
        self.exp.choose("TCS","2026-11-26",selected_equities=("TCS",))
        self.opt.accept(metrics("TCS"),selected_equities=("TCS",),
                        trusted_transport=True)
        self.assertTrue(self.join({"oi_support":factor()},
                                  symbol="TCS",selected=("TCS",),timeframe="3m"))
        self.exp.forget_removed(())
        self.opt.forget_removed(())
        self.flt.forget_removed(())
        with self.assertRaises(OptionEvidenceError):
            self.join({"pcr":factor()},symbol="TCS",selected=("TCS",),timeframe="3m")
        self.assertEqual(self.flt.rows("TCS","3m",selected_equities=("TCS",))[0][1],"WAIT")

if __name__ == "__main__":
    unittest.main()
