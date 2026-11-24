"""SSK authenticated HIST access is not an exchange-verified LIVE quote session."""
import pathlib
import unittest

MAIN=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")

class HolidayConnectionStatusWording(unittest.TestCase):
    def test_scanner_live_final_differentiates_authenticated_gateway(self):
        self.assertIn("LIVE quote/session unverified • 0/5 verified", MAIN)
        self.assertIn('if prefs.get("source")!="Dhan" or not dhan_feed.connected:', MAIN)
        self.assertIn('0/5 verified', MAIN)

    def test_header_and_options_do_not_call_authenticated_holiday_gateway_disconnected(self):
        self.assertIn("SSK/Oracle CONNECTED • HIST candles available separately", MAIN)
        self.assertIn("LIVE option snapshot not verified • HIST Scanner remains available", MAIN)
        self.assertIn("historical source separate • LIVE evidence unverified", MAIN)

    def test_live_and_hist_gates_remain_distinct(self):
        self.assertIn('if not (dhan_feed.connected or closed_hist_gateway):', MAIN)
        self.assertIn('and not (clone_v2_gateway.connected and not regular_hours())', MAIN)
        self.assertIn('if prefs.get("source")!="Dhan" or not dhan_feed.connected:',MAIN)

if __name__=="__main__":
    unittest.main()
