"""STANDARD-2: normal dashboard caches publish exact-frame HIST, Doctors stay read-only."""
import ast
import pathlib
import unittest

SOURCE=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
TREE=ast.parse(SOURCE)
FUNCTIONS={n.name:n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef)}
def body(name):
    return ast.get_source_segment(SOURCE,FUNCTIONS[name])

class CachedHistoricalPublisherTests(unittest.TestCase):
    def test_normal_ui_hydrates_exact_frame_only(self):
        publisher=body("ensure_cached_historical_engine_publish")
        chips=body("five_engine_chips")
        self.assertIn("ensure_cached_historical_engine_publish(sym,display_timeframe)",chips)
        self.assertIn('tf not in ("1m","3m")',publisher)
        self.assertIn('history.get("_scanner_timeframe")!=tf',publisher)
        self.assertIn("historical_regular_session_bars(original,tf)",publisher)
        self.assertIn("valid_candle_history(completed)",publisher)
        self.assertIn("quality_check(completed,seconds,",publisher)
        self.assertIn("contextual_five_engine.peek(",publisher)
        self.assertIn("publish_five_engine_historical(sym,tf,dict(",publisher)
        self.assertIn('live_verified=False',publisher)
        self.assertNotIn("get_market_data(",publisher)
    def test_doctors_cannot_fabricate_live_or_write_publisher(self):
        for name in ("filter_five_diagnostic_panel","all_segments_doctor_panel"):
            if name in FUNCTIONS:
                self.assertNotIn("publish_five_engine_historical(",body(name))
        self.assertIn('market_open=True',body("read_five_engine_context"))
        self.assertIn('live_verified") is not False',body("publish_five_engine_historical"))
if __name__=="__main__": unittest.main()
