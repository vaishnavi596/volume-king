"""FT-3 normalized options + candles + five evidence slots integration."""
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from option_evidence import LocalOptionEvidence, LocalExpiryChoices, OptionEvidenceError, valid_expiry  # noqa: E402
from candle_history import LocalCandleHistory  # noqa: E402
from filter_evidence import LocalFilterEvidence  # noqa: E402

def option(symbol="NIFTY", revision=1, expiry="2026-11-26"):
    return {"symbol":symbol,"expiry":expiry,"revision":revision,
            "observed_at":1795000000,"source":"dhan","ce_oi":100,
            "pe_oi":125,"pcr":1.25,"max_pain":25000,"eligible":True}

def bars():
    return [{"timestamp":100,"open":100,"high":105,"low":99,"close":101,
             "volume":20,"completed":True},
            {"timestamp":200,"open":101,"high":104,"low":100,"close":103,
             "volume":15,"completed":True}]

class OptionsCandleFilterIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.o=LocalOptionEvidence()
        self.c=LocalCandleHistory()
        self.f=LocalFilterEvidence()

    def test_complete_option_metrics_retained_but_no_invented_signals(self):
        self.c.accept("NIFTY","1m",3,bars(),allowed_symbols=("NIFTY",))
        self.assertEqual(self.o.visible("NIFTY","2026-11-26")["status"],"WAIT")
        with self.assertRaises(OptionEvidenceError):
            self.o.accept(option(),trusted_transport=False)
        self.assertTrue(self.o.accept(option(),trusted_transport=True))
        self.assertEqual(self.o.visible("NIFTY","2026-11-26")["status"],"HIST")
        self.assertIn("PCR 1.25",self.o.summary("NIFTY","2026-11-26"))
        self.assertEqual([v for _,v in self.f.rows("NIFTY","1m")[:5]],["WAIT"]*5)
        self.assertEqual(self.f.rows("NIFTY","1m")[5],("",""))

    def test_invalid_partial_or_foreign_options_preserve_last_good_candle_and_option(self):
        self.c.accept("NIFTY","1m",2,bars(),allowed_symbols=("NIFTY",))
        self.o.accept(option(),trusted_transport=True)
        incorrect = [dict(option(revision=2), pcr=999),
                     dict(option(revision=2), pe_oi=-1),
                     dict(option(revision=2), ce_oi=0),
                     dict(option(revision=2), source="yahoo"),
                     dict(option(revision=2), eligible=False),
                     dict(option(revision=2), expiry="not a date"),
                     dict(option(revision=2), live_verified=True),
                     option("TCS", 2)]
        for candidate in incorrect:
            with self.subTest(payload=str(candidate)[:75]),self.assertRaises(OptionEvidenceError):
                self.o.accept(candidate,trusted_transport=True)
        self.assertEqual(self.o.visible("NIFTY","2026-11-26")["pcr"],1.25)
        self.assertEqual(self.c.view("NIFTY","1m")["count"],2)
        self.assertFalse(self.o.accept(option(),trusted_transport=True))
        self.assertEqual(self.o.visible("NIFTY","2026-12-03")["status"],"WAIT")

    def test_strict_calendar_expiry_validation_and_no_forged_dates(self):
        for invalid in ("2026-02-30", "2026-13-01", "2026-11-31",
                        "2026-1-26", "２０２６-11-26", "2026-00-01"):
            with self.subTest(expiry=invalid):
                self.assertFalse(valid_expiry(invalid))
                with self.assertRaises(OptionEvidenceError):
                    self.o.accept(option(expiry=invalid), trusted_transport=True)
        self.assertTrue(valid_expiry("2028-02-29"))

    def test_expiry_roster_selection_is_source_gated_by_symbol(self):
        choices = LocalExpiryChoices()
        with self.assertRaises(OptionEvidenceError):
            choices.choose("NIFTY", "2026-11-26")
        with self.assertRaises(OptionEvidenceError):
            choices.accept("NIFTY", 1, ["2026-11-26"],
                           allowed_symbols=("NIFTY",))
        self.assertTrue(choices.accept("NIFTY", 1, ["2026-11-26", "2026-12-03"],
                        allowed_symbols=("NIFTY",), trusted_transport=True))
        choices.choose("NIFTY", "2026-12-03")
        self.assertEqual(choices.selected("NIFTY"), "2026-12-03")
        self.assertIsNone(choices.selected("BANKNIFTY"))
        with self.assertRaises(OptionEvidenceError):
            choices.choose("BANKNIFTY", "2026-12-03")
        self.assertFalse(choices.accept("NIFTY", 1, ["2026-11-26"],
                          allowed_symbols=("NIFTY",), trusted_transport=True))
        for malformed in ([], ["2026-02-30"], ["2026-12-03", "2026-11-26"],
                          ["2026-11-26", "2026-11-26"]):
            with self.subTest(malformed=malformed), self.assertRaises(OptionEvidenceError):
                choices.accept("NIFTY", 2, malformed,
                               allowed_symbols=("NIFTY",), trusted_transport=True)
        self.assertEqual(choices.selected("NIFTY"), "2026-12-03")
        choices.accept("NIFTY", 2, ["2026-11-26"],
                       allowed_symbols=("NIFTY",), trusted_transport=True)
        self.assertIsNone(choices.selected("NIFTY"))
        self.assertEqual(choices.available("NIFTY"), ("2026-11-26",))

    def test_deleted_symbol_clears_expiry_choices_and_index_independent(self):
        choices = LocalExpiryChoices()
        choices.accept("TCS", 1, ["2026-11-26"], allowed_symbols=("TCS",),
                       trusted_transport=True)
        choices.choose("TCS", "2026-11-26", selected_equities=("TCS",))
        choices.accept("SENSEX", 1, ["2026-11-26"], allowed_symbols=("SENSEX",),
                       trusted_transport=True)
        choices.forget_removed(())
        self.assertEqual(choices.available("TCS", selected_equities=("TCS",)), ())
        self.assertIsNone(choices.selected("TCS", selected_equities=("TCS",)))
        self.assertEqual(choices.available("SENSEX"), ("2026-11-26",))

    def test_options_equity_restricted_and_removed_without_index_leak(self):
        with self.assertRaises(OptionEvidenceError):
            self.o.accept(option("TCS"),trusted_transport=True)
        self.assertTrue(self.o.accept(option("TCS"),selected_equities=("TCS",),
                                      trusted_transport=True))
        self.assertEqual(self.o.visible("TCS","2026-11-26")["status"],"WAIT")
        self.o.forget_removed(())
        self.assertEqual(self.o.visible("TCS","2026-11-26",
                                        selected_equities=("TCS",))["status"],"WAIT")

if __name__ == "__main__":
    unittest.main()
