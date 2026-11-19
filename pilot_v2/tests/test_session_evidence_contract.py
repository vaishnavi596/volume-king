"""Exact server-side Master/delegate policy -> atomic app-evidence test."""
import sys
import unittest
from pathlib import Path
from datetime import datetime, timezone, timedelta
from pilot_v2.device_policy import DeviceRegistry
from pilot_v2.device_sessions import DeviceSessionGateway, VerifiedDevice
from pilot_v2.session_evidence_contract import (
    deliver_session_authorized_evidence, SessionEvidenceError,
)

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_evidence_batch import apply_staged_evidence_batch
from evidence_inbox import DeviceEvidenceInbox

MASTER = "master_device_000001"
SECOND = "second_device_00001"
T0 = int(datetime(2026, 11, 18, 9, 15,
                  tzinfo=timezone(timedelta(hours=5, minutes=30))).timestamp())

def events():
    return [
        {"kind": "candles", "symbol": "TCS", "timeframe": "1m",
         "revision": 1, "bars": [
            {"timestamp": T0 + i*60, "open": 100., "high": 101.,
             "low": 99., "close": 100., "volume": 1., "completed": True}
            for i in range(3)]},
        {"kind": "expiries", "symbol": "TCS", "revision": 1,
         "available": ["2026-11-26"]},
    ]

class SessionEvidenceContractTests(unittest.TestCase):
    def setUp(self):
        self.now = [1000.]
        self.registry = DeviceRegistry()
        self.registry.enroll_master(MASTER, verified_bootstrap=True)
        names = {"valid-master-proof": MASTER, "valid-second-proof": SECOND}
        self.sessions = DeviceSessionGateway(
            self.registry, lambda proof: (
                VerifiedDevice(names[proof]) if proof in names else None),
            clock=lambda: self.now[0], ttl_seconds=60)
        self.master = self.sessions.issue("valid-master-proof")
        self.cache = DeviceEvidenceInbox()

    def deliver(self, token, events_value=None):
        return deliver_session_authorized_evidence(
            self.sessions, token, self.cache,
            events() if events_value is None else events_value,
            ("TCS",), validated_batch_apply=apply_staged_evidence_batch)

    def test_master_authorized_both_feeds_then_delegate_missing_options_denied(self):
        master_result = self.deliver(self.master)
        self.assertEqual(master_result["updated"], 2)
        self.sessions.assign(self.master, SECOND, ("candles",))
        second = self.sessions.issue("valid-second-proof")
        with self.assertRaises(SessionEvidenceError):
            self.deliver(second, [dict(e, revision=2) for e in events()])
        self.assertEqual(self.cache.expiries.available(
            "TCS", selected_equities=("TCS",)), ("2026-11-26",))

    def test_delegated_allowed_and_revoked_before_cache_change(self):
        self.sessions.assign(self.master, SECOND, ("candles", "options"))
        second = self.sessions.issue("valid-second-proof")
        self.assertEqual(self.deliver(second)["updated"], 2)
        self.sessions.assign(self.master, SECOND, ("candles", "options"),
                             enabled=False)
        with self.assertRaises(SessionEvidenceError):
            self.deliver(second)
        self.assertEqual(self.cache.candles.view(
            "TCS", "1m", selected_equities=("TCS",))["count"], 3)

    def test_expiry_logout_unknown_feed_and_unselected_symbol(self):
        self.now[0] += 61
        with self.assertRaises(SessionEvidenceError):
            self.deliver(self.master)
        self.master = self.sessions.issue("valid-master-proof")
        with self.assertRaises(SessionEvidenceError):
            self.deliver(self.master, [{"kind": "secret"}])
        with self.assertRaises(ValueError):
            self.deliver(self.master, [dict(events()[0], symbol="INFY")])
        self.sessions.logout(self.master)
        with self.assertRaises(SessionEvidenceError):
            self.deliver(self.master)
        self.assertEqual(self.cache.candles.view(
            "TCS", "1m", selected_equities=("TCS",))["status"], "WAIT")

    def test_option_factor_requires_both_options_and_assessment(self):
        self.sessions.assign(self.master, SECOND, ("options",))
        second = self.sessions.issue("valid-second-proof")
        f = {"kind": "option_factors", "symbol": "TCS",
             "timeframe": "3m", "revision": 1, "evidence": {}}
        with self.assertRaises(SessionEvidenceError):
            self.deliver(second, [f])
        self.sessions.assign(self.master, SECOND, ("options", "assessment"))
        second = self.sessions.issue("valid-second-proof")
        # Authorization passes; the downstream validator must still reject
        # empty factors or missing expiry, never fabricate a green signal.
        with self.assertRaises(ValueError):
            self.deliver(second, [f])

if __name__ == "__main__":
    unittest.main()
