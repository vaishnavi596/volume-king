import asyncio
import unittest
from v3_local_analysis_pool import LocalAnalysisPool, worker_budget

class LocalPoolTests(unittest.TestCase):
    def test_budget_reserves_capacity(self):
        self.assertEqual(worker_budget(1, 8*1024**3),1)
        self.assertEqual(worker_budget(8, 8*1024**3),7)
        self.assertEqual(worker_budget(16, 256*1024**2),1)
        self.assertEqual(worker_budget(32, 32*1024**3),8)
    def test_results_and_failure_telemetry(self):
        pool=LocalAnalysisPool(2)
        def fail():
            raise ValueError("fixture")
        async def run():
            self.assertEqual(await asyncio.gather(*(pool.run(pow,n,2) for n in range(70))),[n*n for n in range(70)])
            with self.assertRaises(ValueError):
                await pool.run(fail)
        try:
            asyncio.run(run())
            stats=pool.diagnostics()
            self.assertEqual(stats["completed"],71)
            self.assertEqual(stats["failed"],1)
            self.assertEqual(stats["pending"],0)
            self.assertEqual(stats["running"],0)
            self.assertEqual(stats["provider_requests"],0)
        finally:pool.close()
