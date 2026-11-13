"""Regression checks for Dhan-only active provider selection."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class DhanOnlyProviderSelectionTests(unittest.TestCase):
    def test_saved_legacy_provider_migrates_to_dhan(self):
        self.assertIn('if prefs.get("source") != "Dhan":prefs["source"]="Dhan"', SOURCE)

    def test_both_provider_dropdowns_offer_only_dhan(self):
        self.assertEqual(SOURCE.count('options=[ft.dropdown.Option("Dhan")])'), 2)
        self.assertNotIn('options=[ft.dropdown.Option("Yahoo Finance"),ft.dropdown.Option("Broker API"),ft.dropdown.Option("Dhan")])', SOURCE)

    def test_provider_change_cannot_select_legacy(self):
        block = SOURCE.split('    def source_change(e):', 1)[1].split('    source.on_change=source_change', 1)[0]
        self.assertIn('source.value="Dhan"', block)
        self.assertIn('prefs["source"]="Dhan"', block)

    def test_secondary_selector_forces_dhan(self):
        block = SOURCE.split('    def data_source_panel(page_id=None):', 1)[1].split('        chooser.on_change=changed', 1)[0]
        self.assertIn('source.value="Dhan"', block)

if __name__ == "__main__":
    unittest.main()
