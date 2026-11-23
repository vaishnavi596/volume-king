"""Dashboard valid HIST agreement last-good fallback must survive repaint, not mislabel LIVE."""
import unittest,sys,pathlib,ast
ROOT=pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"src"))
from v3_dashboard_last_good import LastGoodHistoricalAgreement
from v3_dashboard_bar_monitor import DashboardBarMonitor

class HistoricalFallbackTests(unittest.TestCase):
    def test_preserve_on_transient_missing_then_recover(self):
        c=LastGoodHistoricalAgreement()
        k=dict(symbol="NIFTY",timeframe="1m",generation=1,source="Dhan",
               filter_signature=("EMA 9/21","RSI 14"))
        self.assertEqual(c.resolve(**k,calculated=(60,40,5),
                     source_candle_time=1795427940),((60,40,5),False))
        self.assertEqual(c.resolve(**k),((60,40,5),True))
        self.assertEqual(c.resolve(**k,calculated=(40,60,5),
                     source_candle_time=1795428000),((40,60,5),False))
        self.assertEqual(c.resolve(**k),((40,60,5),True))
    def test_never_reuse_other_symbol_timeframe_generation_or_filters(self):
        c=LastGoodHistoricalAgreement()
        k=dict(symbol="NIFTY",timeframe="1m",generation=1,source="Dhan",
               filter_signature=("EMA 9/21",))
        c.resolve(**k,calculated=(70,30,3),source_candle_time=1795427940)
        for changed in (dict(symbol="SENSEX"),dict(timeframe="3m"),
                        dict(generation=2),dict(filter_signature=("MACD",)),
                        dict(source="Yahoo")):
            a=dict(k);a.update(changed)
            self.assertEqual(c.resolve(**a),(None,False))
    def test_bad_or_old_data_cannot_replace_valid_agreement(self):
        c=LastGoodHistoricalAgreement()
        k=dict(symbol="BANKNIFTY",timeframe="1m",generation=1,
               source="Dhan",filter_signature=("MACD",))
        c.resolve(**k,calculated=(80,20,4),source_candle_time=200)
        self.assertEqual(c.resolve(**k,calculated=(30,70,5),
                                     source_candle_time=100),((80,20,4),False))
        for bad in ((50,60,4),(50,50,0),(50,50,"4")):
            with self.assertRaises(ValueError):
                c.resolve(**k,calculated=bad,source_candle_time=300)
    def test_monitor_reports_degraded_fallback_not_healthy(self):
        d=DashboardBarMonitor()
        d.observe(surface="INDEX_CARDS",symbol="NIFTY",timeframe="1m",
                  generation=1,history_present=True,history_count=375,
                  bar_constructed=True,used_last_good=True)
        self.assertEqual(d.report(generation=1)["issues"][0]["code"],
                         "LAST_GOOD_HIST_USED_CURRENT_CALCULATION_UNAVAILABLE")
    def test_both_dashboard_surfaces_wired_to_same_cache(self):
        s=(ROOT/"src/main.py").read_text();ast.parse(s)
        self.assertIn("dashboard_last_good=LastGoodHistoricalAgreement()",s)
        self.assertIn("dashboard_hist_agreement(sym,candle_data)",s)
        self.assertIn("dashboard_hist_agreement(index_name,index_history)",s)
        self.assertIn('("Dhan" if prefs.get("source")=="Dhan" else None)',s)

if __name__=="__main__":unittest.main()
