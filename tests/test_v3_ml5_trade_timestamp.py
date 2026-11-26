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
        self.assertEqual(observed_trade_timestamp("25/11/2026 12:00:00",now=1800000000),1795588200)
        for value in ("01/01/1980 00:00:00","01/01/2099 00:00:00","31/02/2026 12:00:00","1980-01-01 00:00:00","2099-01-01 00:00:00",None,123,"invalid"):
            self.assertIsNone(observed_trade_timestamp(value,now=1800000000))
    def test_quote_metadata_stays_unverified_and_compatible(self):
        prices=QuotePriceBatch()
        prices["NIFTY"]=25000.0
        prices.trade_timestamps["NIFTY"]=1795588200
        self.assertEqual(prices,{"NIFTY":25000.0})
        self.assertEqual(observed_quote_fields(prices,"NIFTY")["quote_timestamp"],1795588200)
        self.assertFalse(observed_quote_fields(prices,"NIFTY")["live_verified"])
        self.assertIsNone(observed_quote_fields({"NIFTY":25000.0},"NIFTY")["quote_timestamp"])

    def test_adapter_timestamp_rejects_invalid_or_unowned_metadata(self):
        from unittest.mock import patch
        prices=QuotePriceBatch()
        prices["NIFTY"]=25000.0
        with patch("clone_v2_gateway.time.time",return_value=1800000000):
            for invalid in (True,1,946684799,1800000001,float("nan"),"1795588200",None):
                prices.trade_timestamps["NIFTY"]=invalid
                self.assertIsNone(observed_quote_fields(prices,"NIFTY")["quote_timestamp"])
            prices.trade_timestamps["TCS"]=1795588200
            self.assertIsNone(observed_quote_fields(prices,"TCS")["quote_timestamp"])
            prices.trade_timestamps["NIFTY"]=1795588200
            self.assertEqual(observed_quote_fields(prices,"NIFTY")["quote_timestamp"],1795588200)

    def test_shared_doctor_timestamp_is_observed_not_live(self):
        from v3_smart_active_doctor import quote_timestamp_observation
        q=dict(source="Dhan",symbol="NIFTY",quote_timestamp=1795588200)
        report=quote_timestamp_observation(symbol="NIFTY",quote=q,now=1800000000)
        self.assertTrue(report["timestamp_observed"])
        self.assertFalse(report["source_live_verified"])
        for changed in (dict(q,symbol="TCS"),dict(q,source="Yahoo Finance"),
                        dict(q,quote_timestamp=1),dict(q,quote_timestamp=1800000001)):
            report=quote_timestamp_observation(symbol="NIFTY",quote=changed,now=1800000000)
            self.assertEqual(report["code"],"BK-QUOTE-TIME-001")
            self.assertIsNone(report["timestamp_age_seconds"])
        source=(root/"src/main.py").read_text()
        self.assertIn('"quote_timestamp_observation":__import__',source)
        self.assertIn('quote_time_observation=__import__',source)

    def test_restored_quote_rows_cannot_carry_live_authority(self):
        from v3_market_display_mode import restored_quote_rows
        original=dict(source="Dhan",symbol="NIFTY",price=25000.0,
                      quote_timestamp=1795588200,freshness="exchange_verified",live_verified=True)
        rows=restored_quote_rows({"NIFTY":original,"TCS":dict(original),
            "INFY":dict(original,symbol="INFY",source="Yahoo Finance"),
            "SBIN":dict(original,symbol="SBIN",price=True)},source="Dhan")
        self.assertEqual(set(rows),{"NIFTY"})
        self.assertEqual(rows["NIFTY"]["price"],25000.0)
        self.assertEqual(rows["NIFTY"]["quote_timestamp"],1795588200)
        self.assertTrue(rows["NIFTY"]["cached"])
        self.assertFalse(rows["NIFTY"]["live_verified"])
        self.assertEqual(rows["NIFTY"]["freshness"],"unverified")
        self.assertTrue(original["live_verified"])
        from v3_smart_active_doctor import quote_timestamp_observation
        report=quote_timestamp_observation(symbol="NIFTY",quote=rows["NIFTY"],now=1800000000)
        self.assertEqual(report["quote_session_scope"],"RESTORED_CACHE")
        self.assertFalse(report["source_live_verified"])

    def test_startup_and_provider_reset_use_same_restore_guard(self):
        source=(root/"src/main.py").read_text()
        self.assertIn('quotes=restored_quote_rows(market_store.latest_markets(), source="Dhan")',source)
        self.assertIn('quotes.update(restored_quote_rows(previous_quotes,source=cached_source))',source)
        self.assertIn('quotes.update(restored_quote_rows(market_store.latest_markets(),source=cached_source))',source)
        self.assertIn('q.get("live_verified") is not True or q.get("cached") is True',source)
