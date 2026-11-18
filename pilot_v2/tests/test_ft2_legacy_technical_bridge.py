"""First V1 engines connected to V2 validated candle cache and Flet Scanner."""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone
ROOT = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(ROOT))
from evidence_inbox import DeviceEvidenceInbox
from legacy_technical_bridge import historical_scanner_analysis


def series(count=36, start=None):
    if start is None:
        start = int(datetime(2026, 11, 18, 4, 0, tzinfo=timezone.utc).timestamp())
    result = []
    for i in range(count):
        value = 101.0 + i * .22
        result.append({"timestamp": start + i * 60, "open": value,
                       "high": value + 1.4, "low": value - 1.4,
                       "close": value + .3, "volume": 100 + i,
                       "completed": True})
    return result


class LegacyTechnicalBridgeTests(unittest.TestCase):
    def setUp(self):
        self.app = DeviceEvidenceInbox()

    def test_no_candles_do_not_create_votes(self):
        value = historical_scanner_analysis(self.app.candles, "NIFTY", "1m")
        self.assertEqual(value["status"], "WAIT")
        self.assertIsNone(value["scan"])
        self.assertEqual(self.app.filters.rows("NIFTY", "1m")[4][1], "WAIT")

    def test_real_v1_chart_and_scanner_engines_run_for_completed_history(self):
        self.app.apply_candles("NIFTY", "1m", 1, series(),
                               trusted_transport=True)
        value = historical_scanner_analysis(self.app.candles, "NIFTY", "1m")
        self.assertEqual(value["status"], "HIST")
        self.assertEqual(value["indicators"]["status"], "AVAILABLE")
        self.assertEqual(value["scan"]["count"], 36)
        self.assertIn("not live/5-filter score", value["summary"])
        self.assertEqual(self.app.filters.rows("NIFTY", "1m")[4][1], "WAIT")
        self.assertEqual(historical_scanner_analysis(
            self.app.candles, "NIFTY", "3m")["status"], "WAIT")

    def test_selected_equity_only_and_unselected_peer_wait(self):
        self.app.apply_candles("TCS", "1m", 1, series(),
                               selected_equities=("TCS",),
                               trusted_transport=True)
        self.assertEqual(historical_scanner_analysis(
            self.app.candles, "TCS", "1m", selected_equities=("TCS",))["status"], "HIST")
        self.assertEqual(historical_scanner_analysis(
            self.app.candles, "TCS", "1m")["status"], "WAIT")
        self.assertEqual(historical_scanner_analysis(
            self.app.candles, "INFY", "1m", selected_equities=("TCS",))["status"], "WAIT")

    def test_incomplete_candles_fail_without_breaking_last_good(self):
        self.app.apply_candles("NIFTY", "1m", 1, series(),
                               trusted_transport=True)
        with self.assertRaises(ValueError):
            self.app.apply_candles("NIFTY", "1m", 2, series()[:-1] +
                [dict(series()[-1], completed=False)], trusted_transport=True)
        self.assertEqual(historical_scanner_analysis(
            self.app.candles, "NIFTY", "1m")["status"], "HIST")

    def test_real_flet_scanner_calls_engine_bridge(self):
        source=(ROOT / "main.py").read_text()
        self.assertIn("from legacy_technical_bridge import historical_scanner_analysis", source)
        self.assertIn('historical_scanner_analysis(', source)
        self.assertIn('scanner[0].symbol, scanner[0].timeframe,', source)
        self.assertNotIn("from server_feed import", source)
        self.assertNotIn("from market_feed import", source)


if __name__ == "__main__":
    unittest.main()
