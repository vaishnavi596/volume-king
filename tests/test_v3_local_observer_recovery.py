import unittest
from v3_local_observer_recovery import LocalObserverRecovery


class LocalObserverRecoveryTests(unittest.TestCase):
    def test_cooldown_and_measured_local_retest(self):
        r=LocalObserverRecovery()
        self.assertTrue(r.ready(1,100))
        try:
            raise ValueError("SECRET never log")
        except ValueError as exc:
            r.failed(1,100,exc,"local_worker")
        self.assertFalse(r.ready(1,114))
        self.assertTrue(r.ready(1,115))
        r.succeeded(1,115,0)
        self.assertTrue(r.report(115)["pending"])
        r.succeeded(1,116,3)
        report=r.report(116)
        self.assertFalse(report["pending"])
        self.assertEqual(report["events"][-1]["state"],"LOCAL_RETEST_PASS")
        self.assertNotIn("SECRET",str(report))
        self.assertEqual(report["provider_requests"],0)
        self.assertEqual(report["orders_sent"],0)

    def test_escalation_and_generation_change(self):
        r=LocalObserverRecovery()
        for now in (100,115,145):
            r.failed(1,now,RuntimeError("hidden"),"capture")
        self.assertEqual(r.report(145)["events"][-1]["state"],"ESCALATED_COOLDOWN")
        self.assertFalse(r.ready(1,444))
        self.assertTrue(r.ready(2,146))
        self.assertEqual(r.report(146)["events"][-1]["state"],"ABANDONED_GENERATION_CHANGED")
        self.assertFalse(r.report(146)["pending"])

    def test_bounded_and_read_only_report(self):
        r=LocalObserverRecovery()
        for i in range(50):
            r.failed(1,100+i,RuntimeError(),"capture")
        a=r.report(150)
        self.assertEqual(a["retained_events"],40)
        self.assertEqual(a["events_total"],50)
        self.assertEqual(a,r.report(150))

    def test_both_doctors_read_repair_log_and_observer_uses_it(self):
        from pathlib import Path
        s=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        body=s.split("async def super_five_minute_refresh():",1)[1].split("def historical_five_minute_technical",1)[0]
        self.assertIn("super_five_recovery.ready",body)
        self.assertIn("super_five_recovery.failed",body)
        self.assertIn("super_five_recovery.succeeded",body)
        self.assertIn("generation==provider_generation[0]",body)
        self.assertEqual(s.count("super_five_recovery.report(time.monotonic())"),2)
