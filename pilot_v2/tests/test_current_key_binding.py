"""FT-1 current device key resolution and CI efficiency regression tests.

All keys and sessions are synthetic. No Android, Oracle, Dhan or network.
"""
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pilot_v2.device_sessions import VerifiedDevice, SessionDenied
from pilot_v2.device_verifier import DeviceProof, P256ChallengeVerifier, encode_b64
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.durable_device_keys import DurableDeviceKeys
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.verified_login_gateway import VerifiedLoginGateway

MASTER="master_device_000001"
SECOND="second_device_00001"

def der(private):
    return private.public_key().public_bytes(
        serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)

def proof(device, nonce, key):
    sig=key.sign(P256ChallengeVerifier.signed_message(device,nonce),
                 ec.ECDSA(hashes.SHA256()))
    return DeviceProof(device,nonce,encode_b64(sig))

class CurrentKeyGateTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path=Path(tmp.name)/"keys.sqlite"
        self.now=[1000.]
        self.master_key=ec.generate_private_key(ec.SECP256R1())
        self.old_key=ec.generate_private_key(ec.SECP256R1())
        self.new_key=ec.generate_private_key(ec.SECP256R1())
        self.sessions=DurableDeviceSessions(path,clock=lambda:self.now[0])
        self.sessions2=DurableDeviceSessions(path,clock=lambda:self.now[0])
        self.sessions.bootstrap(MASTER,authorize_bootstrap=lambda d:d==MASTER)
        self.master=self.sessions.issue_verified(VerifiedDevice(MASTER))
        self.keys=DurableDeviceKeys(self.sessions)
        self.keys2=DurableDeviceKeys(self.sessions2)
        self.v1=DurableP256ChallengeVerifier(
            path,{MASTER:der(self.master_key)},
            trusted_key_resolver=self.keys.public_key,clock=lambda:self.now[0])
        self.v2=DurableP256ChallengeVerifier(
            path,{MASTER:der(self.master_key)},
            trusted_key_resolver=self.keys2.public_key,clock=lambda:self.now[0])
        self.g1=VerifiedLoginGateway(self.v1,self.sessions)
        self.g2=VerifiedLoginGateway(self.v2,self.sessions2)

    def register(self, key):
        pending=self.keys.request(self.master,SECOND,der(key))
        self.keys2.complete(self.master,proof(SECOND,pending.challenge,key),["quotes"])

    def test_current_key_only_after_enrollment(self):
        with self.assertRaises(SessionDenied):
            self.g1.challenge(SECOND)
        self.register(self.old_key)
        first=self.g2.challenge(SECOND)
        previous=self.g1.login(proof(SECOND,first,self.old_key))
        self.assertEqual(self.g2.read_feed(previous,"quotes"),SECOND)
        self.register(self.new_key)
        with self.assertRaises(SessionDenied):
            self.g1.read_feed(previous,"quotes")
        stale_nonce=self.g1.challenge(SECOND)
        with self.assertRaises(SessionDenied):
            self.g2.login(proof(SECOND,stale_nonce,self.old_key))
        fresh_nonce=self.g2.challenge(SECOND)
        fresh_session=self.g1.login(proof(SECOND,fresh_nonce,self.new_key))
        self.assertEqual(self.g2.read_feed(fresh_session,"quotes"),SECOND)

    def test_rotation_revokes_unredeemed_challenge(self):
        self.register(self.old_key)
        previous=self.g1.challenge(SECOND)
        self.register(self.new_key)
        with self.assertRaises(SessionDenied):
            self.g2.login(proof(SECOND,previous,self.old_key))

    def test_disabled_device_cannot_challenge_or_verify(self):
        self.register(self.old_key)
        challenge=self.g1.challenge(SECOND)
        self.sessions.master_grant(self.master,SECOND,["quotes"],enabled=False)
        with self.assertRaises(SessionDenied):
            self.g2.challenge(SECOND)
        with self.assertRaises(SessionDenied):
            self.g2.login(proof(SECOND,challenge,self.old_key))

    def test_no_dynamic_resolver_rejects_unknown_secondary(self):
        limited=DurableP256ChallengeVerifier(
            self.sessions._path,{MASTER:der(self.master_key)},
            clock=lambda:self.now[0])
        with self.assertRaises(SessionDenied):
            limited.challenge(SECOND)

if __name__=="__main__":
    unittest.main()
