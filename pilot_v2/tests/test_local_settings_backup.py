"""V2 local-only Backup/Restore: exact schema and no server secrets."""
import ast
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
from local_settings_backup import (export_local_backup, parse_local_backup,
                                   LocalBackupError)


class LocalSettingsBackupTests(unittest.TestCase):
    def setUp(self):
        self.w = LocalWatchlists()
        self.w.add(0, "TCS")
        self.w.add(1, "INFY")
        self.scanner = ScannerSelection("TCS", "3m")
        self.smart = SmartDataSettings(False, 300)
        self.analysis = LocalAnalysisSlots(["NIFTY", "TCS", "INFY"])

    def test_full_local_roundtrip_and_no_secrets_or_server_settings(self):
        exported = export_local_backup(self.w, self.scanner, self.smart, self.analysis)
        self.assertNotIn("token", exported.lower())
        self.assertNotIn("api_key", exported.lower())
        self.assertNotIn("server", exported.lower())
        w, sc, smart, slots = parse_local_backup(exported)
        self.assertEqual(w.groups[0], ["TCS"])
        self.assertEqual(w.groups[1], ["INFY"])
        self.assertEqual(sc, self.scanner)
        self.assertEqual(smart.saved_state(), self.smart.saved_state())
        self.assertEqual(slots.slots, self.analysis.slots)

    def test_wrong_schema_and_extraneous_credentials_fail_closed(self):
        base = json.loads(export_local_backup(
            self.w, self.scanner, self.smart, self.analysis))
        for name, value in (("api_key", "SECRET"), ("source", "Yahoo"),
                            ("server_url", "https://example.test")):
            changed = dict(base)
            changed[name] = value
            with self.subTest(name=name), self.assertRaises(LocalBackupError):
                parse_local_backup(json.dumps(changed))
        for value in (None, "", "{}", '{"foo":1}', "x"*16385):
            with self.assertRaises(LocalBackupError):
                parse_local_backup(value)

    def test_reject_removed_scanner_analysis_and_duplicate_watchlists(self):
        base = json.loads(export_local_backup(
            self.w, self.scanner, self.smart, self.analysis))
        changed = json.loads(json.dumps(base))
        changed["watchlists"]["watchlists"][0] = []
        with self.assertRaises(LocalBackupError):
            parse_local_backup(json.dumps(changed))
        changed = json.loads(json.dumps(base))
        changed["watchlists"]["watchlists"][0].append("INFY")
        with self.assertRaises(LocalBackupError):
            parse_local_backup(json.dumps(changed))

    def test_real_settings_wiring_and_three_bottom_tabs(self):
        src = (SRC / "main.py").read_text()
        ast.parse(src)
        for needle in ("from local_settings_backup import",
                       "def prepare_local_backup(e):",
                       "def restore_local_backup(e):",
                       "parse_local_backup(backup_text[0])",
                       "export_local_backup(",
                       "state, scanner[0], smart[0], analysis_slots[0],",
                       "chart_style=chart_style[0]",
                       'ft.TextButton("Prepare local backup"',
                       'ft.TextButton("Restore local preferences"',
                       'label="Confirm local-only restore"'):
            self.assertIn(needle, src)
        self.assertEqual(src.count("ft.NavigationDestination("), 3)
        self.assertNotIn("get_yahoo(", src)
        self.assertNotIn("ServerAngelFeed(", src)

if __name__ == "__main__":
    unittest.main()
