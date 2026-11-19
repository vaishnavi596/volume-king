"""Offline V2 evidence source lane: synthetic collector only, NEVER Dhan live."""
import unittest

from pilot_v2.oracle_evidence_lane import DhanEvidenceBatch, OracleDhanEvidenceLane
from pilot_v2.shared_read_budget import SharedReadBudget
from pilot_v2.unified_data_pipeline import PipelineUnavailable

EVENT = {"kind": "expiries", "symbol": "NIFTY", "revision": 1,
         "available": ["2026-11-26"]}


class EvidenceLaneTests(unittest.TestCase):
    def setUp(self):
        self.mono = 100.0
        self.now = 1800000000.0
        self.calls = []
        self.budget = SharedReadBudget(monotonic=lambda: self.mono)
        def collector():
            self.calls.append(1)
            return DhanEvidenceBatch("dhan", len(self.calls), self.now,
                                     [dict(EVENT)])
        self.lane = OracleDhanEvidenceLane(
            transport=collector, read_budget=self.budget,
            monotonic=lambda: self.mono, clock=lambda: self.now,
            cache_seconds=30)

    def test_cached_signed_devices_share_one_dhan_read_budget(self):
        first = self.lane("master-verified")
        first["events"][0]["symbol"] = "MUTATED"
        self.assertEqual(self.lane("delegate-verified")["events"][0]["symbol"],
                         "NIFTY")
        self.assertEqual(len(self.calls), 1)
        self.mono += 31
        self.assertEqual(self.lane("master-verified")["events"][0]["symbol"],
                         "NIFTY")
        self.assertEqual(len(self.calls), 2)
        self.assertEqual(self.budget.status()["next_read_seconds"], 1)

    def test_no_cache_on_missing_provider_and_bad_source(self):
        for invalid in (
                DhanEvidenceBatch("mock", 1, self.now, [dict(EVENT)]),
                DhanEvidenceBatch("dhan", 1, self.now + 30, [dict(EVENT)]),
                DhanEvidenceBatch("dhan", 1, self.now - 90000, [dict(EVENT)]),
                DhanEvidenceBatch("dhan", True, self.now, [dict(EVENT)]),
                DhanEvidenceBatch("dhan", 1, self.now, [{"kind": "orders"}]),
                {"events": [dict(EVENT)]},
        ):
            with self.subTest(invalid=str(invalid)[:65]):
                self.mono += 2
                self.lane._transport = lambda value=invalid: value
                with self.assertRaises(PipelineUnavailable):
                    self.lane("verified-device")
        self.assertIsNone(self.lane._cached)

    def test_shared_quota_denies_no_extra_dhan_fanout(self):
        self.budget.reserve()  # A quote lane used the single quota already.
        with self.assertRaises(PipelineUnavailable):
            self.lane("verified-device")
        self.assertEqual(self.calls, [])
        self.mono += 1.1
        self.lane("verified-device")
        self.assertEqual(len(self.calls), 1)
        self.mono += 31
        self.budget.throttle()  # Simulate read-only Dhan 429 shared cooldown.
        with self.assertRaises(PipelineUnavailable):
            self.lane("verified-device")
        self.assertEqual(len(self.calls), 1)

    def test_revisions_and_source_events_fail_closed_after_expiration(self):
        first = self.lane("verified")
        self.mono += 31
        self.lane._transport = lambda: DhanEvidenceBatch(
            "dhan", 1, self.now, [dict(EVENT)])
        with self.assertRaises(PipelineUnavailable):
            self.lane("verified")
        self.assertEqual(self.lane._cached[1], first)
        self.mono += 2
        self.lane._transport = lambda: (_ for _ in ()).throw(OSError("private"))
        with self.assertRaises(PipelineUnavailable):
            self.lane("verified")
        self.assertEqual(self.lane._cached[1], first)

    def test_invalid_device_and_unreviewed_transport_refused(self):
        for bad in ("", 2, None):
            with self.assertRaises(PipelineUnavailable):
                self.lane(bad)
        for bad in (None, object()):
            with self.assertRaises(ValueError):
                OracleDhanEvidenceLane(
                    transport=bad, read_budget=self.budget,
                    monotonic=lambda: 1, clock=lambda: self.now)


if __name__ == "__main__":
    unittest.main()
