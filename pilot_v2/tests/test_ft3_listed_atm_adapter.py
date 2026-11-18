"""V2 exact listed ATM±3 normalization isolated from any real Dhan HTTP."""
import sys
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/"android_app"/"src"
sys.path.insert(0,str(ROOT))
from listed_atm_adapter import normalized_atm_window
from evidence_inbox import DeviceEvidenceInbox
from option_evidence import OptionEvidenceError


def listed(n=11):
    return [{"strike": 24800+50*i, "ce_price": 90-i,
             "ce_oi": 100+i, "ce_volume": 40+i,
             "pe_price": 50+i, "pe_oi": 110+i,
             "pe_volume": 45+i} for i in range(n)]


def adapt(rows=None, spot=25075, **extra):
    params={"symbol":"NIFTY", "expiry":"2026-11-26",
            "revision":1,"observed_at":1000, "spot":spot,
            "listed_rows": listed() if rows is None else rows,
            "trusted_transport":True}
    params.update(extra)
    return normalized_atm_window(**params)


class ListedATMTests(unittest.TestCase):
    def test_real_listed_neighborhood_and_deterministic_tie(self):
        data=adapt()
        self.assertEqual(len(data["rows"]),7)
        self.assertEqual(data["rows"][3]["strike"],25050)  # 25075 tie -> lower
        self.assertEqual([x["strike"] for x in data["rows"]],
                         [24900,24950,25000,25050,25100,25150,25200])
        self.assertEqual(data["source"],"dhan")

    def test_rejects_missing_three_strikes_on_either_side(self):
        with self.assertRaises(OptionEvidenceError):
            adapt(spot=24800)
        with self.assertRaises(OptionEvidenceError):
            adapt(spot=25300)
        with self.assertRaises(OptionEvidenceError):
            adapt(rows=listed(6))
        with self.assertRaises(OptionEvidenceError):
            adapt(trusted_transport=False)

    def test_rejects_malformed_foreign_or_unsorted_market_data(self):
        rows=listed()
        for bad in (
            list(reversed(rows)),
            rows[:5]+[dict(rows[5],strike=rows[4]["strike"])]+rows[6:],
            rows[:4]+[dict(rows[4],ce_oi=-1)]+rows[5:],
            rows[:4]+[dict(rows[4],ce_price=float("nan"))]+rows[5:],
            rows[:4]+[dict(rows[4],source="yahoo")]+rows[5:],
        ):
            with self.subTest(data=str(bad)[:65]),self.assertRaises(OptionEvidenceError):
                adapt(rows=bad)

    def test_window_passes_existing_app_strike_cache_only_for_selected_expiry(self):
        app=DeviceEvidenceInbox()
        app.apply_expiries("NIFTY",1,["2026-11-26"],trusted_transport=True)
        with self.assertRaises(OptionEvidenceError):
            app.apply_option_strikes(adapt(),trusted_transport=True)
        app.select_expiry("NIFTY","2026-11-26")
        self.assertTrue(app.apply_option_strikes(adapt(),trusted_transport=True))
        self.assertEqual(app.strikes.visible(
            "NIFTY","2026-11-26",app.expiries)["rows"][3]["strike"],25050)
        self.assertEqual(app.filters.rows("NIFTY","1m")[5],("",""))
        self.assertEqual([v for _,v in app.filters.rows("NIFTY","1m")[:5]],["WAIT"]*5)


if __name__=="__main__":unittest.main()
