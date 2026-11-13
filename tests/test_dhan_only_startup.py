"""Production startup must never restore an archived data provider."""
from pathlib import Path
import unittest
S=(Path(__file__).resolve().parents[1]/"src/main.py").read_text(encoding="utf-8")
class StartupProviderTests(unittest.TestCase):
    def test_saved_provider_cannot_override_dhan_startup(self):
        start=S.split('    prefs.update(load_preferences(STATE,page.client_storage))',1)[1]
        before_schema=start.split('    prefs["schema_version"]=2',1)[0]
        self.assertIn('prefs["source"]="Dhan"',before_schema)
        self.assertNotIn('if prefs.get("source") not in',before_schema)
    def test_ui_still_has_dhan_only_source(self):
        self.assertIn('prefs["source"]="Dhan"',S)
if __name__=="__main__":unittest.main()
