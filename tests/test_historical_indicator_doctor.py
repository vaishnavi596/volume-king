"""Cache-only Doctor observation of actual historical indicator execution."""
import unittest
from v3_smart_active_doctor import active_report

class HistoricalIndicatorDoctorTests(unittest.TestCase):
    def report(self, observed):
        return active_report(generation=1,symbols=[],quote_present=[],index_present=[],
            connected={},signal_present=[],attempts={},now_monotonic=1,market_open=False,
            errors=[],progress={},performance={},quote_attempt_age=None,
            historical_indicator_observation=observed)

    def row(self, observed):
        return next((r for r in self.report(observed)["active"]
                     if r["check"]=="HISTORICAL_INDICATOR_RUNTIME"),None)

    def test_unobserved_and_wrong_generation(self):
        for observed in ({},{"generation":2,"successes":1}):
            self.assertEqual(self.row(observed)["status"],"UNVERIFIED")

    def test_failure_is_actionable(self):
        row=self.row({"generation":1,"successes":1,"last_error":"ValueError"})
        self.assertEqual((row["status"],row["code"]),("ERROR","BK-HIST-001"))
        self.assertEqual(row["evidence"]["last_error"],"ValueError")

    def test_observed_success_hidden(self):
        self.assertIsNone(self.row({"generation":1,"successes":1,"last_error":None}))
        self.assertEqual(self.report({"generation":1,"successes":1})["provider_requests"],0)

    def test_index_worker_error_and_unverified_are_distinct(self):
        args=dict(generation=1,symbols=[],quote_present=[],index_present=[],
            connected={},signal_present=[],attempts={},now_monotonic=1,market_open=False,
            errors=[],progress={},performance={},quote_attempt_age=None)
        def row(value):
            return next((r for r in active_report(**args,historical_prewarm_observation=value)["active"]
                if r["check"]=="HISTORICAL_INDEX_WORKER"),None)
        self.assertEqual(row({"generation":2,"successes":1})["status"],"UNVERIFIED")
        self.assertEqual(row({"generation":1,"last_error":"ValueError"})["code"],"BK-HIST-WORKER-001")
        self.assertIsNone(row({"generation":1,"successes":1}))

    def test_index_worker_runs_before_publication_and_rechecks_generation(self):
        from pathlib import Path
        s=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        worker=s.split("async def prewarm_index_historical_indicator(",1)[1].split("def historical_vote_agreement(",1)[0]
        self.assertIn("await local_analysis_pool.run(compute)",worker)
        self.assertIn("generation!=provider_generation[0]",worker)
        self.assertIn("historical_indicator_cache[identity]=result",worker)
        self.assertNotIn("get_market_data(",worker)
        poll=s.split("async def dhan_index_candle_poll():",1)[1].split("async def watch_three_minute_warmup():",1)[0]
        self.assertLess(poll.index("await prewarm_index_historical_indicator"),poll.index('chart_snapshots[(index_sym,"1m",generation)]=index_history'))
