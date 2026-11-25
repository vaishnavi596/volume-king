import sys
import unittest
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
sys.path.insert(0,str(root/"src"))
from backend.clone_v2_gateway import observed_trade_timestamp
from clone_v2_gateway import QuotePriceBatch, observed_quote_fields

class ML5TradeTimestampTests(unittest.TestCase):
    def test_ist_and_reject_placeholder_future(self):
        self.assertEqual(observed_trade_timestamp("2026-11-25 12:00:00",now=1800000000),1795588200)
        for value in ("1980-01-01 00:00:00","2099-01-01 00:00:00",None,123,"invalid"):
            self.assertIsNone(observed_trade_timestamp(value,now=1800000000))
    def test_quote_metadata_stays_unverified_and_compatible(self):
        prices=QuotePriceBatch()
        prices["NIFTY"]=25000.0
        prices.trade_timestamps["NIFTY"]=1795588200
        self.assertEqual(prices,{"NIFTY":25000.0})
        self.assertEqual(observed_quote_fields(prices,"NIFTY")["quote_timestamp"],1795588200)
        self.assertFalse(observed_quote_fields(prices,"NIFTY")["live_verified"])
        self.assertIsNone(observed_quote_fields({"NIFTY":25000.0},"NIFTY")["quote_timestamp"])
