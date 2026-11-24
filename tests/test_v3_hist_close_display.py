"""Closed-session historical close must never be represented as LTP."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from v3_hist_close_display import historical_close_display

class HistoricalCloseDisplayTests(unittest.TestCase):
    def setUp(self):
        self.hist={"source":"Dhan","_scanner_timeframe":"3m",
                   "bars":[[1700000000,100,105,98,102.25,1000]]}
        self.now=1700000300

    def test_completed_matching_dhan_history_is_explicitly_not_live(self):
        result=historical_close_display(self.hist,now=self.now)
        self.assertEqual(result[0],"HIST 102.25")
        self.assertIn("HIST CLOSE",result[1])
        self.assertIn("NOT LIVE",result[1])
        self.assertIn("source unverified",result[1])

    def test_no_cross_timeframe_or_source(self):
        for field,val in (("_scanner_timeframe","1m"),("source","Yahoo Finance")):
            bad=dict(self.hist,**{field:val})
            self.assertIsNone(historical_close_display(bad,now=self.now))

    def test_future_partial_or_malformed_price_never_shows(self):
        self.assertIsNone(historical_close_display(self.hist,now=1700000170))
        for bar in ([1700000000,100,99,98,102,100],
                    [1700000000,100,105,98,-1,100],
                    [1700000000,100,105,98,float("nan"),100]):
            self.assertIsNone(historical_close_display(dict(self.hist,bars=[bar]),now=self.now))

    def test_latest_completed_candle_used_without_network(self):
        h=dict(self.hist,bars=self.hist["bars"]+[[1700000180,102,110,101,109,200]])
        self.assertEqual(historical_close_display(h,now=1700000400)[0],"HIST 109.00")
        self.assertEqual(historical_close_display(h,now=1700000300)[0],"HIST 102.25")

if __name__=="__main__":
    unittest.main()
