"""B201 dashboard Scanner-then-disappear root-cause monitor, offline only."""
import ast
import pathlib
import sys
import unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_dashboard_bar_monitor import DashboardBarMonitor

class DashboardMonitorTests(unittest.TestCase):
    def test_hidden_when_good_but_reports_disappeared(self):
        d=DashboardBarMonitor()
        k=dict(surface="INDEX_CARDS",symbol="NIFTY",timeframe="1m",
               generation=1,history_present=True,history_count=375)
        d.observe(**k,bar_constructed=True)
        self.assertEqual(d.report(generation=1)["issue_count"],0)
        d.observe(**k,bar_constructed=False)
        r=d.report(generation=1)
        self.assertEqual(r["issues"][0]["code"],"HIST_BAR_DISAPPEARED_WITH_CACHE")
        self.assertTrue(r["issues"][0]["previous_bar_was_visible_in_control_tree"])
        self.assertEqual(r["provider_requests"],0)
        d.observe(**k,bar_constructed=True)
        self.assertEqual(d.report(generation=1)["issue_count"],0)

    def test_cached_history_without_vote_is_not_called_healthy(self):
        d=DashboardBarMonitor()
        d.observe(surface="INDEX_CARDS",symbol="BANKNIFTY",timeframe="1m",
                  generation=3,history_present=True,history_count=376,bar_constructed=False)
        self.assertEqual(d.report(generation=3)["issues"][0]["code"],
                         "CACHED_1M_HISTORY_NO_HIST_VOTE_BAR")
        self.assertEqual(d.report(generation=4)["issue_count"],0)

    def test_two_dashboard_presenters_disagree(self):
        d=DashboardBarMonitor()
        for surface,bar in (("INDEX_CARDS",True),("ANALYSIS_SLOTS",False)):
            d.observe(surface=surface,symbol="SENSEX",timeframe="1m",
                      generation=2,history_present=True,history_count=50,
                      bar_constructed=bar)
        names={v["code"] for v in d.report(generation=2)["issues"]}
        self.assertIn("DASHBOARD_SURFACE_AGREEMENT_MISMATCH",names)

    def test_no_false_proof_of_flutter_pixels_or_phone_persistence(self):
        d=DashboardBarMonitor()
        report=d.report(generation=1)
        self.assertIn("NOT Flutter painted pixels",report["source"])
        self.assertIn("CURRENT_APP_PROCESS_ONLY",report["snapshot_scope"])
        self.assertEqual(report["orders_sent"],0)

    def test_phone_diagnostic_wire_paths(self):
        s=(ROOT/"src/main.py").read_text()
        ast.parse(s)
        self.assertIn("dashboard_bar_monitor=DashboardBarMonitor()",s)
        self.assertIn('surface="INDEX_CARDS"',s)
        self.assertIn('surface="ANALYSIS_SLOTS"',s)
        self.assertIn('"dashboard_bar_errors_only":dashboard_bar_errors',s)
        self.assertNotIn("dashboard_bar_monitor.fetch(",s)

if __name__=="__main__":unittest.main()
