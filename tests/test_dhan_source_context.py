"""Missing source preference must resolve consistently to Dhan across UI and health."""
import pathlib
import unittest

SOURCE = pathlib.Path(__file__).resolve().parents[1] / "src" / "main.py"


class DhanSourceContextTests(unittest.TestCase):
    def test_no_auto_default_in_market_chart_and_health_paths(self):
        source = SOURCE.read_text(encoding="utf-8")
        self.assertNotIn('prefs.get("source","Auto")', source)
        self.assertIn('prefs.get("source","Dhan")!=selected', source)
        self.assertIn('market_store.get("market",prefs.get("source","Dhan")', source)
        self.assertIn('key="market:"+prefs.get("source","Dhan")', source)
        self.assertNotIn('.get(prefs.get("source"),"Yahoo Finance")', source)
        self.assertIn('"Yahoo Finance":"Yahoo Finance"}.get(prefs.get("source"),"Dhan")', source)
        self.assertIn('source.value=prefs.get("source","Dhan");save()', source)
        self.assertIn('prefs.get(\'source\',\'Dhan\')', source)


if __name__ == "__main__":
    unittest.main()
