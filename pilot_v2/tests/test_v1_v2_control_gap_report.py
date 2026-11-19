"""V1 UI controls machine-checkable in existing single CI migration gap report."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v2_ui_gap_gate", ROOT / "tools" / "one_click_migration_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class SourceControlGapTests(unittest.TestCase):
    def test_read_only_v1_source_and_v2_controls(self):
        rows = {name: (v1, v2) for name, v1, v2 in gate.control_parity()}
        self.assertEqual(len(rows), len(gate.V1_CONTROL_GAPS))
        for key in ("Scanner native line/candle style",
                    "Scanner selected timeframe",
                    "Expiry selection UI", "Native historical chart"):
            with self.subTest(key=key):
                self.assertEqual(rows[key], (True, True))
        for key in ("Rich chart WebView",
                    "Verified real-time visible chart sync",
                    "Scanner automatic market refresh"):
            with self.subTest(key=key):
                self.assertEqual(rows[key], (True, False))

    def test_report_not_completed_by_source_match(self):
        report = gate.audit()
        self.assertTrue(any(row[0] == "Rich chart WebView"
                            and row[2] is False
                            for row in report["control_parity"]))
        self.assertGreater(len(report["pending_external"]), 0)

if __name__ == "__main__":
    unittest.main()
