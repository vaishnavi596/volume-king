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

    def test_retained_or_merged_candles_never_claim_fresh_transport_equality(self):
        prior=dict(self.old,candle_transport_integrity="SHA256_MATCH",
                   _scanner_timeframe="1m")
        retained=retain_candle_history(
            {"source":"Dhan","bars":[],
             "candle_transport_integrity":"NOT_PROVIDED"},prior)
        self.assertEqual(retained["candle_transport_integrity"],
                         "RETAINED_PRIOR_TRANSPORT_SHA256_MATCH")
        self.assertFalse(retained["live_verified"])
        latest=[list(row) for row in prior["bars"][-2:]]
        merged=retain_candle_history(
            {"source":"Dhan","bars":latest,
             "_scanner_timeframe":"1m",
             "candle_transport_integrity":"SHA256_MATCH"},prior)
        self.assertTrue(merged["_candle_partial_revised"])
        self.assertEqual(merged["candle_transport_integrity"],
                         "MERGED_HISTORY_NOT_DIRECT_DIGEST")
        self.assertFalse(merged["live_verified"])

    def test_partial_history_does_not_replace_last_40_candles(self):
        result=retain_candle_history({"source":"Dhan","bars":candles(13000,4)},self.old)
        self.assertEqual(len(result["bars"]),40)
        self.assertTrue(result["_candle_retained"])

    def test_last_four_overlapping_candles_are_revised_without_losing_history(self):
        for n in (2,3,4):
            latest=[list(row) for row in self.old["bars"][-n:]]
            for row in latest:
                row[4]=102.0
            result=retain_candle_history({"source":"Dhan","bars":latest,
                "candle_fetched_at":66000},self.old)
            self.assertEqual(len(result["bars"]),40)
            self.assertEqual(result["bars"][-n:],latest)
            self.assertEqual(result["bars"][:-n],self.old["bars"][:-n])
            self.assertTrue(result["_candle_partial_revised"])
            self.assertFalse(result["live_verified"])
            self.assertEqual(result["freshness"],"historical_unverified")

    def test_partial_history_does_not_cross_timeframe_or_accept_gaps(self):
        latest=[list(row) for row in self.old["bars"][-2:]]
        latest[0][4]=102.0
        prior=dict(self.old,_scanner_timeframe="1m")
        cross=retain_candle_history({"source":"Dhan","bars":latest,
            "_scanner_timeframe":"3m"},prior)
        self.assertEqual(cross["bars"],latest)
        self.assertFalse(cross.get("_candle_retained",False))
        self.assertFalse(cross.get("_candle_partial_revised",False))
        # Even an empty response cannot borrow the other timeframe's bars.
        empty=retain_candle_history({"source":"Dhan","bars":[],
            "_scanner_timeframe":"3m"},prior)
        self.assertEqual(empty["bars"],[])
        self.assertFalse(empty.get("_candle_retained",False))
        gap=[list(self.old["bars"][-4]),list(self.old["bars"][-1])]
        result=retain_candle_history({"source":"Dhan","bars":gap},self.old)
        self.assertFalse(result.get("_candle_partial_revised",False))

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

    def test_explicit_timeframe_never_borrows_untagged_legacy_candles(self):
        # Legacy phone cache may have valid but unknown 5m bars; it cannot
        # serve a new explicit 1m/3m request after a missing Dhan refresh.
        for tf in ("1m", "3m", "5m"):
            with self.subTest(timeframe=tf):
                fresh={"source":"Dhan", "_scanner_timeframe":tf,
                       "bars":[], "candle_fetched_at":0}
                result=retain_candle_history(fresh,self.old)
                self.assertEqual(result["bars"],[])
                self.assertNotIn("_candle_retained",result)
                self.assertNotIn("_candle_partial_revised",result)
        # Valid matching-tag last-good history continues to work normally.
        prior=dict(self.old,_scanner_timeframe="3m")
        fresh={"source":"Dhan","_scanner_timeframe":"3m","bars":[]}
        result=retain_candle_history(fresh,prior)
        self.assertEqual(result["bars"],prior["bars"])
        self.assertTrue(result["_candle_retained"])
        self.assertFalse(result["live_verified"])

    def test_cross_timeframe_last_filter_votes_never_transfer(self):
        from candle_retention import retain_last_filter_votes
        prior={"source":"Dhan","timeframe":"5m","timestamp":1234.0,
               "votes":[{"name":"EMA 9/21","vote":1}],
               "historical":True}
        for tf in ("1m","3m"):
            with self.subTest(tf=tf):
                new={"source":"Dhan","timeframe":tf,"votes":[]}
                result=retain_last_filter_votes(
                    new,prior,selected_filters=["EMA 9/21"])
                self.assertEqual(result["votes"],[])
                self.assertNotIn("_last_votes_retained",result)
                self.assertIsNone(result.get("timestamp"))
        same=retain_last_filter_votes(
            {"source":"Dhan","timeframe":"5m","votes":[]},
            prior,selected_filters=["EMA 9/21"])
        self.assertTrue(same["_last_votes_retained"])
        self.assertTrue(same["historical"])
        self.assertFalse(same["live_verified"])

    def test_cross_timeframe_complete_history_never_relabels_bars(self):
        old=dict(self.old,_scanner_timeframe="5m")
        fresh={"source":"Dhan","_scanner_timeframe":"1m",
               "bars":candles(2000,40)}
        result=retain_candle_history(fresh,old)
        self.assertEqual(result["bars"],fresh["bars"])
        self.assertNotIn("_candle_retained",result)
        short={"source":"Dhan","_scanner_timeframe":"1m",
               "bars":candles(2000,3)}
        result=retain_candle_history(short,old)
        self.assertEqual(result["bars"],short["bars"])
        self.assertNotIn("_candle_retained",result)

    def test_malformed_incoming_votes_do_not_crash_retention(self):
        from candle_retention import retain_last_filter_votes
        prior={"source":"Dhan","timestamp":1234.0,
               "votes":[{"name":"candle","vote":1}]}
        incoming={"source":"Dhan","votes":{"malformed":"payload"}}
        result=retain_last_filter_votes(incoming,prior,selected_filters=["candle"])
        self.assertTrue(result["_last_votes_retained"])
        self.assertEqual(result["bias"],"WAIT")
        self.assertFalse(result["live_verified"])

    def test_malformed_prior_votes_are_not_reused(self):
        from candle_retention import retain_last_filter_votes
        incoming={"source":"Dhan","votes":[]}
        prior={"source":"Dhan","timestamp":1234.0,"votes":{"candle":1}}
        result=retain_last_filter_votes(incoming,prior,selected_filters=["candle"])
        self.assertNotIn("_last_votes_retained",result)
        self.assertEqual(result["votes"],[])

    def test_ordered_candles_required(self):
        broken=dict(self.old,bars=candles()[:-1]+[candles()[-3]])
        self.assertFalse(retain_candle_history({"source":"Dhan","bars":[]},broken).get("_candle_retained"))
