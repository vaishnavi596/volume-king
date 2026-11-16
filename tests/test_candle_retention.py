"""BK retained historical candles never turn into invented live candles."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from candle_retention import retain_candle_history

def candles(start=1000,count=40):
    return [[start+300*i,100.0,105.0,95.0,101.0,1000.0] for i in range(count)]

class CandleRetentionTests(unittest.TestCase):
    def setUp(self):
        self.old={"source":"Dhan","bars":candles(),"candle_fetched_at":65000,
                  "freshness":"historical_unverified","live_verified":False}

    def test_empty_dhan_response_keeps_history_but_not_live(self):
        incoming={"source":"Dhan","bars":[],"price":2077.3,"live_verified":True}
        result=retain_candle_history(incoming,self.old)
        self.assertEqual(result["bars"],self.old["bars"])
        self.assertEqual(result["price"],2077.3)
        self.assertTrue(result["historical"])
        self.assertTrue(result["cached"])
        self.assertFalse(result["live_verified"])
        self.assertEqual(result["freshness"],"historical_unverified")
        self.assertEqual(result["candle_fetched_at"],65000)

    def test_partial_history_does_not_replace_last_40_candles(self):
        result=retain_candle_history({"source":"Dhan","bars":candles(13000,4)},self.old)
        self.assertEqual(len(result["bars"]),40)
        self.assertTrue(result["_candle_retained"])

    def test_older_window_does_not_replace_newer_window(self):
        result=retain_candle_history({"source":"Dhan","bars":candles(100,40)},self.old)
        self.assertEqual(result["bars"],self.old["bars"])

    def test_newer_valid_window_wins(self):
        newer=candles(2000)
        result=retain_candle_history({"source":"Dhan","bars":newer},self.old)
        self.assertEqual(result["bars"],newer)
        self.assertNotIn("_candle_retained",result)

    def test_cross_provider_history_not_reused(self):
        result=retain_candle_history({"source":"Dhan","bars":[]},
                                     {"source":"Yahoo Finance","bars":candles()})
        self.assertEqual(result["bars"],[])
        self.assertNotIn("_candle_retained",result)

    def test_invalid_prior_not_used_as_history(self):
        broken=dict(self.old,bars=[[1,100,105,95,101,1000]])
        result=retain_candle_history({"source":"Dhan","bars":[]},broken)
        self.assertEqual(result["bars"],[])
        self.assertNotIn("_candle_retained",result)

    def test_ordered_candles_required(self):
        broken=dict(self.old,bars=candles()[:-1]+[candles()[-3]])
        self.assertFalse(retain_candle_history({"source":"Dhan","bars":[]},broken).get("_candle_retained"))
