"""Vote percentage contract: directional votes only, no trade probability."""
import unittest
from test_audit import start


class StrengthBarTests(unittest.TestCase):
    def test_vote_percentage(self):
        _, v = start({"scanner_live": False})
        calc = v["signal_percentages"]
        filters=("Supertrend","EMA 9/21","RSI 14","MACD","VWAP",
                 "SMC Structure","Order Block","Pivot Points")
        self.assertEqual(calc({"votes": [{"name":name,"vote":1 if i<6 else -1}
                                          for i,name in enumerate(filters)]}), (75, 25, 8))
        self.assertEqual(calc({"votes": [{"name":name,"vote":1} for name in filters]}), (100, 0, 8))
        self.assertIsNone(calc({"votes": [{"vote": 0}, {"vote": None}]}))

    def test_all_watchlists_render_without_signal_data(self):
        _, v = start({"scanner_live": False})
        for index in range(5):
            v["active_watch"][0] = index
            v["fill_watch"]()


if __name__ == "__main__":
    unittest.main()
