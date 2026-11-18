"""Offline FT-3 joint expiry/metric/factor safety without a Dhan request."""
from pathlib import Path
import sys
import unittest

src = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(src))
from option_evidence import LocalExpiryChoices, LocalOptionEvidence, OptionEvidenceError
from filter_evidence import LocalFilterEvidence, FilterEvidenceError
from option_filter_gate import accept_option_factors, select_option_expiry, accept_expiry_roster, accept_option_metrics


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

    def test_expiry_change_clears_only_four_option_factors_not_candle(self):
        self.exp.accept("NIFTY",1,["2026-11-26","2026-12-03"],
                        allowed_symbols=("NIFTY",),trusted_transport=True)
        select_option_expiry(self.flt,self.exp,"NIFTY","2026-11-26")
        self.opt.accept(metrics(),trusted_transport=True)
        self.join({"pcr":factor(),"oi_support":factor()})
        self.flt.accept_available("NIFTY","1m",10,{"candle_trend":factor()},
                                  allowed_symbols=("NIFTY",),trusted_transport=True)
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"NEUTRAL HIST")
        with self.assertRaises(OptionEvidenceError):
            select_option_expiry(self.flt,self.exp,"NIFTY","2026-12-31")
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"NEUTRAL HIST")
        self.assertTrue(select_option_expiry(
            self.flt,self.exp,"NIFTY","2026-12-03"))
        self.assertEqual([v for _,v in self.flt.rows("NIFTY","1m")[:5]],
                         ["WAIT","WAIT","WAIT","WAIT","NEUTRAL HIST"])
        self.assertEqual(self.flt.rows("NIFTY","1m")[-1],("",""))
        self.assertFalse(select_option_expiry(
            self.flt,self.exp,"NIFTY","2026-12-03"))
        with self.assertRaises(OptionEvidenceError):
            self.join({"pcr":factor()},revision=2)
        self.opt.accept(metrics(revision=2,expiry="2026-12-03"),trusted_transport=True)
        self.assertTrue(self.join({"pcr":factor()},revision=1))
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"NEUTRAL HIST")
        self.assertEqual(self.flt.rows("NIFTY","1m")[4][1],"NEUTRAL HIST")

    def test_new_roster_removing_expiry_retires_only_option_evidence(self):
        self.exp.accept("NIFTY",1,["2026-11-26","2026-12-03"],
                        allowed_symbols=("NIFTY",),trusted_transport=True)
        select_option_expiry(self.flt,self.exp,"NIFTY","2026-11-26")
        self.opt.accept(metrics(),trusted_transport=True)
        self.join({"pcr":factor()})
        self.flt.accept_available("NIFTY","1m",5,{"candle_trend":factor()},
                                  allowed_symbols=("NIFTY",),trusted_transport=True)
        with self.assertRaises(OptionEvidenceError):
            accept_expiry_roster(self.flt,self.exp,"NIFTY",2,[],
                allowed_symbols=("NIFTY",),trusted_transport=True)
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"NEUTRAL HIST")
        self.assertTrue(accept_expiry_roster(
            self.flt,self.exp,"NIFTY",2,["2026-12-03"],
            allowed_symbols=("NIFTY",),trusted_transport=True))
        self.assertIsNone(self.exp.selected("NIFTY"))
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"WAIT")
        self.assertEqual(self.flt.rows("NIFTY","1m")[4][1],"NEUTRAL HIST")


    def test_new_selected_option_metrics_retire_old_directions_preserve_candle(self):
        self.exp.accept("NIFTY",1,["2026-11-26","2026-12-03"],
                        allowed_symbols=("NIFTY",),trusted_transport=True)
        select_option_expiry(self.flt,self.exp,"NIFTY","2026-11-26")
        self.assertTrue(accept_option_metrics(
            self.flt,self.opt,self.exp,metrics(),trusted_transport=True))
        self.join({"pcr":factor(),"oi_support":factor()},revision=50)
        self.flt.accept_available("NIFTY","1m",30,{"candle_trend":factor()},
                                  allowed_symbols=("NIFTY",),trusted_transport=True)
        self.flt.accept_available("NIFTY","3m",50,{"pcr":factor()},
                                  allowed_symbols=("NIFTY",),trusted_transport=True)
        for invalid in (dict(metrics(revision=2),source="yahoo"),
                        dict(metrics(revision=2),pcr=99)):
            with self.subTest(invalid=invalid),self.assertRaises(OptionEvidenceError):
                accept_option_metrics(self.flt,self.opt,self.exp,invalid,
                                      trusted_transport=True)
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"NEUTRAL HIST")
        self.assertFalse(accept_option_metrics(
            self.flt,self.opt,self.exp,metrics(),trusted_transport=True))
        # A higher revision with identical observed metrics changes nothing.
        self.assertTrue(accept_option_metrics(
            self.flt,self.opt,self.exp,metrics(revision=2),trusted_transport=True))
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"NEUTRAL HIST")
        # New Dhan observation: all four option directions across timeframes WAIT.
        changed=dict(metrics(revision=3),observed_at=1795000060)
        self.assertTrue(accept_option_metrics(
            self.flt,self.opt,self.exp,changed,trusted_transport=True))
        self.assertEqual([v for _,v in self.flt.rows("NIFTY","1m")[:5]],
                         ["WAIT","WAIT","WAIT","WAIT","NEUTRAL HIST"])
        self.assertEqual(self.flt.rows("NIFTY","3m")[3][1],"WAIT")
        self.assertEqual(self.opt.visible("NIFTY","2026-11-26")["observed_at"],
                         1795000060)
        self.assertEqual(self.flt.rows("NIFTY","1m")[-1],("",""))
        self.assertTrue(self.join({"pcr":factor(1795000060)},revision=1))
        self.assertEqual(self.flt.rows("NIFTY","1m")[3][1],"NEUTRAL HIST")
        with self.assertRaises(FilterEvidenceError):
            self.join({"pcr":factor()},revision=2)

    def test_nonselected_expiry_and_equity_scope_cannot_erase_current_factors(self):
        self.exp.accept("NIFTY",1,["2026-11-26","2026-12-03"],
                        allowed_symbols=("NIFTY",),trusted_transport=True)
        select_option_expiry(self.flt,self.exp,"NIFTY","2026-11-26")
        accept_option_metrics(self.flt,self.opt,self.exp,metrics(),trusted_transport=True)
        self.join({"max_pain":factor()})
        later=dict(metrics(revision=3,expiry="2026-12-03"),observed_at=1795000090)
        self.assertTrue(accept_option_metrics(
            self.flt,self.opt,self.exp,later,trusted_transport=True))
        self.assertEqual(self.flt.rows("NIFTY","1m")[2][1],"NEUTRAL HIST")
        with self.assertRaises(OptionEvidenceError):
            accept_option_metrics(self.flt,self.opt,self.exp,metrics("TCS"),
                                  trusted_transport=True)
        self.assertEqual(self.flt.rows("NIFTY","1m")[2][1],"NEUTRAL HIST")
        with self.assertRaises(OptionEvidenceError):
            accept_option_metrics(self.flt,self.opt,self.exp,metrics(revision=5),
                                  trusted_transport=False)
        self.assertEqual(self.flt.rows("NIFTY","1m")[2][1],"NEUTRAL HIST")

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
