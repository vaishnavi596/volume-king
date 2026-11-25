"""STANDARD-2: both phone Doctors reuse the exact historical display window."""
import ast, pathlib, unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
SRC=(ROOT/"src/main.py").read_text(encoding="utf-8")
TREE=ast.parse(SRC)
class HistoricalDoctorParityTests(unittest.TestCase):
    def test_b178_and_b147_share_historical_session_window(self):
        self.assertIn("diagnostic_bars=(historical_regular_session_bars(bars,tf)",SRC)
        self.assertIn("completed_bars=([bar for bar in diagnostic_bars",SRC)
        self.assertIn("if isinstance(diagnostic_bars,(list,tuple)) else [])",SRC)
        self.assertIn("diagnostic_hist_bars=(historical_regular_session_bars(",SRC)
        self.assertIn("diagnostic_analysis=(await local_analysis_pool.run(diagnostic_analyze,",SRC)
        # Inspection must not publish a fake scanner/engine snapshot.
        doctor=next(n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef)
                    and n.name=="filter_five_diagnostic_panel")
        code=ast.get_source_segment(SRC,doctor)
        self.assertNotIn("publish_five_engine_historical(",code)
        self.assertNotIn("get_market_data(",code)
    def test_hist_selection_does_not_change_live_gate(self):
        self.assertIn('diagnostic_context["exact_frame_snapshot_published"]=bool(exact_published_snapshot)',SRC)
        self.assertIn('"NO_EXACT_FRAME_PUBLISH" if not exact_published_snapshot',SRC)
        self.assertIn('snapshot_read_gate',SRC)
if __name__=="__main__":unittest.main()
