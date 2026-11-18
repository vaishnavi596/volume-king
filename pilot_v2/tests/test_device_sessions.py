"""Offline-only V2-002 opaque session, master authorization and expiry tests."""
import unittest
from pilot_v2.device_policy import DeviceRegistry
from pilot_v2.device_sessions import DeviceSessionGateway, VerifiedDevice, SessionDenied

MASTER = "master_device_000001"
SECOND = "second_device_00001"
THIRD = "third_device_000001"
FOURTH = "fourth_device_000001"

class SessionGatewayTests(unittest.TestCase):
    def setUp(self):
        self.now = [1000.]
        self.registry = DeviceRegistry()
        self.registry.enroll_master(MASTER, verified_bootstrap=True)
        allowed_proofs = {"master-proof": MASTER,
                          "second-proof": SECOND,
                          "third-proof": THIRD,
                          "fourth-proof": FOURTH}
        self.gateway = DeviceSessionGateway(
            self.registry,
            lambda proof: (VerifiedDevice(allowed_proofs[proof])
                           if proof in allowed_proofs else None),
            clock=lambda: self.now[0], ttl_seconds=60)

    def test_no_claimed_device_or_role_can_log_in_without_verifier(self):
        for proof in ({ "device_id": MASTER, "role": "master" },
                      MASTER, "fake-master", None):
            with self.subTest(proof=repr(proof)), self.assertRaises(SessionDenied):
                self.gateway.issue(proof)

    def test_master_grants_limited_access_to_2_phones(self):
        master = self.gateway.issue("master-proof")
        self.gateway.assign(master, SECOND, {"quotes", "indices"})
        self.gateway.assign(master, THIRD, {"candles"})
        second = self.gateway.issue("second-proof")
        third = self.gateway.issue("third-proof")
        self.assertEqual(self.gateway.check_feed(second, "quotes"), SECOND)
        self.assertEqual(self.gateway.check_feed(third, "candles"), THIRD)
        for token, feed in ((second, "options"), (third, "quotes")):
            with self.assertRaises(SessionDenied):
                self.gateway.check_feed(token, feed)
        with self.assertRaises(Exception):
            self.gateway.assign(second, FOURTH, {"quotes"})
        with self.assertRaises(Exception):
            self.gateway.assign(master, FOURTH, {"quotes"})

    def test_master_disable_immediately_revokes_old_secondary_session(self):
        master = self.gateway.issue("master-proof")
        self.gateway.assign(master, SECOND, {"quotes"})
        secondary = self.gateway.issue("second-proof")
        self.gateway.assign(master, SECOND, {"quotes"}, enabled=False)
        with self.assertRaises(SessionDenied):
            self.gateway.check_feed(secondary, "quotes")
        with self.assertRaises(SessionDenied):
            self.gateway.issue("second-proof")
        self.gateway.assign(master, SECOND, {"quotes"}, enabled=True)
        new_secondary = self.gateway.issue("second-proof")
        self.assertNotEqual(new_secondary, secondary)
        self.gateway.revoke(master, SECOND)
        with self.assertRaises(SessionDenied):
            self.gateway.check_feed(new_secondary, "quotes")

    def test_expiry_logout_rotation_and_invalid_tokens(self):
        original = self.gateway.issue("master-proof")
        replacement = self.gateway.issue("master-proof")
        self.assertNotEqual(original, replacement)
        with self.assertRaises(SessionDenied):
            self.gateway.identity(original)
        self.now[0] += 60
        with self.assertRaises(SessionDenied):
            self.gateway.identity(replacement)
        fresh = self.gateway.issue("master-proof")
        self.gateway.logout(fresh)
        for token in (fresh, "", "wrong", "🔑" * 30):
            with self.subTest(token=repr(token)[:24]), self.assertRaises(SessionDenied):
                self.gateway.identity(token)

    def test_server_proof_provider_is_mandatory(self):
        with self.assertRaises(ValueError):
            DeviceSessionGateway(self.registry, None)
        with self.assertRaises(ValueError):
            DeviceSessionGateway(self.registry, lambda _: None, ttl_seconds=0)

if __name__=="__main__":
    unittest.main()
