"""Last-good Watchlist price remains HIST after an intraday Dhan link loss.

Actual Flet app_main runtime; read-only injected Dhan candle, no provider IO.
"""
import pathlib
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/"src"),str(ROOT/"tests")]
from test_audit import start
IST=timezone(timedelta(hours=5,minutes=30))

class IntradayLastGoodWatchlist(unittest.TestCase):
    def test_disconnected_last_completed_3m_price_is_hist_not_blank(self):
        _,ui=start({"source":"Dhan","scanner_live":False})
        sym="RELIANCE"
        # Prior completed historical data is retained in the exact frame.
        start_stamp=int((datetime.now(IST)-timedelta(days=1)).replace(
            hour=11,minute=27,second=0,microsecond=0).timestamp())
        data={"source":"Dhan","_scanner_timeframe":"3m",
              "bars":[[start_stamp,100,104,99,103.5,500]],
              "historical":True,"live_verified":False}
        ui["chart_snapshots"][(sym,"3m",ui["provider_generation"][0])]=data
        self.assertFalse(ui["dhan_feed"].connected)
        price,caption=ui["watch_price_and_status"](sym)
        self.assertEqual(price,"HIST 103.50")
        self.assertIn("NOT LIVE",caption)
        self.assertIn("HIST CLOSE",caption)

    def test_missing_last_valid_data_is_not_fabricated(self):
        _,ui=start({"source":"Dhan","scanner_live":False})
        price,caption=ui["watch_price_and_status"]("RELIANCE")
        self.assertEqual(price,"—")
        self.assertIsNone(caption)

if __name__=="__main__":unittest.main()
