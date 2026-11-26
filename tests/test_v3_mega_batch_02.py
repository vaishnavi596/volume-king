import unittest
import tempfile
from pathlib import Path
from v3_brain_staging_memory import StagingBrainLedger
from refresh_coordinator import LaneCoordinator
from v3_local_observer_recovery import LocalObserverRecovery

class MegaBatch02Tests(unittest.TestCase):
    def test_brain_nested_secrets_and_auth(self):
        ledger=StagingBrainLedger(":memory:",{"phone1":"a"*20})
        try:
            args=dict(device_id="phone1",credential="a"*20,event_id="event-001",kind="prediction_event",created_at=100)
            for payload in ({"data":[{"Access_Token":"x"}]}, {"data":{" password ":"x"}}):
                with self.assertRaises(ValueError):ledger.append(**args,payload=payload)
            with self.assertRaises(PermissionError):ledger.since(device_id=[],credential="a"*20)
            with self.assertRaises(PermissionError):ledger.since(device_id="phone1",credential="é"*20)
            self.assertEqual(ledger.audit()["stored_events"],0)
            self.assertFalse(ledger.audit()["live_votes_enabled"])
        finally:ledger.close()

    def test_restore_refuses_dangling_symlink(self):
        try:from cryptography.fernet import Fernet
        except ImportError:self.skipTest("optional encryption")
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"alias"
            p.symlink_to(Path(folder)/"absent")
            with self.assertRaises(FileExistsError):
                StagingBrainLedger.restore_to_new(destination=p,encrypted_blob=b"",encryption_key=Fernet.generate_key(),device_credentials={"phone1":"a"*20})

    def test_invalidated_flight_cannot_repopulate_cache(self):
        c=LaneCoordinator(clock=lambda:10)
        def fetch():
            c.invalidate("quotes","a")
            return {"value":1}
        self.assertEqual(c.run("quotes","a",fetch,ttl_seconds=30),{"value":1})
        self.assertEqual(c.cache_size(),0)
        self.assertEqual(c.run("quotes","a",lambda:{"value":2},ttl_seconds=30),{"value":2})

    def test_reuse_predicate_cannot_mutate_cached_object(self):
        c=LaneCoordinator(clock=lambda:10,max_cached=2)
        c.run("quotes","a",lambda:{"value":1},ttl_seconds=30)
        c.run("quotes","b",lambda:{"value":2},ttl_seconds=30)
        def mutate(value,age):
            value["value"]=999
            return True
        self.assertEqual(c.run("quotes","a",lambda:None,ttl_seconds=30,reuse_if=mutate),{"value":1})
        c.run("quotes","b",lambda:{"value":3},ttl_seconds=0)
        self.assertEqual(c.cache_size(),2)

    def test_invalid_clock_and_recovery_callbacks(self):
        c=LaneCoordinator(clock=lambda:float("nan"))
        c.run("quotes","a",lambda:1,ttl_seconds=30)
        self.assertEqual(c.cache_size(),0)
        r=LocalObserverRecovery()
        r.failed(1,100,RuntimeError(),"capture")
        self.assertFalse(r.ready(2,float("nan")))
        r.succeeded(2,float("inf"),1)
        self.assertEqual(r.request_retry(1,float("nan")),"INVALID_CONTEXT")
        self.assertTrue(r.report(101)["pending"])
        self.assertEqual(r.report(101)["generation"],1)
        self.assertEqual(r.report(101)["invalid_callbacks"],3)
