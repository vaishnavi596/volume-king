"""SENSEX B143 explicitly opt-in read-only diagnostic source guards."""
import ast
from pathlib import Path
import unittest

MAIN=Path(__file__).resolve().parents[1]/"src"/"main.py"
GATEWAY=Path(__file__).resolve().parents[1]/"backend"/"clone_v2_gateway.py"

class SensexFullDiagnosticB143(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=MAIN.read_text()
        cls.server=GATEWAY.read_text()
        ast.parse(cls.app,filename=str(MAIN))

    def test_new_index_mapping_and_old_probe_removed(self):
        self.assertIn('"SENSEX": ("IDX_I", 51)',self.server)
        self.assertNotIn('def sensex_full_diagnostic_panel():',self.app)
        self.assertNotIn('content.append(sensex_full_diagnostic_panel())',self.app)

    def test_new_filter_diagnostic_is_opt_in_and_cache_only(self):
        p=self.app.split("    def filter_five_diagnostic_panel():",1)[1].split(
            "    # Keep the manual Diagnostics gate",1)[0]
        self.assertIn("on_click=inspect",p)
        self.assertIn('"provider_requests":0',p)
        self.assertIn('"orders_sent":0',p)
        self.assertNotIn("asyncio.to_thread(",p)
        self.assertNotIn("dhan_feed.quote(",p)
        self.assertIn('read_five_engine_context(symbol,tf)',p)

    def test_five_box_percentages_fail_closed(self):
        p=self.app.split("    def filter_five_diagnostic_panel():",1)[1].split(
            "    # Keep the manual Diagnostics gate",1)[0]
        self.assertIn('"bullish_percent":bull if ready else None',p)
        self.assertIn('"bearish_percent":bear if ready else None',p)
        self.assertIn('"HIST_ONLY"',p)
        self.assertIn('"errors_only":errors',p)
        self.assertIn('filter_five_diagnostic_panel(),',self.app)

if __name__=="__main__":
    unittest.main()
