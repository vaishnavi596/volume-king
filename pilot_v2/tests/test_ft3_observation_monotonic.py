"""FT3 offline source observation rollback vs revision tests; zero Dhan calls."""
from pathlib import Path
import sys
import unittest

src = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(src))
from option_evidence import LocalOptionEvidence, OptionEvidenceError
from filter_evidence import LocalFilterEvidence

def option(revision, observed_at, *, expiry="2026-11-26", symbol="NIFTY"):
    return {"symbol":symbol,"expiry":expiry,"revision":revision,
            "observed_at":observed_at,"source":"dhan","ce_oi":100,
            "pe_oi":125,"pcr":1.25,"max_pain":25000,"eligible":True}

def row(observed_at, direction="bullish"):
    return {"direction":direction,"source":"dhan",
            "observed_at":observed_at,"eligible":True}

def five(observed_at, direction="bullish"):
    return {key:row(observed_at,direction) for key in
            ("oi_support","oi_resistance","max_pain","pcr","candle_trend")}

class SourceObservationMonotonicTests(unittest.TestCase):
    def test_option_higher_revision_older_source_time_cannot_erase_last_good(self):
        cache=LocalOptionEvidence()
        self.assertTrue(cache.accept(option(4,200),trusted_transport=True))
        self.assertFalse(cache.accept(option(9,199),trusted_transport=True))
        self.assertEqual(cache.visible("NIFTY","2026-11-26")["revision"],4)
        self.assertEqual(cache.visible("NIFTY","2026-11-26")["observed_at"],200)
        self.assertFalse(cache.accept(option(4,300),trusted_transport=True))
        self.assertTrue(cache.accept(option(5,200),trusted_transport=True))
        self.assertTrue(cache.accept(option(6,201),trusted_transport=True))
        self.assertEqual(cache.visible("NIFTY","2026-11-26")["observed_at"],201)
        self.assertEqual(cache.visible("NIFTY","2026-12-03")["status"],"WAIT")

    def test_independent_expiries_have_independent_observation_clock(self):
        cache=LocalOptionEvidence()
        cache.accept(option(100,300),trusted_transport=True)
        self.assertTrue(cache.accept(option(1,40,expiry="2026-12-03"),
                                     trusted_transport=True))
        self.assertEqual(cache.visible("NIFTY","2026-11-26")["revision"],100)
        self.assertEqual(cache.visible("NIFTY","2026-12-03")["revision"],1)
        with self.assertRaises(OptionEvidenceError):
            cache.accept(dict(option(101,301),source="other"),trusted_transport=True)

    def test_partial_factor_fast_revision_stale_time_does_not_overwrite(self):
        f=LocalFilterEvidence()
        f.accept_available("NIFTY","1m",20,{"pcr":row(500)},
                           allowed_symbols=("NIFTY",),trusted_transport=True)
        self.assertFalse(f.accept_available(
            "NIFTY","1m",200,{"pcr":row(499,"bearish")},
            allowed_symbols=("NIFTY",),trusted_transport=True))
        self.assertEqual(f.rows("NIFTY","1m")[3][1],"BULLISH HIST")
        # A slower independent candle lane can still update at revision one.
        self.assertTrue(f.accept_available(
            "NIFTY","1m",1,{"candle_trend":row(100)},
            allowed_symbols=("NIFTY",),trusted_transport=True))
        self.assertTrue(f.accept_available(
            "NIFTY","1m",21,{"pcr":row(501,"bearish")},
            allowed_symbols=("NIFTY",),trusted_transport=True))
        self.assertEqual(f.rows("NIFTY","1m")[3][1],"BEARISH HIST")
        self.assertEqual(f.rows("NIFTY","1m")[4][1],"BULLISH HIST")
        self.assertEqual(f.rows("NIFTY","1m")[-1],("",""))

    def test_full_snapshot_rollback_denied_atomically(self):
        f=LocalFilterEvidence()
        f.accept("TCS","3m",10,five(800),allowed_symbols=("TCS",),
                 trusted_transport=True)
        candidate=five(801,"bearish")
        candidate["pcr"]=row(799,"bearish")
        self.assertFalse(f.accept("TCS","3m",11,candidate,
                                  allowed_symbols=("TCS",),trusted_transport=True))
        self.assertEqual([v for _,v in f.rows(
            "TCS","3m",selected_equities=("TCS",))[:5]],["BULLISH HIST"]*5)
        self.assertTrue(f.accept("TCS","3m",11,five(801,"bearish"),
                                 allowed_symbols=("TCS",),trusted_transport=True))
        self.assertEqual(f.rows("TCS","3m",selected_equities=("TCS",))[3][1],
                         "BEARISH HIST")

if __name__=="__main__":
    unittest.main()
