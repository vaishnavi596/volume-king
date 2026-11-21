"""B178 phone doctor contract: 17 filters, five independent boxes, no SENSEX-only probe."""
import ast
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
APP=(ROOT/"src"/"main.py").read_text(encoding="utf-8")

class FilterFiveDoctorContract(unittest.TestCase):
    def test_main_app_compiles_and_old_sensex_tool_is_removed(self):
        ast.parse(APP)
        self.assertNotIn("def sensex_full_diagnostic_panel():",APP)
        self.assertNotIn("content.append(sensex_full_diagnostic_panel())",APP)
        self.assertNotIn("SENSEX FULL DIAG (read-only)",APP)

    def test_main_doctor_contains_all_filters_and_five_box_diagnosis(self):
        start=APP.index("    def filter_five_diagnostic_panel():")
        end=APP.index("    # Keep the manual Diagnostics gate",start)
        panel=APP[start:end]
        self.assertIn('names=list(filter_selected)',panel)
        self.assertIn('complete_filter_rows(result,names,filter_modes)',panel)
        self.assertIn('enrich_context_filter_rows(symbol,',panel)
        self.assertIn('snapshot_for_display(five_engine_snapshots.get(symbol)',panel)
        for name in ('technical','candle','news','futures','options'):
            self.assertIn('"'+name+'"',panel)
        self.assertIn('"errors_only":errors',panel)
        self.assertIn('"filter_results":filter_rows',panel)
        self.assertIn('"five_boxes":engines',panel)
        self.assertIn('"provider_requests":0',panel)
        self.assertIn('"HIST_ONLY"',panel)
        self.assertIn('"bullish_percent":bull if ready else None',panel)
        self.assertIn('"bearish_percent":bear if ready else None',panel)
        self.assertIn("FILTER + FIVE BOX DIAG (read-only)",panel)

    def test_panel_is_embedded_in_existing_main_error_doctor(self):
        start=APP.index("    def v3_live_building_panel():")
        end=APP.index("    def settings():",start)
        self.assertIn("filter_five_diagnostic_panel(),",APP[start:end])
        self.assertIn("content.append(v3_live_building_panel())",APP)

if __name__=="__main__":
    unittest.main()
