"""V2 Flet source-bound candlestick and CE/PE chain offline tests."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"android_app"/"src"
sys.path.insert(0,str(ROOT))
from evidence_inbox import DeviceEvidenceInbox
from candle_option_views import candle_geometry
from option_evidence import OptionEvidenceError


def candles():
    return [
      {"timestamp":100,"open":100,"high":105,"low":98,
       "close":102,"volume":12,"completed":True},
      {"timestamp":200,"open":102,"high":104,"low":97,
       "close":99,"volume":10,"completed":True},
    ]


def chain(rev=1, observed=200, expiry="2026-11-26"):
    return {"symbol":"NIFTY","expiry":expiry,"revision":rev,
            "observed_at":observed,"source":"dhan",
            "rows":[{"strike":25000+i*50,"ce_price":101-i*2,
                     "ce_oi":100+i,"ce_volume":12+i,
                     "pe_price":81+i,"pe_oi":120+i,
                     "pe_volume":20+i} for i in range(7)]}


class CandleOptionTests(unittest.TestCase):
    def setUp(self):
        self.app=DeviceEvidenceInbox()
        self.app.apply_expiries("NIFTY",1,["2026-11-26","2026-12-03"],
                                trusted_transport=True)
        self.app.select_expiry("NIFTY","2026-11-26")

    def test_native_candle_geometry_true_ohlc_and_index_timeframe(self):
        self.assertEqual(candle_geometry(self.app.candles,"NIFTY","1m"),())
        self.app.apply_candles("NIFTY","1m",1,candles(),trusted_transport=True)
        geom=candle_geometry(self.app.candles,"NIFTY","1m")
        self.assertEqual(len(geom),2)
        self.assertTrue(geom[0]["up"])
        self.assertFalse(geom[1]["up"])
        self.assertGreater(geom[0]["wick_height"],geom[0]["body_height"])
        self.assertEqual(candle_geometry(self.app.candles,"NIFTY","3m"),())

    def test_strict_selected_expiry_ce_pe_and_replay_retention(self):
        self.assertEqual(self.app.strikes.visible(
            "NIFTY","2026-11-26",self.app.expiries)["status"],"WAIT")
        with self.assertRaises(OptionEvidenceError):
            self.app.apply_option_strikes(chain())
        self.assertTrue(self.app.apply_option_strikes(chain(),trusted_transport=True))
        rows=self.app.strikes.visible(
            "NIFTY","2026-11-26",self.app.expiries)
        self.assertEqual(len(rows["rows"]),7)
        self.assertEqual(rows["rows"][3]["strike"],25150)
        self.assertFalse(self.app.apply_option_strikes(chain(),trusted_transport=True))
        with self.assertRaises(OptionEvidenceError):
            self.app.apply_option_strikes(chain(2,300,"2026-12-03"),
                                          trusted_transport=True)
        self.assertEqual(self.app.strikes.visible(
            "NIFTY","2026-11-26",self.app.expiries)["rows"],rows["rows"])

    def test_invalid_or_partial_chain_cannot_overwrite_last_good(self):
        self.app.apply_option_strikes(chain(),trusted_transport=True)
        for bad in (dict(chain(2,300),source="yahoo"),
                    dict(chain(2,300),rows=chain()["rows"][:6]),
                    dict(chain(2,300),rows=[dict(x,ce_oi=-1) if i==2 else x
                                             for i,x in enumerate(chain()["rows"])]),
                    dict(chain(2,300),rows=list(reversed(chain()["rows"])))):
            with self.subTest(bad=str(bad)[:40]),self.assertRaises(OptionEvidenceError):
                self.app.apply_option_strikes(bad,trusted_transport=True)
        self.assertEqual(self.app.strikes.visible(
            "NIFTY","2026-11-26",self.app.expiries)["rows"][0]["ce_oi"],100)

    def test_expiry_change_and_deleted_equity_do_not_leak(self):
        self.app.apply_option_strikes(chain(),trusted_transport=True)
        self.app.select_expiry("NIFTY","2026-12-03")
        self.assertEqual(self.app.strikes.visible(
            "NIFTY","2026-11-26",self.app.expiries)["status"],"WAIT")
        self.app.strikes.forget_removed(())
        self.assertEqual(self.app.strikes.visible(
            "TCS","2026-11-26",self.app.expiries,selected_equities=())["status"],"WAIT")

    def test_app_ui_real_ohlc_and_ce_pe_rows_but_not_live(self):
        source=(ROOT/"main.py").read_text()
        self.assertIn("candle_geometry(",source)
        self.assertIn("ft.Stack([",source)
        self.assertIn("evidence_inbox.strikes.visible(",source)
        self.assertIn("CE/PE strikes WAIT",source)
        self.assertIn("Option-chain HIST only",source)
        self.assertNotIn("from market_feed import",source)


if __name__=="__main__":
    unittest.main()
