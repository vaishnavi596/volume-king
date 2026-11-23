"""Dashboard three-index 1m historical-vote contract (source-only).

The index poll has changed from 5m to real 1m historical candles. A 5m
Super Five vote must never masquerade as Dashboard 1m evidence.
"""
import ast
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


class DashboardIndexVoteFallbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)
        cls.functions = {
            node.name: ast.get_source_segment(cls.source, node)
            for node in ast.walk(cls.tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        }

    def test_three_index_cards_share_real_one_minute_renderer(self):
        source = self.functions["dashboard_market_indices"]
        self.assertIn('("NIFTY", "BANKNIFTY", "SENSEX")', source)
        self.assertIn('shared_history(index_name,"1m")', source)
        self.assertIn('dashboard_hist_agreement(index_name,index_history)', source)
        helper=self.functions["dashboard_hist_agreement"]
        self.assertIn('historical_vote_agreement(history,"1m")', helper)
        self.assertIn('historical_vote_bar(index_agreement,"1m")', source)

    def test_incomplete_one_minute_does_not_borrow_five_minute_ranking(self):
        source = self.functions["dashboard_market_indices"]
        self.assertIn('if index_agreement is None:', source)
        self.assertIn('index_signal_row=historical_vote_bar(None,"1m")', source)
        self.assertNotIn('watch_signal_cache.get(index_name)', source)
        self.assertNotIn('vote_display(counts,False)', source)

    def test_three_slot_dashboard_does_not_label_five_minute_as_one(self):
        source = self.functions["dashboard_index_analysis"]
        self.assertIn('shared_history(sym,"1m")', source)
        self.assertIn('dashboard_hist_agreement(sym,candle_data)', source)
        self.assertIn('historical_vote_bar(agreement,"1m")', source)
        self.assertNotIn('display_analysis(sym,candle_data)', source)

    def test_completed_bar_calculation_is_timeframe_specific(self):
        source = self.functions["historical_vote_agreement"]
        self.assertIn('seconds=timeframe_spec(tf)["seconds"]', source)
        self.assertIn('bar[0]+seconds<=now', source)
        self.assertIn('quality_check(completed,seconds', source)
        self.assertIn('analyze(quality["bars"],selected,tf)', source)
        self.assertIn('data.get("_scanner_timeframe","5m")!=tf', source)

    def test_index_candle_poller_reuses_existing_cadence(self):
        source = self.functions["dhan_index_candle_poll"]
        self.assertIn('get_market_data,index_sym,"1m","2d"', source)
        self.assertIn('chart_snapshots[(index_sym,"1m",generation)]', source)
        self.assertIn('shared_history(index_sym,"1m")', source)
        self.assertNotIn('get_market_data,index_sym,"5m","2d"', source)
        self.assertIn('remember_candle_failure(index_sym,"1m","index candle fetch",exc)', source)
        self.assertNotIn('remember_candle_failure(index_sym,"5m","index candle fetch",exc)', source)

    def test_five_engine_dashboard_uses_matching_index_one_minute_not_legacy_five(self):
        summary=self.functions["five_engine_summary"]
        chips=self.functions["five_engine_chips"]
        for body in (summary,chips):
            self.assertIn('("NIFTY","BANKNIFTY","SENSEX")',body)
            self.assertIn('else "5m"',body)
            self.assertIn("completed_timeframe_candle_balance",body)
        self.assertIn('if not historical and display_timeframe=="1m":',chips)
        self.assertIn('historical_vote_agreement(shared_history(sym,"1m"),"1m")',chips)
        self.assertIn('if not historical and display_timeframe=="3m":',chips)
        self.assertIn('three=watch_three_minute_signal(sym)',chips)
        self.assertIn('historical=True',chips)
        self.assertIn('NOT live',chips)
        self.assertNotIn('dhan_feed.intraday(',chips)

    def test_doctor_reports_selected_versus_external_wait_filters(self):
        body=self.functions["filter_coverage_panel"]
        self.assertIn('len(filter_selected)',body)
        self.assertIn('"OI Support","OI Resistance","OI Profile"',body)
        self.assertIn('"Dhan Max Pain","News Headlines"',body)
        self.assertIn('external evidence WAIT ',body)
        self.assertIn("indexes 1m / equities 5m",body)

    def test_one_minute_index_histories_never_presented_live(self):
        source = self.functions["historical_vote_bar"]
        self.assertIn('vote_display(agreement,False,timeframe=tf)', source)


if __name__ == "__main__":
    unittest.main()
