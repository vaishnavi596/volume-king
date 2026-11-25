import unittest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from dhan_multi_timeframe import completed_derived_bars
class SharedRecovery(unittest.TestCase):
    def test_five_minute_requires_complete_session_bucket(self):
        start=int(datetime(2026,11,23,9,15,tzinfo=timezone(timedelta(hours=5,minutes=30))).timestamp())
        rows=[[start+i*60,100+i,102+i,99+i,101+i,10] for i in range(5)]
        self.assertEqual(completed_derived_bars(rows,"5m",now_epoch=start+300),[(start,100,106,99,105,50)])
        self.assertEqual(completed_derived_bars(rows[:-1],"5m",now_epoch=start+300),[])
        self.assertEqual(completed_derived_bars(rows,"5m",now_epoch=start+299),[])
    def test_ssk_options_bounded_and_unverified(self):
        src=(Path(__file__).resolve().parents[1]/"src/main.py").read_text()
        self.assertIn("option_ssk_attempted.add(option_key)",src)
        self.assertIn("not in option_ssk_attempted",src)
        self.assertIn('or "424" in detail',src)
        self.assertIn("await asyncio.sleep(3.25)",src)
        self.assertIn('freshness="historical_unverified",candle_transport_integrity="DERIVED_FROM_1M_UNVERIFIED"',src)
