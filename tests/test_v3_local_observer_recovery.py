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
        master=s.split('"test":"V3_MASTER_ALL_SEGMENTS_DOCTOR"',1)[1].split("report.value=json.dumps(report_data",1)[0]
        active=s.split("def inspect_active(_):",1)[1].split("return ft.Column([",1)[0]
        board=s.split("def repair_board():",1)[1].split("def update_repair_board():",1)[0]
        self.assertIn('"local_auto_recovery":super_five_recovery.report(time.monotonic())',master)
        self.assertIn('data["local_auto_recovery"]=super_five_recovery.report(time.monotonic())',active)
        self.assertIn("payload=super_five_recovery.report(time.monotonic())",board)

    def test_persistent_audit_does_not_restore_recovery_authority(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            path=Path(directory)/"repair.json"
            r=LocalObserverRecovery(path)
            r.failed(1,100,ValueError("secret"),"local_worker")
            sequence,doc=r.audit_snapshot()
            r.audit_written(sequence,r.write_audit(doc))
            self.assertIsNone(r.audit_snapshot())
            reopened=LocalObserverRecovery(path)
            reopened.load_audit()
            report=reopened.report(101)
            self.assertEqual(len(report["previous_events"]),1)
            self.assertEqual(report["previous_events"][0]["state"],"RETRY_SCHEDULED")
            self.assertFalse(report["pending"])
            self.assertTrue(reopened.ready(1,101))
            self.assertNotIn("secret",path.read_text())

    def test_corrupt_audit_is_reported_without_recovery_or_data_deletion(self):
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as directory:
            path=Path(directory)/"repair.json"
            path.write_text("not json")
            r=LocalObserverRecovery(path)
            r.load_audit()
            self.assertEqual(r.report(100)["persistence_error"],"JSONDecodeError")
            self.assertFalse(r.report(100)["pending"])
            self.assertEqual(path.read_text(),"not json")

    def test_board_reports_actual_stages_not_global_health(self):
        r=LocalObserverRecovery()
        self.assertIsNone(r.board(1,100)["progress"])
        r.failed(1,100,ValueError(),"capture")
        self.assertEqual(r.board(1,100)["progress"],25)
        r.advance(1,115,"REPAIRING")
        self.assertEqual(r.board(1,115)["progress"],50)
        r.advance(1,116,"RETESTING")
        self.assertEqual(r.board(1,116)["progress"],75)
        r.succeeded(1,117,2)
        self.assertEqual(r.board(1,117)["progress"],100)
        self.assertEqual(r.board(1,117)["repaired"],1)
        self.assertEqual(r.board(2,117)["status"],"UNOBSERVED")

    def test_board_is_first_dashboard_section_and_cache_only(self):
        from pathlib import Path
        s=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()
        body=s.split("    def dashboard():",1)[1].split("    search=",1)[0]
        self.assertLess(body.index('wrap_delta_section("dashboard_repair"'),body.index('wrap_delta_section("dashboard_indices"'))
        board=s.split("    def repair_board():",1)[1].split("    def dashboard():",1)[0]
        self.assertNotIn("get_market_data(",board)
        self.assertNotIn("dhan_feed.",board)
        self.assertIn("host.update()",board)

    def test_manual_request_never_bypasses_cooldown_or_duplicates_worker(self):
        r=LocalObserverRecovery()
        self.assertEqual(r.request_retry(1,99),"NO_PENDING_REPAIR")
        r.failed(1,100,ValueError(),"capture")
        self.assertEqual(r.request_retry(1,114),"COOLDOWN")
        self.assertFalse(r.ready(1,114))
        self.assertEqual(r.request_retry(2,115),"NO_PENDING_REPAIR")
        self.assertEqual(r.request_retry(1,115),"QUEUED_EXISTING_OBSERVER")
        r.advance(1,115,"REPAIRING")
        self.assertEqual(r.request_retry(1,116),"ALREADY_RUNNING")
        self.assertEqual(r.report(116)["events"][-1]["state"],"MANUAL_RETRY_REQUESTED")
        self.assertTrue(r.report(116)["pending"])
