"""One run must produce an evidence-based progress report, not a fake complete."""
import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "tools" / "one_click_migration_gate.py"
spec = importlib.util.spec_from_file_location("v2_gap_gate", PATH)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)

class OneRunGateTests(unittest.TestCase):
    def test_missing_live_evidence_never_promotes_complete(self):
        data = gate.audit()
        self.assertGreaterEqual(data["active_module_count"], 40)
        self.assertEqual(len(data["pending_external"]), 8)
        self.assertTrue(data["wired"]["Watchlist + 70 unique equity selection"])
        self.assertTrue(data["wired"]["Scanner + Super Five shared historical chart"])
        with tempfile.TemporaryDirectory() as temp:
            prior = gate.REPORT
            try:
                gate.REPORT = Path(temp) / "audit.md"
                self.assertFalse(gate.write_report(data, strict=False))
                self.assertTrue(gate.write_report(data, strict=True))
                text = gate.REPORT.read_text(encoding="utf-8")
                self.assertIn("NOT COMPLETE", text)
                self.assertIn("Separate mandatory acceptance still pending", text)
                self.assertIn("- App + device + provider migration: NOT COMPLETE", text)
            finally:
                gate.REPORT = prior

    def test_direct_legacy_import_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            unsafe = Path(temp) / "src"
            unsafe.mkdir()
            (unsafe / "main.py").write_text("import market_feed\n")
            old = gate.V2
            try:
                gate.V2 = unsafe
                result = gate.audit()
                self.assertTrue(any("Blocked import" in issue for issue in result["issues"]))
            finally:
                gate.V2 = old

if __name__ == "__main__":
    unittest.main()
