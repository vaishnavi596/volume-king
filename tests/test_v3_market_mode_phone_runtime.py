"""Actual Flet app_main mode change: retained HIST vs guarded LIVE boxes.

Offline only. No Dhan requests, no broker orders or Oracle mutations.
"""
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"tests"))
from test_audit import start,event

class MarketModePhoneRuntime(unittest.TestCase):
    def test_persisted_mode_and_live_final_scope(self):
        page,ui=start({"source":"Dhan","scanner_live":False})
        self.assertEqual(ui["prefs"]["market_display_mode"],"AUTO")
        control=ui["market_display_choice"]
        control.value="HISTORICAL"
        control.on_change(event(control))
        self.assertEqual(ui["prefs"]["market_display_mode"],"HISTORICAL")
        self.assertIn("HISTORICAL ONLY",ui["session_caption"]())
        self.assertIn("DISABLED BY HISTORICAL MODE",
                      ui["canonical_live_final_note"]("NIFTY","1m").value)
        self.assertNotIn("HIDDEN BY LIVE ONLY",
                         ui["scanner_historical_final_vote"]("NIFTY","1m").value)
        self.assertEqual(page.client_storage.get("bot_king_preferences")["market_display_mode"],
                         "HISTORICAL")
        _,reboot=start(page.client_storage.get("bot_king_preferences"))
        self.assertEqual(reboot["prefs"]["market_display_mode"],"HISTORICAL")

    def test_live_only_excludes_historical_final_and_historical_chips(self):
        _,ui=start({"source":"Dhan","scanner_live":False,
                    "market_display_mode":"LIVE_ONLY"})
        self.assertIn("HIDDEN BY LIVE ONLY MODE",
                      ui["scanner_historical_final_vote"]("NIFTY","1m").value)
        self.assertNotIn("HIST",ui["five_engine_summary"]("NIFTY","1m").value)
        # No independent publisher evidence or authenticated quote: chips stay WAIT.
        chips=ui["five_engine_chips"]("NIFTY","1m")
        labels=[str(chip.content.value) for row in chips.controls
                for chip in row.controls[:3]][:5]
        self.assertFalse(any(" HIST " in label for label in labels),labels)
        self.assertIn("LIVE",ui["session_caption"]())

    def test_scanner_open_day_historical_mode_suppresses_live_and_setup(self):
        # Test the actual scanner nested function's safety contract.
        import ast
        source=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        matches=[n for n in ast.walk(ast.parse(source))
                 if isinstance(n,ast.AsyncFunctionDef) and n.name=="scan_market"]
        self.assertEqual(len(matches),1)
        body=ast.get_source_segment(source,matches[0])
        self.assertIn('historical_mode_selected=(prefs.get("market_display_mode")=="HISTORICAL")',body)
        self.assertIn('or historical_mode_selected',body)
        self.assertIn('and not historical_mode_selected',body)
        self.assertIn('hist.get("live_verified") is True',body)
        self.assertIn('hist.get("freshness")=="exchange_verified"',body)
        self.assertIn('advanced=dict(advanced,bias="WAIT",score=0',body)

    def test_invalid_saved_mode_defaults_auto(self):
        _,ui=start({"source":"Dhan","scanner_live":False,
                    "market_display_mode":"INVALID"})
        self.assertEqual(ui["prefs"]["market_display_mode"],"AUTO")

if __name__=="__main__":
    unittest.main()
