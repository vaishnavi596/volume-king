"""Joint app-side 0/5/70 demand, five timeframes and source-gated views."""
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_state import LocalWatchlists
from scanner_state import ScannerSelection
from smart_data import SmartDataSettings
from feed_inbox import DeviceFeedInbox
from evidence_inbox import DeviceEvidenceInbox
from historical_three_minute_fallback import HistoricalThreeMinuteFallback
from app_data_readiness import joint_data_readiness, data_readiness_label


class JointAppDataReadiness(unittest.TestCase):
    def test_all_five_timeframes_and_adaptive_0_5_70_unique_roster(self):
        for count in (0, 5, 70):
            w = LocalWatchlists()
            for i in range(count):
                w.add(i % 5, f"EQ{i:03}")
            for tf in ("1m", "3m", "5m", "15m", "30m"):
                with self.subTest(count=count, timeframe=tf):
                    quotes, evidence = DeviceFeedInbox(), DeviceEvidenceInbox()
                    state = joint_data_readiness(
                        w, ScannerSelection("NIFTY", tf), SmartDataSettings(),
                        quotes, evidence,
                        HistoricalThreeMinuteFallback(evidence.candles))
                    self.assertEqual(state["equity_count"], count)
                    self.assertEqual(len(state["equities"]), count)
                    self.assertEqual(state["requested_quote_symbols"], count + 3)
                    self.assertEqual(state["candle_status"], "WAIT")
                    self.assertEqual(state["quote_status"], "WAIT")
                    self.assertEqual(state["filter_coverage"], 0)
                    self.assertEqual(state["sixth_filter"], ("", ""))
                    self.assertEqual(state["expiry_status"], "WAIT")
                    self.assertEqual(state["super_five_status"], "WAIT")
                    self.assertFalse(state["live_verified"])
                    self.assertFalse(state["gateway_connected"])
                    self.assertEqual(state["network_requests"], 0)
                    self.assertIn("Oracle not connected", data_readiness_label(state))

    def test_scanner_unselected_symbol_fails_closed(self):
        w = LocalWatchlists()
        evidence = DeviceEvidenceInbox()
        with self.assertRaises(ValueError):
            joint_data_readiness(
                w, ScannerSelection("TCS", "1m"), SmartDataSettings(),
                DeviceFeedInbox(), evidence,
                HistoricalThreeMinuteFallback(evidence.candles))

    def test_same_model_shared_across_dashboard_scanner_settings(self):
        main = (SRC / "main.py").read_text()
        self.assertIn("from app_data_readiness import", main)
        self.assertIn("joint_data_readiness(", main)
        self.assertGreaterEqual(main.count("data_readiness_label("), 2)
        self.assertIn("Verified data: WAIT", main)
        self.assertNotIn("ServerAngelFeed", main)
        self.assertNotIn("get_yahoo(", main)

if __name__ == "__main__":
    unittest.main()
