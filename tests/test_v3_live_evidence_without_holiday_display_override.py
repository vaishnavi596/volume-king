"""LIVE presentation uses verified Dhan evidence, not holiday-calendar inference."""
import ast
import pathlib
import unittest

SOURCE=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
TREE=ast.parse(SOURCE)
def fn(name):
    nodes=[n for n in ast.walk(TREE) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return ast.get_source_segment(SOURCE,nodes[0])

class LiveEvidenceNoCalendarDisplayOverride(unittest.TestCase):
    def test_contextual_reader_checks_connected_and_time_provenance_not_calendar(self):
        source=fn("read_five_engine_context")
        self.assertIn('and dhan_feed.connected',source)
        self.assertIn('now=time.time()',source)
        self.assertIn('market_open=True',source)
        self.assertNotIn('market_open=regular_hours()',source)

    def test_live_final_requires_connection_and_cache_quorum(self):
        source=fn("canonical_live_final_note")
        self.assertIn('not dhan_feed.connected',source)
        self.assertIn('read_five_engine_context(symbol,timeframe)',source)
        self.assertNotIn('or not regular_hours()',source)

    def test_all_five_slots_can_use_fresh_verified_cache_and_hist_fallback(self):
        for name in ("five_engine_summary","five_engine_chips"):
            source=fn(name)
            self.assertNotIn('snapshot=snapshot_for_display(None,now=time.time())',source)
            self.assertIn('read_five_engine_context(',source)
        self.assertIn('completed_timeframe_candle_balance',fn("five_engine_chips"))
        self.assertIn('historical_five_minute_technical',fn("five_engine_summary"))

if __name__=="__main__":
    unittest.main()
