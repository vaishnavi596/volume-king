"""Regression checks for the visible Dhan-only provider selectors.

Legacy provider behavior remains available to internal regression fixtures until
the underlying data paths are fully isolated and migrated.
"""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class DhanOnlyProviderSelectionTests(unittest.TestCase):
    def test_dhan_is_default(self):
        self.assertIn('"source":"Dhan"', SOURCE)

    def test_both_provider_dropdowns_offer_only_dhan(self):
        self.assertEqual(SOURCE.count('options=[ft.dropdown.Option("Dhan")])'), 2)
        self.assertNotIn('options=[ft.dropdown.Option("Yahoo Finance"),ft.dropdown.Option("Broker API"),ft.dropdown.Option("Dhan")])', SOURCE)

    def test_saved_unknown_provider_defaults_to_dhan(self):
        self.assertIn('if prefs.get("source") not in ("Yahoo Finance","Broker API","Dhan"):prefs["source"]="Dhan"', SOURCE)

    def test_legacy_provider_callbacks_remain_for_regression_compatibility(self):
        block = SOURCE.split('    def source_change(e):', 1)[1].split('    source.on_change=source_change', 1)[0]
        self.assertIn('prefs["source"]=source.value', block)

if __name__ == "__main__":
    unittest.main()
