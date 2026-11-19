"""V2 native Scanner history 15/35/70 bars persists and backs up safely."""
import json
import sys
import unittest
from pathlib import Path
SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_state import LocalWatchlists
from scanner_state import ScannerSelection
from smart_data import SmartDataSettings
from local_analysis_slots import LocalAnalysisSlots
from chart_window import WINDOWS
from local_settings_backup import export_local_backup, parse_local_backup, LocalBackupError

class PersistentHistoryWindow(unittest.TestCase):
    def setUp(self):
        self.w = LocalWatchlists()
        self.w.add(0, "TCS")
        self.scanner = ScannerSelection("TCS", "3m")
        self.smart = SmartDataSettings()
        self.slots = LocalAnalysisSlots(["NIFTY", "TCS", "NIFTY"])

    def test_roundtrip_each_history_window_and_schema3(self):
        for window in WINDOWS:
            with self.subTest(history_bars=window):
                exported = export_local_backup(
                    self.w, self.scanner, self.smart, self.slots,
                    chart_style="Candles", chart_window=window)
                doc = json.loads(exported)
                self.assertEqual(doc["schema_version"], 3)
                self.assertEqual(doc["chart_window"], window)
                sections = parse_local_backup(exported)
                self.assertEqual(len(sections), 6)
                self.assertEqual(sections[4:], ("Candles", window))
                self.assertEqual(sections[0].selected, ("TCS",))

    def test_legacy_backups_never_reset_unmentioned_history(self):
        old1 = export_local_backup(
            self.w, self.scanner, self.smart, self.slots)
        old2 = export_local_backup(
            self.w, self.scanner, self.smart, self.slots,
            chart_style="Line")
        self.assertEqual(len(parse_local_backup(old1)), 4)
        self.assertEqual(len(parse_local_backup(old2)), 5)

    def test_invalid_window_and_secret_fields_never_restore(self):
        good = json.loads(export_local_backup(
            self.w, self.scanner, self.smart, self.slots,
            chart_style="Candles", chart_window=35))
        for key, value in (("chart_window", 12), ("chart_window", "35"),
                           ("chart_window", True), ("schema_version", 5),
                           ("api_key", "PRIVATE"), ("oracle_url", "https://example.test")):
            with self.subTest(key=key, value=value):
                mutated = dict(good, **{key: value})
                with self.assertRaises(LocalBackupError):
                    parse_local_backup(json.dumps(mutated))
        with self.assertRaises(LocalBackupError):
            export_local_backup(
                self.w, self.scanner, self.smart, self.slots, chart_window=15)

    def test_main_saves_restores_window_without_provider_requests(self):
        main = (SRC / "main.py").read_text(encoding="utf-8")
        for needle in (
            'chart_window_key = "botking.v2.chart_window.v1"',
            "def save_chart_window():",
            "page.client_storage.set(chart_window_key, chart_window[0])",
            "new_chart_window = restored[5] if len(restored) >= 6 else None",
            "chart_window[0] = new_chart_window",
            "chart_window=chart_window[0]",
            "save_chart_window()",
            "chart_window[0] = window_from_dropdown(e.control.value)",
        ):
            self.assertIn(needle, main)
        for old in ("ServerAngelFeed(", "get_yahoo(", "submit_order("):
            self.assertNotIn(old, main)

if __name__ == "__main__":
    unittest.main()
