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
        self.assertIn("content.append(v3_live_building_panel())",body)
        self.assertNotIn("content.append(data_overview())",body)
        self.assertNotIn('content.append(section("ERROR HISTORY"',body)
        self.assertNotIn('section("09  DIAGNOSTICS"',body)
        self.assertNotIn('return section("SYSTEM HEALTH"',SOURCE)
        panel=SOURCE.split('return section("PLATINUM SMART DOCTOR",ft.Column([',1)[1] if SOURCE.count('return section("PLATINUM SMART DOCTOR",ft.Column([')==1 else SOURCE.split("    def v3_live_building_panel():",1)[1].split("    def settings():",1)[0]
        self.assertIn("controls=[data_overview()]",panel)
        self.assertIn("error_history_text()",panel)
        self.assertIn("super_five_recovery.report(time.monotonic())",panel)
        self.assertIn("filter_five_diagnostic_panel()",panel)
        self.assertIn("master_diagnostic_panel()",panel)
        self.assertIn("ERROR DOCTOR • rule-based local diagnosis",SOURCE)

    def test_health_merge_retains_diagnostics_and_retry(self):
        health=SOURCE.split("    def data_overview():",1)[1].split("    def news_event_overview():",1)[0]
        for marker in ("current_filter_coverage()", "diagnose(problem)", "display_failures",
                       "feature_rows", "market_store.status", "retry_selected_data"):
            self.assertIn(marker,health)
        self.assertIn("def error_history_text():",SOURCE)

if __name__=="__main__":unittest.main()
