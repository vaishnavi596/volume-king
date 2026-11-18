"""Synthetic P-256 master-approved enroll/rotate tests; no mobile/network."""
import tempfile
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pilot_v2.device_sessions import VerifiedDevice, SessionDenied
from pilot_v2.device_verifier import DeviceProof,P256ChallengeVerifier,encode_b64
from pilot_v2.durable_device_sessions import DurableDeviceSessions
from pilot_v2.durable_challenges import DurableP256ChallengeVerifier
from pilot_v2.durable_device_keys import DurableDeviceKeys

M="master_device_000001"
D="second_device_00001"
T="third_device_000001"
F="fourth_device_000001"
E="fifth_device_0000001"

def der(key):
    return key.public_key().public_bytes(serialization.Encoding.DER,
                                        serialization.PublicFormat.SubjectPublicKeyInfo)

class DurableKeysTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        path=Path(self.tmp.name)/"auth.sqlite"
        self.now=[1000.]
        self.s1=DurableDeviceSessions(path,clock=lambda:self.now[0])
        self.s2=DurableDeviceSessions(path,clock=lambda:self.now[0])
        # Durable verifier constructor creates login_challenge table.
        self.masterkey=ec.generate_private_key(ec.SECP256R1())
        self.v=DurableP256ChallengeVerifier(path,{M:der(self.masterkey)},
                       clock=lambda:self.now[0])
        self.s1.bootstrap(M,authorize_bootstrap=lambda x:x==M)
        self.master=self.s1.issue_verified(VerifiedDevice(M))
        self.keys1=DurableDeviceKeys(self.s1)
        self.keys2=DurableDeviceKeys(self.s2)
        self.old=ec.generate_private_key(ec.SECP256R1())

    def signed(self,device,nonce,key):
        signature=key.sign(P256ChallengeVerifier.signed_message(device,nonce),
                           ec.ECDSA(hashes.SHA256()))
        return DeviceProof(device,nonce,encode_b64(signature))

    def enroll(self,device,key,feeds=("quotes",)):
        pending=self.keys1.request(self.master,device,der(key))
        self.keys2.complete(self.master,self.signed(device,pending.challenge,key),feeds)
        return pending

    def test_master_proof_creates_bound_key_and_restricted_grant(self):
        pending=self.enroll(D,self.old)
        self.assertEqual(len(pending.fingerprint),64)
        self.assertEqual(self.keys1.public_key(D),der(self.old))
        token=self.s2.issue_verified(VerifiedDevice(D))
        self.assertEqual(self.s1.authorize(token,"quotes"),D)
        with self.assertRaises(SessionDenied):
            self.s1.authorize(token,"options")

    def test_rotation_revokes_old_session_and_replaces_key(self):
        self.enroll(D,self.old)
        oldsession=self.s1.issue_verified(VerifiedDevice(D))
        new=ec.generate_private_key(ec.SECP256R1())
        self.enroll(D,new,("indices",))
        self.assertEqual(self.keys2.public_key(D),der(new))
        self.assertNotEqual(self.keys2.public_key(D),der(self.old))
        with self.assertRaises(SessionDenied):
            self.s2.authorize(oldsession,"quotes")
        fresh=self.s1.issue_verified(VerifiedDevice(D))
        self.assertEqual(self.s2.authorize(fresh,"indices"),D)
        with self.assertRaises(SessionDenied):
            self.s2.authorize(fresh,"quotes")

    def test_wrong_signature_consumes_pending_without_enrollment(self):
        pending=self.keys1.request(self.master,D,der(self.old))
        wrong=ec.generate_private_key(ec.SECP256R1())
        with self.assertRaises(SessionDenied):
            self.keys2.complete(self.master,self.signed(D,pending.challenge,wrong),["quotes"])
        with self.assertRaises(SessionDenied):
            self.keys2.complete(self.master,self.signed(D,pending.challenge,self.old),["quotes"])
        self.assertIsNone(self.keys1.public_key(D))

    def test_invalid_master_and_expired_pending_do_not_register(self):
        pending=self.keys1.request(self.master,D,der(self.old))
        self.s1.logout(self.master)
        with self.assertRaises(SessionDenied):
            self.keys2.complete(self.master,self.signed(D,pending.challenge,self.old),["quotes"])
        self.master=self.s1.issue_verified(VerifiedDevice(M))
        new=self.keys1.request(self.master,D,der(self.old))
        self.now[0]+=91
        with self.assertRaises(SessionDenied):
            self.keys2.complete(self.master,self.signed(D,new.challenge,self.old),["quotes"])

    def test_capacity_and_master_key_protection(self):
        self.enroll(D,self.old)
        self.enroll(T,ec.generate_private_key(ec.SECP256R1()))
        self.enroll(F,ec.generate_private_key(ec.SECP256R1()))
        self.assertIsNotNone(self.keys2.public_key(F))
        with self.assertRaises(SessionDenied):
            self.keys2.request(self.master,E,der(self.old))
        with self.assertRaises(SessionDenied):
            self.keys2.request(self.master,M,der(self.old))
        with self.assertRaises(SessionDenied):
            self.keys2.request(self.master,D,b"invalid")

if __name__=="__main__":
    unittest.main()
