"""P-256 real signature tests; never calls Oracle, Dhan or device hardware."""
import unittest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from pilot_v2.device_sessions import DeviceSessionGateway, SessionDenied
from pilot_v2.device_policy import DeviceRegistry
from pilot_v2.device_verifier import P256ChallengeVerifier, DeviceProof, encode_b64
from pilot_v2.broker_token_status import classify_dhan_token

MASTER="master_device_000001"
SECOND="second_device_00001"

class P256DeviceLoginTests(unittest.TestCase):
    def setUp(self):
        self.now=[100.]
        self.master_key=ec.generate_private_key(ec.SECP256R1())
        self.second_key=ec.generate_private_key(ec.SECP256R1())
        def public(k):
            return k.public_key().public_bytes(
                serialization.Encoding.DER,
                serialization.PublicFormat.SubjectPublicKeyInfo)
        self.registry=DeviceRegistry()
        self.registry.enroll_master(MASTER, verified_bootstrap=True)
        self.verifier=P256ChallengeVerifier({MASTER:public(self.master_key),
                                            SECOND:public(self.second_key)},
                                           clock=lambda:self.now[0],ttl_seconds=30)
        self.sessions=DeviceSessionGateway(self.registry,self.verifier.verify,
                                          clock=lambda:self.now[0],ttl_seconds=120)

    def make_proof(self,device,key):
        challenge=self.verifier.challenge(device)
        signature=key.sign(self.verifier.signed_message(device,challenge),
                           ec.ECDSA(hashes.SHA256()))
        return DeviceProof(device,challenge,encode_b64(signature))

    def test_verified_master_may_grant_then_secondary_may_access_selected_feed(self):
        master=self.sessions.issue(self.make_proof(MASTER,self.master_key))
        self.sessions.assign(master,SECOND,{"quotes","indices"})
        second=self.sessions.issue(self.make_proof(SECOND,self.second_key))
        self.assertEqual(self.sessions.check_feed(second,"quotes"),SECOND)
        with self.assertRaises(SessionDenied):
            self.sessions.check_feed(second,"options")

    def test_wrong_key_invalid_signature_consumes_challenge(self):
        bad=self.make_proof(MASTER,self.second_key)
        for _ in range(2):
            with self.assertRaises(SessionDenied):
                self.sessions.issue(bad)
        good=self.make_proof(MASTER,self.master_key)
        self.assertIsInstance(self.sessions.issue(good),str)

    def test_replay_and_expiry_and_forged_identity(self):
        p=self.make_proof(MASTER,self.master_key)
        self.sessions.issue(p)
        with self.assertRaises(SessionDenied):
            self.sessions.issue(p)
        stale=self.make_proof(MASTER,self.master_key)
        self.now[0]+=30
        with self.assertRaises(SessionDenied):
            self.sessions.issue(stale)
        with self.assertRaises(SessionDenied):
            self.sessions.issue({"role":"master","device_id":MASTER})

    def test_challenge_is_bound_to_device_id(self):
        valid=self.make_proof(MASTER,self.master_key)
        self.verifier.challenge(SECOND)
        with self.assertRaises(SessionDenied):
            self.sessions.issue(DeviceProof(SECOND,valid.challenge,valid.signature))

    def test_unknown_key_and_malformed_public_key_denied(self):
        with self.assertRaises(SessionDenied):
            self.verifier.challenge("missing_device_0001")
        with self.assertRaises(ValueError):
            P256ChallengeVerifier({MASTER:b"invalid"})

class DhanTokenStateTests(unittest.TestCase):
    def test_broker_expiry_never_extends_mobile_session(self):
        self.assertEqual(classify_dhan_token(
            now=100,expires_at=1000,renewal_supported=False,configured=True,
            renewal_window_seconds=60).state,"CONNECTED")
        near=classify_dhan_token(now=950,expires_at=1000,
                                  renewal_supported=False,configured=True,
                                  renewal_window_seconds=60)
        self.assertEqual(near.state,"REAUTH_SOON")
        self.assertTrue(near.needs_user_reauth)
        expired=classify_dhan_token(now=1000,expires_at=1000,
                                     renewal_supported=True,configured=True)
        self.assertEqual(expired.state,"REAUTH_REQUIRED")
        self.assertFalse(expired.can_fetch)
        supported=classify_dhan_token(now=950,expires_at=1000,
                                      renewal_supported=True,configured=True,
                                      renewal_window_seconds=60)
        self.assertEqual(supported.state,"RENEWAL_DUE")
        self.assertTrue(supported.can_fetch)

    def test_invalid_and_unconfigured_fails_closed(self):
        self.assertFalse(classify_dhan_token(
            now=100,expires_at=1000,renewal_supported=False,
            configured=False).can_fetch)
        for kwargs in ({"now":float("nan")},{"renewal_supported":1},
                       {"configured":"yes"},{"expires_at":-1}):
            params=dict(now=100,expires_at=1000,
                        renewal_supported=False,configured=True)
            params.update(kwargs)
            with self.subTest(kwargs=kwargs),self.assertRaises(ValueError):
                classify_dhan_token(**params)

if __name__=="__main__":
    unittest.main()
