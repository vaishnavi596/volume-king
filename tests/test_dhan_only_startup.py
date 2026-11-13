"""Production broker UI must only offer Dhan; legacy fixtures remain isolated."""
from pathlib import Path
import unittest
S=(Path(__file__).resolve().parents[1]/"src/main.py").read_text(encoding="utf-8")
class StartupProviderTests(unittest.TestCase):
    def test_production_broker_selector_is_dhan_only(self):
        self.assertIn('broker_names=["Dhan"]',S)
        self.assertIn('options=[ft.dropdown.Option("Dhan")]',S)
    def test_legacy_saved_source_remains_available_for_regression_fixtures(self):
        self.assertIn('if prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan"):',S)
if __name__=="__main__":unittest.main()
