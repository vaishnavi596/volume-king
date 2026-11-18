"""SQLite atomic shared P-256 challenge tests: no HTTP or device data."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import hashes,serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.device_verifier import DeviceProof,P256ChallengeVerifier,encode_b64
from pilot_v2.device_sessions import SessionDenied
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.verified_login_gateway import VerifiedLoginGateway

MASTER="master_device_000001"

class SharedP256Tests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.t=[1000.]
        path=Path(tmp.name)/"session.sqlite"
        self.key=ec.generate_private_key(ec.SECP256R1())
        der=self.key.public_key().public_bytes(
            serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)
        keys={MASTER:der}
        self.one=DurableP256ChallengeVerifier(path,keys,clock=lambda:self.t[0])
        self.two=DurableP256ChallengeVerifier(path,keys,clock=lambda:self.t[0])
        self.s1=DurableDeviceSessions(path,clock=lambda:self.t[0])
        self.s2=DurableDeviceSessions(path,clock=lambda:self.t[0])
        self.s1.bootstrap(MASTER,authorize_bootstrap=lambda _:True)
        self.g1=VerifiedLoginGateway(self.one,self.s1)
        self.g2=VerifiedLoginGateway(self.two,self.s2)
        self.path=path

    def signed(self,nonce,key=None):
        signature=(key or self.key).sign(
            P256ChallengeVerifier.signed_message(MASTER,nonce),
            ec.ECDSA(hashes.SHA256()))
        return DeviceProof(MASTER,nonce,encode_b64(signature))

    def test_challenge_issued_worker_one_login_worker_two_and_replay_fails(self):
        nonce=self.g1.challenge(MASTER)
        proof=self.signed(nonce)
        token=self.g2.login(proof)
        self.assertEqual(self.g1.read_feed(token,"quotes"),MASTER)
        with self.assertRaises(SessionDenied):
            self.g1.login(proof)

    def test_wrong_signature_consumes_shared_nonce(self):
        nonce=self.g1.challenge(MASTER)
        wrong=ec.generate_private_key(ec.SECP256R1())
        with self.assertRaises(SessionDenied):
            self.g2.login(self.signed(nonce,wrong))
        with self.assertRaises(SessionDenied):
            self.g1.login(self.signed(nonce))

    def test_new_challenge_invalidates_previous_across_workers(self):
        old=self.g1.challenge(MASTER)
        fresh=self.g2.challenge(MASTER)
        with self.assertRaises(SessionDenied):
            self.g1.login(self.signed(old))
        # Any failed proof consumes the most recent outstanding nonce.
        with self.assertRaises(SessionDenied):
            self.g2.login(self.signed(fresh))
        nxt=self.g1.challenge(MASTER)
        self.assertEqual(self.g2.read_feed(self.g1.login(self.signed(nxt)),"quotes"),MASTER)

    def test_expiry_clock_rollback_and_restart(self):
        nonce=self.g1.challenge(MASTER)
        self.t[0]+=60
        with self.assertRaises(SessionDenied):
            self.g2.login(self.signed(nonce))
        nxt=self.g1.challenge(MASTER)
        self.t[0]-=1
        with self.assertRaises(SessionDenied):
            self.g2.login(self.signed(nxt))
        self.t[0]+=1
        another=self.g2.challenge(MASTER)
        reopened=DurableP256ChallengeVerifier(
            self.path,{MASTER:self.one._keys[MASTER].public_bytes(
                serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo)},
            clock=lambda:self.t[0])
        self.assertEqual(reopened.verify(self.signed(another)).device_id,MASTER)

    def test_hash_only_in_storage_and_forged_role_denied(self):
        nonce=self.g1.challenge(MASTER)
        with sqlite3.connect(self.path) as db:
            digest,=db.execute("SELECT digest FROM login_challenge WHERE device=?",
                               (MASTER,)).fetchone()
        self.assertEqual(len(digest),64)
        self.assertNotEqual(digest,nonce)
        with self.assertRaises(SessionDenied):
            self.g2.login({"device_id":MASTER,"master":True})
        self.assertEqual(self.g1.login(self.signed(nonce)) is not None,True)

if __name__=="__main__":
    unittest.main()
