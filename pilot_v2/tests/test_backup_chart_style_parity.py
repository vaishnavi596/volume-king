"""V2 chart-style backup upgrade: strict schema 2, legacy 1 still accepted."""
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
from local_settings_backup import (
    export_local_backup, parse_local_backup, LocalBackupError)

class BackupChartStyleParity(unittest.TestCase):
    def setUp(self):
        self.watch = LocalWatchlists()
        self.watch.add(0, "TCS")
        self.scanner = ScannerSelection("TCS", "3m")
        self.smart = SmartDataSettings()
        self.slots = LocalAnalysisSlots(["NIFTY", "TCS", "NIFTY"])

    def test_v2_backup_roundtrip_style_and_every_local_section(self):
        for style in ("Candles", "Line"):
            with self.subTest(style=style):
                blob = export_local_backup(
                    self.watch, self.scanner, self.smart, self.slots,
                    chart_style=style)
                saved = json.loads(blob)
                self.assertEqual(saved["schema_version"], 2)
                self.assertEqual(saved["chart_style"], style)
                output = parse_local_backup(blob)
                self.assertEqual(len(output), 5)
                self.assertEqual(output[0].groups, self.watch.groups)
                self.assertEqual(output[1], self.scanner)
                self.assertEqual(output[2], self.smart)
                self.assertEqual(output[3].slots, self.slots.slots)
                self.assertEqual(output[4], style)
                self.assertNotIn("api_key", blob.lower())
                self.assertNotIn("token", blob.lower())

    def test_existing_v1_backup_stays_readable_without_style_reset(self):
        old = export_local_backup(
            self.watch, self.scanner, self.smart, self.slots)
        self.assertEqual(json.loads(old)["schema_version"], 1)
        self.assertEqual(len(parse_local_backup(old)), 4)

    def test_invalid_backup_style_or_credentials_rejected(self):
        data = json.loads(export_local_backup(
            self.watch, self.scanner, self.smart, self.slots,
            chart_style="Candles"))
        for key, value in (("chart_style", "WebView"), ("chart_style", None),
                           ("schema_version", 3), ("api_key", "SECRET"),
                           ("server_url", "https://example.test")):
            candidate = dict(data, **{key: value})
            with self.subTest(key=key, value=value), self.assertRaises(LocalBackupError):
                parse_local_backup(json.dumps(candidate))
        with self.assertRaises(ValueError):
            export_local_backup(self.watch, self.scanner, self.smart,
                                self.slots, chart_style="unknown")

    def test_ui_restore_wires_both_v1_and_v2_without_overwrite(self):
        main = (SRC / "main.py").read_text(encoding="utf-8")
        self.assertIn("new_chart_style = restored[4] if len(restored) >= 5 else None", main)
        self.assertIn("if new_chart_style is not None:", main)
        self.assertIn("chart_style[0] = new_chart_style", main)
        self.assertIn("save_chart_style()", main)
        self.assertIn("chart_style=chart_style[0]", main)

if __name__ == "__main__":
    unittest.main()
