"""STANDARD-2 Master Doctor must use the same historical source window."""
import ast
import pathlib
import unittest

SRC=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SRC)

class MasterDoctorHistoricalParityTests(unittest.TestCase):
    def test_master_scanner_uses_shared_hist_window(self):
        self.assertIn("scanner_hist_bars=(historical_regular_session_bars(scanner_bars,scanner_tf)",SRC)
        self.assertIn('scanner_data.get("_scanner_timeframe")==scanner_tf',SRC)
        self.assertIn("scanner_hist_result=(analyze(scanner_hist_bars,",SRC)
        self.assertIn("scanner_rows=complete_filter_rows(\n                    scanner_hist_result,",SRC)
        # Neither master nor B178 changes the original raw provider series.
        self.assertIn('diagnostic_bars=(historical_regular_session_bars(bars,tf)',SRC)
        self.assertIn("diagnostic_hist_bars=(historical_regular_session_bars(",SRC)
    def test_verified_engine_proof_is_still_independent(self):
        self.assertIn("scanner_engine_frame_eligible=(scanner_tf in",SRC)
        self.assertIn("and regular_hours())",SRC)
        self.assertIn('"verified_boxes":sum(x["verified_directional_percent_available"]',SRC)

if __name__=="__main__":unittest.main()
