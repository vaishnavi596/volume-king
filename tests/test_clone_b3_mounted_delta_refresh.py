"""App-only B3 incremental refresh wiring regression; no device/network."""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


class MountedDeltaRefreshSourceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_data_refresh_checks_mounted_sections_before_select(self):
        source = self.source
        start = source.index("    async def flush_view_refresh():")
        stop = source.index("    def request_view_refresh(i):", start)
        flush = source[start:stop]
        self.assertIn("refresh_mounted_data_sections(target)", flush)
        self.assertLess(flush.index("refresh_mounted_data_sections(target)"),
                        flush.index("select(target,refresh_only=True)"))
        self.assertIn("if target==4", flush)

    def test_mounted_delta_path_does_not_replace_page_tree(self):
        source = self.source
        start = source.index("    def refresh_mounted_data_sections(target):")
        stop = source.index("    refresh_pending=[False]", start)
        section = source[start:stop]
        self.assertIn("host.content=factory()", section)
        self.assertIn("host.update()", section)
        self.assertNotIn("body.controls", section)
        self.assertNotIn("render_page(", section)
        self.assertNotIn("select(", section)
        self.assertNotIn("page.update()", section)

    def test_scanner_controls_and_chart_are_persistent(self):
        source = self.source
        start = source.index("    def scanner_content():")
        stop = source.index("    def run_scan(e):", start)
        scanner = source[start:stop]
        self.assertIn("scanner_controls(),scan_result", scanner)
        self.assertIn("scanner_compact_chart", scanner)
        self.assertIn('wrap_delta_section("scanner_five"', scanner)
        self.assertIn('wrap_delta_section("scanner_options"', scanner)
        self.assertIn('wrap_delta_section("scanner_assessment"', scanner)

    def test_dashboard_sections_mounted_and_no_new_provider_request(self):
        source = self.source
        start = source.index("    def dashboard():")
        stop = source.index("    search=ft.TextField(", start)
        dashboard = source[start:stop]
        self.assertIn('wrap_delta_section("dashboard_indices"', dashboard)
        self.assertIn('wrap_delta_section("dashboard_analysis"', dashboard)
        self.assertIn('wrap_delta_section("dashboard_super_five"', dashboard)
        self.assertIn('wrap_delta_section("dashboard_risk"', dashboard)
        start = source.index("    def refresh_mounted_data_sections(target):")
        stop = source.index("    refresh_pending=[False]", start)
        path = source[start:stop]
        self.assertNotIn("dhan_feed.", path)
        self.assertNotIn("get_market_data(", path)


if __name__ == "__main__":
    unittest.main()
