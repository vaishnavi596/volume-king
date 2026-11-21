"""B1 isolated queue burst behavior; no broker, server or Flutter calls."""
import unittest
from clone_day2_apply_queue import SmartApplyQueue, Update

class B1CapacityTests(unittest.TestCase):
    def mk(self, count):
        for n in range(count):
            for kind in ("quote", "candle_1m", "candle_3m", "candle_5m",
                         "filter_oi_support", "filter_oi_resistance",
                         "filter_max_pain", "filter_pcr", "filter_candle_trend", "assessment"):
                timeframe = kind.split("_", 1)[1] if kind.startswith("candle_") else ""
                yield Update("watchlist", "SYM_%03d" % n,
                             "candle" if timeframe else kind, 1, n,
                             timeframe=timeframe, completed=bool(timeframe))
    def test_all_counts_no_rejections(self):
        for n in (10, 35, 54, 73):
            with self.subTest(n=n):
                queue = SmartApplyQueue(max_pending=512)
                got=[]
                report=queue.ingest_burst(self.mk(n), apply=got.append, batch_size=128)
                self.assertEqual(len(got),n*10)
                self.assertEqual(len(report.applied),n*10)
                self.assertEqual(queue.health()["counts"]["capacity_rejected"],0)
                self.assertEqual(queue.health()["pending"],0)
                self.assertEqual(queue.health()["state"],"OK")
    def test_small_cap_and_timeframe_isolation(self):
        queue = SmartApplyQueue(max_pending=2)
        applied=[]
        update=[Update("watchlist","A","candle",1,j,timeframe=f,completed=True) for j,f in enumerate(("1m","3m","5m"))]
        queue.ingest_burst(update,apply=applied.append,batch_size=1)
        self.assertEqual([u.timeframe for u in applied],["1m","3m","5m"])
    def test_fail_closed_and_retry_retains_pending(self):
        queue=SmartApplyQueue(max_pending=1)
        updates=[Update("watchlist","A","quote",1,1),Update("watchlist","B","quote",1,2)]
        def bad(_): raise RuntimeError("failed renderer")
        with self.assertRaises(RuntimeError):
            queue.ingest_burst(updates,apply=bad,batch_size=1)
        self.assertEqual(queue.health()["pending"],1)
        self.assertEqual(queue.health()["counts"]["capacity_rejected"],0)
        self.assertEqual(queue.apply_tick(1).queue_length,0)
    def test_noncompleted_and_invalid_timeframe(self):
        queue=SmartApplyQueue(max_pending=2)
        with self.assertRaises(ValueError):
            queue.ingest_burst([Update("watchlist","A","candle",1,1)])
        self.assertEqual(queue.health()["pending"],0)

if __name__=="__main__":
    unittest.main()
