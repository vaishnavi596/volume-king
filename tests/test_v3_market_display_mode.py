"""Evidence-only LIVE/HIST market mode: no calendar or manual override."""
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_market_display_mode import MODES,normalized_mode,resolve_mode

class MarketDisplayModeTests(unittest.TestCase):
    def test_only_two_data_modes_and_legacy_settings_migrate(self):
        self.assertEqual(MODES,("LIVE","HISTORICAL"))
        for old in (None,"bad","AUTO","LIVE_ONLY","HISTORICAL"):
            self.assertEqual(normalized_mode(old),"AUTO")

    def test_live_verified_wins_even_if_calendar_cannot_confirm_open(self):
        for eligible in (True,False,None):
            self.assertEqual(resolve_mode("AUTO",session_eligible=eligible,
                live_verified=True,history_valid=True),"LIVE")

    def test_data_loss_preserves_history_and_never_claims_live(self):
        for old in ("AUTO","LIVE_ONLY","HISTORICAL"):
            self.assertEqual(resolve_mode(old,session_eligible=True,
                live_verified=False,history_valid=True),"HIST")
            self.assertEqual(resolve_mode(old,session_eligible=False,
                live_verified=False,history_valid=False),"WAIT")

    def test_phone_has_no_manual_mode_switch(self):
        s=(ROOT/"src"/"main.py").read_text()
        self.assertIn('prefs["market_display_mode"]=normalized_mode',s)
        self.assertIn('market_display_choice=ft.Text(',s)
        self.assertNotIn('market_display_choice=ft.Dropdown(',s)
        self.assertIn('historical_mode_selected=False',s)
        self.assertIn('display_mode=resolve_mode(',s)

if __name__=="__main__":
    unittest.main()
