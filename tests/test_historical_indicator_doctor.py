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
