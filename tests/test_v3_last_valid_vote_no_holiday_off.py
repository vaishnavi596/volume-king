"""Do not guess holiday status or rewind a valid retained technical/candle vote."""
import ast
from pathlib import Path
import unittest
SOURCE=(Path(__file__).resolve().parents[1]/"src/main.py").read_text()
TREE=ast.parse(SOURCE)

def source_of(name):
    nodes=[n for n in ast.walk(TREE) if isinstance(n,ast.FunctionDef) and n.name==name]
    assert len(nodes)==1,(name,len(nodes))
    return ast.get_source_segment(SOURCE,nodes[0])

class LastValidDisplayContract(unittest.TestCase):
    def test_five_box_unavailable_remains_wait_not_calendar_off(self):
        chips=source_of("five_engine_chips")
        self.assertIn('label=short+" WAIT"',chips)
        self.assertNotIn('label=short+" OFF"',chips)
        self.assertIn('completed_timeframe_candle_balance',chips)
        self.assertIn('historical_five_minute_technical',chips)
        self.assertNotIn('if not regular_hours() and "WAIT" in label',chips)
    def test_live_requires_fresh_authenticated_cache(self):
        reader=source_of("read_five_engine_context")
        self.assertIn('dhan_feed.connected',reader)
        self.assertIn('now=time.time()',reader)
        self.assertIn('provider_generation[0]',reader)
        self.assertIn('market_open=True',reader)
    def test_no_manual_holiday_display_mode(self):
        self.assertIn('market_display_choice=ft.Text(',SOURCE)
        self.assertNotIn('market_display_choice=ft.Dropdown(',SOURCE)

if __name__=="__main__":unittest.main()
