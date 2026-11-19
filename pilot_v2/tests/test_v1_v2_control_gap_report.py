"""V1 UI controls machine-checkable in existing single CI migration gap report."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "v2_ui_gap_gate", ROOT / "tools" / "one_click_migration_gate.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class SourceControlGapTests(unittest.TestCase):
    def test_read_only_v1_source_and_v2_controls(self):
        rows = {name: (v1, v2) for name, v1, v2 in gate.control_parity()}
        self.assertEqual(len(rows), len(gate.V1_CONTROL_GAPS))
        for key in ("Scanner show/hide chart control",
                    "Scanner native line/candle style",
                    "Scanner selected timeframe",
                    "Expiry selection UI", "Native historical chart"):
            with self.subTest(key=key):
                self.assertEqual(rows[key], (True, True))
        for key in ("Rich chart WebView",
                    "Verified real-time visible chart sync",
                    "Scanner automatic market refresh"):
            with self.subTest(key=key):
                self.assertEqual(rows[key], (True, False))

    def test_migrated_control_regression_fails_gate(self):
        baseline = gate.control_parity()
        self.assertGreaterEqual(len(baseline), 8)
        broken = ((baseline[0][0], True, False),) + baseline[1:]
        with patch.object(gate, "control_parity", return_value=broken):
            audit = gate.audit()
        self.assertIn("Regressed V2 local UI control: " + baseline[0][0],
                      audit["issues"])

    def test_pending_live_capabilities_do_not_fail_source_gate(self):
        audit = gate.audit()
        self.assertFalse(any("Regressed V2 local UI control" in item
                             for item in audit["issues"]))
        self.assertEqual(sum(bool(v2) for _, _, v2 in audit["control_parity"][:5]), 5)

    def test_report_not_completed_by_source_match(self):
        report = gate.audit()
        self.assertTrue(any(row[0] == "Rich chart WebView"
                            and row[2] is False
                            for row in report["control_parity"]))
        self.assertGreater(len(report["pending_external"]), 0)

if __name__ == "__main__":
    unittest.main()
