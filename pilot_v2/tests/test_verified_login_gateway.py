"""Real P-256 synthetic proof + persistent V2 sessions, not an HTTP test."""
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from pilot_v2.device_verifier import P256ChallengeVerifier, DeviceProof, encode_b64
from pilot_v2.device_sessions import SessionDenied
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.verified_login_gateway import VerifiedLoginGateway

MASTER="master_device_000001"
SECOND="second_device_00001"

def public(key):
    return key.public_key().public_bytes(
        serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)

class VerifiedLoginTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory()
        self.addCleanup(d.cleanup)
        self.clock=[1000.]
        path=Path(d.name)/"auth.sqlite"
        self.s1=DurableDeviceSessions(path,clock=lambda:self.clock[0])
        self.s2=DurableDeviceSessions(path,clock=lambda:self.clock[0])
        self.s1.bootstrap(MASTER,authorize_bootstrap=lambda d:d==MASTER)
        self.masterkey=ec.generate_private_key(ec.SECP256R1())
        self.otherkey=ec.generate_private_key(ec.SECP256R1())
        keys={MASTER:public(self.masterkey),SECOND:public(self.otherkey)}
        self.v1=P256ChallengeVerifier(keys,clock=lambda:self.clock[0])
        self.v2=P256ChallengeVerifier(keys,clock=lambda:self.clock[0])
        self.g1=VerifiedLoginGateway(self.v1,self.s1)
        self.g2=VerifiedLoginGateway(self.v2,self.s2)

    def proof(self,gateway,device,key):
        nonce=gateway.challenge(device)
        sig=key.sign(P256ChallengeVerifier.signed_message(device,nonce),
                     ec.ECDSA(hashes.SHA256()))
        return DeviceProof(device,nonce,encode_b64(sig))

    def test_master_proof_then_cross_worker_delegated_restrictions_and_revoke(self):
        m=self.g1.login(self.proof(self.g1,MASTER,self.masterkey))
        self.g2.master_grant(m,SECOND,["quotes"])
        delegated=self.g2.login(self.proof(self.g2,SECOND,self.otherkey))
        self.assertEqual(self.g1.read_feed(delegated,"quotes"),SECOND)
        with self.assertRaises(SessionDenied):
            self.g2.read_feed(delegated,"options")
        with self.assertRaises(SessionDenied):
            self.g2.master_grant(delegated,SECOND,["options"])
        self.g1.master_revoke(m,SECOND)
        with self.assertRaises(SessionDenied):
            self.g2.read_feed(delegated,"quotes")

    def test_forged_master_role_and_wrong_key_never_issue_session(self):
        with self.assertRaises(SessionDenied):
            self.g1.login({"device_id":MASTER,"role":"master"})
        with self.assertRaises(SessionDenied):
            self.g1.login(self.proof(self.g1,MASTER,self.otherkey))
        legitimate=self.g1.login(self.proof(self.g1,MASTER,self.masterkey))
        self.assertEqual(self.g1.read_feed(legitimate,"quotes"),MASTER)

    def test_signed_proof_cannot_replay_and_session_ends_at_expiry(self):
        valid=self.proof(self.g1,MASTER,self.masterkey)
        token=self.g1.login(valid)
        with self.assertRaises(SessionDenied):
            self.g1.login(valid)
        self.clock[0]+=900
        with self.assertRaises(SessionDenied):
            self.g2.read_feed(token,"quotes")

    def test_unenrolled_secondary_key_still_cannot_login(self):
        with self.assertRaises(SessionDenied):
            self.g1.login(self.proof(self.g1,SECOND,self.otherkey))

if __name__=="__main__":
    unittest.main()
