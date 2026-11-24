"""Unexpected closure and stale-feed display mode, pure offline contract."""
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_market_display_mode import MODES,normalized_mode,resolve_mode

class MarketDisplayModeTests(unittest.TestCase):
    def test_mode_validation_and_default(self):
        self.assertEqual(MODES,("AUTO","HISTORICAL","LIVE_ONLY"))
        self.assertEqual(normalized_mode(None),"AUTO")
        self.assertEqual(normalized_mode("bad"),"AUTO")

    def test_auto_falls_back_on_unplanned_weekday_stale_feed(self):
        self.assertEqual(resolve_mode("AUTO",session_eligible=True,
                                      live_verified=False,history_valid=True),"HIST")
        self.assertEqual(resolve_mode("AUTO",session_eligible=False,
                                      live_verified=True,history_valid=True),"HIST")

    def test_auto_recovers_only_with_fresh_verified_live_and_valid_session(self):
        self.assertEqual(resolve_mode("AUTO",session_eligible=True,
                                      live_verified=True,history_valid=True),"LIVE")
        self.assertEqual(resolve_mode("AUTO",session_eligible=True,
                                      live_verified=False,history_valid=False),"WAIT")

    def test_manual_modes_fail_closed(self):
        self.assertEqual(resolve_mode("HISTORICAL",session_eligible=True,
                                      live_verified=True,history_valid=True),"HIST")
        self.assertEqual(resolve_mode("HISTORICAL",session_eligible=True,
                                      live_verified=True,history_valid=False),"WAIT")
        self.assertEqual(resolve_mode("LIVE_ONLY",session_eligible=False,
                                      live_verified=True,history_valid=True),"WAIT")
        self.assertEqual(resolve_mode("LIVE_ONLY",session_eligible=True,
                                      live_verified=True,history_valid=True),"LIVE")

    def test_phone_settings_and_final_presenters_retain_safety_labels(self):
        text=(ROOT/"src"/"main.py").read_text()
        self.assertIn('prefs["market_display_mode"]=normalized_mode',text)
        self.assertIn('market_display_choice=ft.Dropdown(',text)
        self.assertIn('new_mode=normalized_mode(e.control.value)',text)
        self.assertIn('HIST FINAL • HIDDEN BY LIVE ONLY MODE',text)
        self.assertIn('LIVE FINAL • DISABLED BY HISTORICAL MODE',text)
        self.assertIn('and prefs.get("market_display_mode")!="LIVE_ONLY"',text)
        self.assertIn('if prefs.get("market_display_mode")!="HISTORICAL"',text)

if __name__=="__main__":
    unittest.main()
