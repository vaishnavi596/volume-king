"""Prevent accidental Yahoo selection when an older app has no source preference."""
import unittest
from pathlib import Path


class DefaultProviderContractTests(unittest.TestCase):
    def test_main_uses_dhan_for_missing_source(self):
        source=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        self.assertIn('selected=prefs.get("source","Dhan")',source)
        self.assertIn('source.value=prefs.get("source","Dhan");save()',source)
        self.assertNotIn('selected=prefs.get("source","Yahoo Finance")',source)
        self.assertNotIn('source.value=prefs.get("source","Yahoo Finance")',source)


if __name__ == "__main__":
    unittest.main()
