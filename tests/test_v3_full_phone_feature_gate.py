"""Single-install full V3 phone Doctor gate: reports real feature states safely."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
MAIN=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
PROBE=(ROOT/"src"/"v3_live_capacity_probe.py").read_text(encoding="utf-8")
DOCTOR=(ROOT/"src"/"v3_stock_diagnostics.py").read_text(encoding="utf-8")

class TestSinglePhoneFeatureAudit(unittest.TestCase):
    def test_full_source_compiles(self):
        for name,text in (("main",MAIN),("probe",PROBE),("doctor",DOCTOR)):
            with self.subTest(file=name):ast.parse(text)
    def test_real_phone_probe_has_one_active_max_70_button(self):
        # One diagnostic pass: actual selected unique equities, capped at 70.
        # Three indices are counted separately, not as equity slots.
        self.assertIn('TEST ACTIVE • MAX 70 EQUITIES (+3 INDICES)',MAIN)
        self.assertIn('async def run_cached_test(e):',MAIN)
        self.assertIn('count=len(chosen)',MAIN)
        self.assertNotIn('ft.OutlinedButton("TEST 54',MAIN)
        self.assertNotIn('ft.OutlinedButton("TEST 70 SHARES',MAIN)
        self.assertIn('local_analysis_pool.run(benchmark_cached_capacity',MAIN)
        self.assertIn('stock_diagnostic_registry.reconcile(',MAIN)
    def test_one_pass_live_feature_inventory(self):
        for key in ('"dhan_connected"','"oracle_gateway_connected"',
            '"equity_quote_status"','"index_quote_present"',
            '"watchlist_count"','"configured_unique_equities"',
            '"scanner_status"','"scanner_progress"','"scanner_fetch_error_count"',
            '"option_status"','"options_cached_context_count"',
            '"chart_provider"','"chart_source_present"','"chart_webview_attached"',
            '"super_five_cached_symbols"','"watchlist_3m_signal_cache_symbols"',
            '"news_fusion_cached_context_count"','"active_analysis_filter_names"',
            '"five_verified_live_filters"','"sixth_filter_slot"',
            '"login_bootstrap_states"','"trade_execution"'):
            with self.subTest(key=key):self.assertIn(key,MAIN)
    def test_no_fake_live_claim_and_preserved_disabled_orders(self):
        self.assertIn('"ui_raster_ms":"UNMEASURED',PROBE)
        self.assertIn('"five_live_options_filters":"NOT MEASURED',PROBE)
        self.assertIn('"live_signal_eligible":False',DOCTOR)
        self.assertIn('"trade_execution":"DISABLED"',MAIN)
    def test_all_six_candle_timeframes_in_real_cached_probe(self):
        self.assertIn('("1m","3m","5m","10m","15m","30m")',PROBE)
        self.assertIn('completed_derived_bars(',PROBE)

if __name__=="__main__":
    unittest.main()
