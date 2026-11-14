"""Batch 4: health and doctor are one Settings-only diagnostic surface."""
import pathlib
import unittest

SOURCE=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")

class HealthPlacementTest(unittest.TestCase):
    def test_dashboard_has_no_health_panel(self):
        body=SOURCE.split("    def dashboard():",1)[1].split("    search=ft.TextField(",1)[0]
        self.assertNotIn("data_overview(),",body)
        self.assertIn("dashboard_market_indices(),",body)

    def test_settings_has_one_diagnostic_location(self):
        body=SOURCE.split("    def settings():",1)[1].split("    # Scanner-only upgrade.",1)[0]
        self.assertIn("content.append(data_overview())",body)
        self.assertIn('content.append(section("RECENT ERROR TYPES"',body)
        self.assertNotIn('section("09  DIAGNOSTICS"',body)
        self.assertEqual(SOURCE.count('return section("SYSTEM HEALTH"'),1)
        self.assertIn("ERROR DOCTOR • rule-based local diagnosis",SOURCE)

if __name__=="__main__":unittest.main()
