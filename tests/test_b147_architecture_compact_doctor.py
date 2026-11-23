"""B147 full selected filter inventory, compact errors and SENSEX source-preserving probe."""
import ast
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_compact_doctor import compact_doctor
from scanner_engine import ALL_FILTERS

class B147ArchitectureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.main=(ROOT/"src"/"main.py").read_text(encoding="utf-8")
        ast.parse(cls.main,filename=str(ROOT/"src"/"main.py"))

    def test_all_saved_filters_including_seventeen_survive(self):
        self.assertGreaterEqual(len(ALL_FILTERS),17)
        self.assertIn("MAX_ACTIVE_FILTERS=len(filter_names)",self.main)
        self.assertIn('filter_selected=list(dict.fromkeys(x for x in saved_filters',self.main)
        self.assertIn('active_analysis_filter_names":[str(name) for name in filter_selected]',self.main)
        self.assertNotIn("MAX_ACTIVE_FILTERS=15",self.main)

    def test_compact_doctor_hides_healthy_and_issues_every_unavailable_filter(self):
        chosen=ALL_FILTERS[:17]
        rows=[{"name":name,"vote":None} for name in chosen]
        doc=compact_doctor([{"symbol":"SENSEX","state":"ERROR","error_codes":["DATA_INCOMPLETE"]},
                            {"symbol":"NIFTY","state":"CACHE_PRESENT_UNVERIFIED","error_codes":[]}],
                           chosen,rows,scanner_symbol="SENSEX",scanner_timeframe="1m",
                           provider_connected=True,quote_status="UNAVAILABLE")
        self.assertEqual(doc["selected_filter_count"],17)
        self.assertEqual(len(doc["filter_results"]),17)
        self.assertEqual(doc["healthy_filter_count_hidden"],0)
        self.assertEqual(doc["healthy_stock_count_hidden"],1)
        self.assertTrue(any(x.get("symbol")=="SENSEX" for x in doc["issues"]))
        self.assertFalse(any(x.get("symbol")=="NIFTY" for x in doc["issues"]))
        self.assertTrue(all(x["directional_live_verified"] is False for x in doc["filter_results"]))

    def test_one_minute_default_is_separate_from_watchlist(self):
        self.assertIn('prefs.get("scanner_timeframe","1m")',self.main)
        self.assertIn('prefs.get("chart_timeframe","1m")',self.main)
        self.assertIn('value=str(prefs.get("scanner_refresh","60"))',self.main)
        self.assertIn('def watch_three_minute_signal(sym):',self.main)
        self.assertIn('["1m","3m","5m","10m","15m","30m"]',self.main)

    def test_filter_and_five_box_diagnostic_replaces_old_sensex_probe(self):
        self.assertNotIn("def sensex_full_diagnostic_panel():",self.main)
        p=self.main.split("    def filter_five_diagnostic_panel():",1)[1].split(
            "    # Keep the manual Diagnostics gate",1)[0]
        self.assertIn('names=list(filter_selected)',p)
        self.assertIn('"five_boxes":engines',p)
        self.assertIn('"provider_requests":0',p)
        self.assertIn("FILTER + FIVE BOX DIAG (read-only)",p)
        self.assertNotIn('dhan_feed.quote,"SENSEX"',p)
        self.assertNotIn("market_orders(",p)

if __name__=="__main__": unittest.main()
