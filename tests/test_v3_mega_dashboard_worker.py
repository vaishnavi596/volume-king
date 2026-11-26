import unittest
import asyncio
from v3_dashboard_last_good import LastGoodHistoricalAgreement
from v3_dashboard_bar_monitor import DashboardBarMonitor
from v3_local_analysis_pool import LocalAnalysisPool
from active_symbol_budget import plan_active_symbols, plan_due_history_symbols

class MegaDashboardWorkerTests(unittest.TestCase):
    def test_invalid_history_cannot_poison_last_good(self):
        with self.assertRaises(ValueError):LastGoodHistoricalAgreement(0)
        c=LastGoodHistoricalAgreement()
        k=dict(symbol="NIFTY",timeframe="1m",generation=1,source="Dhan",filter_signature=("MACD",))
        for bad in (float("nan"),float("inf")):
            with self.assertRaises(ValueError):c.resolve(**k,calculated=(60,40,4),source_candle_time=bad)
        self.assertEqual(c.resolve(**k),(None,False))
        self.assertEqual(c.resolve(**dict(k,generation=-1)),(None,False))

    def test_dashboard_hidden_count_exact_scope(self):
        with self.assertRaises(ValueError):DashboardBarMonitor(0)
        d=DashboardBarMonitor()
        for gen,sym,shown in ((1,"NIFTY",True),(2,"NIFTY",True),(2,"TCS",True),(2,"SENSEX",False)):
            d.observe(surface="INDEX_CARDS",symbol=sym,timeframe="1m",generation=gen,history_present=shown,bar_constructed=shown,history_count=30 if shown else 0)
        self.assertEqual(d.report(generation=2)["healthy_hidden"],1)

    def test_worker_limits_and_submit_failure(self):
        for bad in (0,9,True,2.5):
            with self.assertRaises(ValueError):LocalAnalysisPool(bad)
        p=LocalAnalysisPool(1)
        p.close()
        with self.assertRaises(RuntimeError):asyncio.run(p.run(lambda:1))
        self.assertEqual(p.diagnostics()["submission_failed"],1)
        self.assertEqual(p.diagnostics()["pending"],0)

    def test_index_roster_and_clock(self):
        groups=[[],[],[],[],[]]
        with self.assertRaises(ValueError):plan_active_symbols(groups,keep_indices=("TCS",))
        active=plan_active_symbols(groups)
        with self.assertRaises(ValueError):plan_due_history_symbols(active,now=100,last_global_attempt=-1)
