"""Historical evidence remains visible on a failed candle scan, never becomes live."""
import sys
from pathlib import Path
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from candle_retention import retain_last_filter_votes

PRIOR={"source":"Dhan","timestamp":15000.0,"historical":True,
       "votes":[{"name":"RSI","vote":1},{"name":"MACD","vote":-1}],
       "bias":"BEARISH","score":80,"freshness":"historical_unverified",
       "live_verified":False}
INVALID={"source":"Dhan","timestamp":None,"votes":[],"bias":"DATA UNAVAILABLE","score":0}

class RetainHistoricalVotesTests(unittest.TestCase):
    def test_failed_new_scan_retains_colored_historical_votes_only(self):
        row=retain_last_filter_votes(INVALID,PRIOR,selected_filters=["RSI","MACD"])
        self.assertEqual(row["votes"],PRIOR["votes"])
        self.assertEqual(row["timestamp"],PRIOR["timestamp"])
        self.assertTrue(row["_last_votes_retained"])
        self.assertTrue(row["historical"])
        self.assertFalse(row["live_verified"])
        self.assertEqual(row["bias"],"WAIT")
        self.assertEqual(row["score"],0)

    def test_fresh_votes_take_priority(self):
        valid=dict(INVALID,timestamp=16000,votes=[{"name":"RSI","vote":-1}])
        self.assertEqual(retain_last_filter_votes(valid,PRIOR,selected_filters=["RSI","MACD"]),valid)

    def test_changed_filters_cannot_reuse_wrong_technical_votes(self):
        self.assertEqual(retain_last_filter_votes(INVALID,PRIOR,selected_filters=["EMA 9/21"]),INVALID)

    def test_source_mismatch_cannot_reuse_another_provider(self):
        self.assertEqual(retain_last_filter_votes(INVALID,dict(PRIOR,source="Yahoo Finance"),
                                                  selected_filters=["RSI","MACD"]),INVALID)

    def test_missing_real_timestamp_does_not_retain(self):
        self.assertEqual(retain_last_filter_votes(INVALID,dict(PRIOR,timestamp=None),
                                                  selected_filters=["RSI","MACD"]),INVALID)

    def test_wait_only_votes_do_not_masquerade_as_direction(self):
        p=dict(PRIOR,votes=[{"name":"RSI","vote":None},{"name":"MACD","vote":None}])
        self.assertEqual(retain_last_filter_votes(INVALID,p,selected_filters=["RSI","MACD"]),INVALID)
