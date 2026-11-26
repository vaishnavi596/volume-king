import unittest
from types import SimpleNamespace
from pathlib import Path
from clone_v2_gateway import CloneDhanReadOnly, QuotePriceBatch, observed_quote_fields
from server_feed import FeedError

class LoginQuoteProofTests(unittest.TestCase):
    def test_actual_quote_batch_subclass_accepted(self):
        gateway=SimpleNamespace(connected=True)
        feed=CloneDhanReadOnly(gateway)
        proof=QuotePriceBatch()
        proof["NIFTY"]=25000.0
        import time
        proof.trade_timestamps["NIFTY"]=time.time()-1
        feed.activate_with_quote(proof)
        self.assertTrue(feed.connected)
        self.assertEqual(observed_quote_fields(proof,"NIFTY")["timestamp_origin"],"DHAN_QUOTE_LAST_TRADE_TIME")
        for invalid in ({}, {"NIFTY":True},{"NIFTY":float("nan")},{"NIFTY":-1},{"":20}):
            with self.assertRaises(FeedError):
                feed.activate_with_quote(invalid)
            self.assertFalse(feed.connected)
        gateway.connected=False
        with self.assertRaises(FeedError):
            feed.activate_with_quote(proof)
    def test_login_timestamp_wiring(self):
        source=(Path(__file__).resolve().parents[1]/"src/main.py").read_text()
        self.assertIn("**observed_quote_fields(proof,symbol)",source)
        self.assertIn("BK-LOGIN-QUOTE-001",source)
