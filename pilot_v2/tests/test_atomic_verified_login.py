"""Offline atomic P-256 login + concurrent key rotation, no HTTP/Dhan."""
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from pilot_v2.atomic_verified_login import AtomicVerifiedLogin
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.durable_device_keys import DurableDeviceKeys
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.device_sessions import SessionDenied, VerifiedDevice
from pilot_v2.device_verifier import DeviceProof, P256ChallengeVerifier, encode_b64

M = "master_device_000001"
D = "second_device_00001"

def public(key):
    return key.public_key().public_bytes(serialization.Encoding.DER,
                                         serialization.PublicFormat.SubjectPublicKeyInfo)

def signed(device, nonce, private):
    sig = private.sign(P256ChallengeVerifier.signed_message(device,nonce),
                       ec.ECDSA(hashes.SHA256()))
    return DeviceProof(device, nonce, encode_b64(sig))

class AtomicLoginTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        path=Path(temp.name)/"auth.sqlite"
        self.t=[1000.]
        self.s1=DurableDeviceSessions(path,clock=lambda:self.t[0])
        self.s2=DurableDeviceSessions(path,clock=lambda:self.t[0])
        self.s1.bootstrap(M,authorize_bootstrap=lambda x:x==M)
        self.owner=self.s1.issue_verified(VerifiedDevice(M))
        self.k1=DurableDeviceKeys(self.s1)
        self.k2=DurableDeviceKeys(self.s2)
        self.masterkey=ec.generate_private_key(ec.SECP256R1())
        self.oldkey=ec.generate_private_key(ec.SECP256R1())
        self.newkey=ec.generate_private_key(ec.SECP256R1())
        keys={M:public(self.masterkey)}
        self.v1=DurableP256ChallengeVerifier(path,keys,clock=lambda:self.t[0],
                                               trusted_key_resolver=self.k1.public_key)
        self.v2=DurableP256ChallengeVerifier(path,keys,clock=lambda:self.t[0],
                                               trusted_key_resolver=self.k2.public_key)
        self.a=AtomicVerifiedLogin(self.v1,self.s1)
        self.b=AtomicVerifiedLogin(self.v2,self.s2)

    def enroll(self,key):
        p=self.k1.request(self.owner,D,public(key))
        self.k2.complete(self.owner,signed(D,p.challenge,key),["quotes"])

    def test_master_and_delegated_across_two_workers(self):
        owner=self.b.login(signed(M,self.a.challenge(M),self.masterkey))
        self.assertEqual(self.a.read_feed(owner,"quotes"),M)
        # Login rotates the existing master token by design. Use the newly
        # authenticated master session for all subsequent delegated changes.
        self.owner=owner
        self.enroll(self.oldkey)
        second=self.a.login(signed(D,self.b.challenge(D),self.oldkey))
        self.assertEqual(self.b.read_feed(second,"quotes"),D)
        with self.assertRaises(SessionDenied):
            self.b.read_feed(second,"indices")

    def test_rotation_invalidates_old_key_and_previous_sessions(self):
        self.enroll(self.oldkey)
        initial=self.a.login(signed(D,self.a.challenge(D),self.oldkey))
        stale=self.b.challenge(D)
        self.enroll(self.newkey)
        with self.assertRaises(SessionDenied):
            self.b.read_feed(initial,"quotes")
        with self.assertRaises(SessionDenied):
            self.a.login(signed(D,stale,self.oldkey))
        with self.assertRaises(SessionDenied):
            self.b.login(signed(D,self.b.challenge(D),self.oldkey))
        fresh=self.a.login(signed(D,self.b.challenge(D),self.newkey))
        self.assertEqual(self.b.read_feed(fresh,"quotes"),D)

    def test_wrong_signature_consumes_nonce_across_workers(self):
        self.enroll(self.oldkey)
        nonce=self.a.challenge(D)
        with self.assertRaises(SessionDenied):
            self.b.login(signed(D,nonce,self.newkey))
        with self.assertRaises(SessionDenied):
            self.a.login(signed(D,nonce,self.oldkey))

    def test_disable_and_missing_enrollment_fail_closed(self):
        with self.assertRaises(SessionDenied):
            self.a.challenge(D)
        self.enroll(self.oldkey)
        nonce=self.a.challenge(D)
        self.s2.master_grant(self.owner,D,["quotes"],enabled=False)
        with self.assertRaises(SessionDenied):
            self.b.login(signed(D,nonce,self.oldkey))

    def test_expired_nonce_and_session(self):
        nonce=self.a.challenge(M)
        self.t[0]+=60
        with self.assertRaises(SessionDenied):
            self.b.login(signed(M,nonce,self.masterkey))
        valid=self.a.login(signed(M,self.a.challenge(M),self.masterkey))
        self.t[0]+=900
        with self.assertRaises(SessionDenied):
            self.b.read_feed(valid,"quotes")

    def test_refuse_mismatched_session_and_nonce_store(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        other=DurableDeviceSessions(Path(tmp.name)/"other.sqlite",
                                   clock=lambda:self.t[0])
        with self.assertRaises(ValueError):
            AtomicVerifiedLogin(self.v1,other)
        with self.assertRaises(SessionDenied):
            self.a.login({"role":"master"})

if __name__=="__main__":
    unittest.main()
