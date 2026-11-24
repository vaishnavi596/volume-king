"""Real Flet app: automatic source-aware LIVE/HIST display, no manual third mode."""
import ast
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
sys.path.insert(0,str(ROOT/"tests"))
from test_audit import start

class MarketModePhoneRuntime(unittest.TestCase):
    def test_saved_legacy_modes_migrate_to_auto_source(self):
        for legacy in ("HISTORICAL","LIVE_ONLY","INVALID"):
            _,ui=start({"source":"Dhan","scanner_live":False,
                        "market_display_mode":legacy})
            self.assertEqual(ui["prefs"]["market_display_mode"],"AUTO")
            self.assertIn("LIVE",ui["session_caption"]())
            self.assertIn("HISTORICAL",ui["session_caption"]())
            self.assertFalse(hasattr(ui["market_display_choice"],"on_change"))

    def test_disconnected_live_is_not_faked_and_hist_not_hidden(self):
        _,ui=start({"source":"Dhan","scanner_live":False,
                    "market_display_mode":"LIVE_ONLY"})
        self.assertNotIn("HIDDEN BY LIVE ONLY MODE",
                         ui["scanner_historical_final_vote"]("NIFTY","1m").value)
        self.assertIn("WAIT",ui["canonical_live_final_note"]("NIFTY","1m").value)

    def test_scanner_source_evidence_and_fallback_guards(self):
        s=(ROOT/"src"/"main.py").read_text()
        matches=[n for n in ast.walk(ast.parse(s))
                 if isinstance(n,ast.AsyncFunctionDef) and n.name=="scan_market"]
        self.assertEqual(len(matches),1)
        body=ast.get_source_segment(s,matches[0])
        for required in ('historical_mode_selected=False','display_mode=resolve_mode(',
                         'if display_mode!="LIVE":','if history_valid and display_mode=="HIST":',
                         'hist.get("live_verified") is True',
                         'hist.get("freshness")=="exchange_verified"',
                         'and dhan_feed.connected',
                         '0<=candle_age_seconds<=timeframe_spec(interval)["fresh_seconds"]'):
            self.assertIn(required,body)

if __name__=="__main__":
    unittest.main()
