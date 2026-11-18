"""Offline P-256 ownership, master authorization and capacity enrollment gates."""
import unittest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from pilot_v2.device_policy import DeviceRegistry
from pilot_v2.device_sessions import DeviceSessionGateway, VerifiedDevice, SessionDenied
from pilot_v2.device_verifier import DeviceProof, P256ChallengeVerifier, encode_b64
from pilot_v2.device_enrollment import EnrollmentManager

MASTER="master_device_000001"
SECOND="second_device_00001"
THIRD="third_device_000001"
FOURTH="fourth_device_000001"

def public_der(key):
    return key.public_key().public_bytes(
        serialization.Encoding.DER,
        serialization.PublicFormat.SubjectPublicKeyInfo)

class EnrollmentTests(unittest.TestCase):
    def setUp(self):
        self.t=[100.]
        self.registry=DeviceRegistry()
        self.registry.enroll_master(MASTER,verified_bootstrap=True)
        self.sessions=DeviceSessionGateway(
            self.registry,lambda proof: VerifiedDevice(MASTER) if proof=="approved" else None,
            clock=lambda:self.t[0],ttl_seconds=900)
        self.master=self.sessions.issue("approved")
        self.manager=EnrollmentManager(self.sessions,self.registry,clock=lambda:self.t[0])
        self.key=ec.generate_private_key(ec.SECP256R1())

    def signed(self,device,nonce,key):
        message=P256ChallengeVerifier.signed_message(device,nonce)
        signature=key.sign(message,ec.ECDSA(hashes.SHA256()))
        return DeviceProof(device,nonce,encode_b64(signature))

    def test_master_approval_and_key_possession_required(self):
        nonce,fp=self.manager.request(self.master,SECOND,public_der(self.key),["quotes"])
        self.assertEqual(len(fp),64)
        self.assertFalse(self.registry.can_access(SECOND,"quotes"))
        self.assertEqual(self.manager.complete(self.master,self.signed(SECOND,nonce,self.key)),
                         public_der(self.key))
        self.assertTrue(self.registry.can_access(SECOND,"quotes"))
        self.assertFalse(self.registry.can_access(SECOND,"options"))

    def test_wrong_key_consumes_pending_and_replay_denied(self):
        nonce,_=self.manager.request(self.master,SECOND,public_der(self.key),["quotes"])
        badkey=ec.generate_private_key(ec.SECP256R1())
        with self.assertRaises(SessionDenied):
            self.manager.complete(self.master,self.signed(SECOND,nonce,badkey))
        with self.assertRaises(SessionDenied):
            self.manager.complete(self.master,self.signed(SECOND,nonce,self.key))
        self.assertFalse(self.registry.can_access(SECOND,"quotes"))

    def test_master_session_expires_and_no_secondary_can_approve(self):
        nonce,_=self.manager.request(self.master,SECOND,public_der(self.key),["quotes"])
        self.sessions.logout(self.master)
        with self.assertRaises(SessionDenied):
            self.manager.complete(self.master,self.signed(SECOND,nonce,self.key))
        self.assertFalse(self.registry.can_access(SECOND,"quotes"))

    def test_expired_and_aborted_pending_do_not_enroll(self):
        nonce,_=self.manager.request(self.master,SECOND,public_der(self.key),["quotes"])
        self.t[0]+=120
        with self.assertRaises(SessionDenied):
            self.manager.complete(self.master,self.signed(SECOND,nonce,self.key))
        nonce,_=self.manager.request(self.master,SECOND,public_der(self.key),["quotes"])
        self.manager.abort(self.master,SECOND)
        with self.assertRaises(SessionDenied):
            self.manager.complete(self.master,self.signed(SECOND,nonce,self.key))

    def test_three_device_limit_and_bad_public_key_rejected(self):
        for device in (SECOND,THIRD):
            nonce,_=self.manager.request(self.master,device,public_der(self.key),["quotes"])
            self.manager.complete(self.master,self.signed(device,nonce,self.key))
        with self.assertRaises(SessionDenied):
            self.manager.request(self.master,FOURTH,public_der(self.key),["quotes"])
        for key in (b"invalid",b""):
            with self.assertRaises(SessionDenied):
                self.manager.request(self.master,SECOND,key,["quotes"])

    def test_non_master_cannot_issue_or_change_enrollment(self):
        self.registry.assign(MASTER,SECOND,{"quotes"})
        self.sessions._verify_proof=lambda proof: VerifiedDevice(SECOND) if proof=="second" else VerifiedDevice(MASTER)
        second=self.sessions.issue("second")
        with self.assertRaises(Exception):
            self.manager.request(second,THIRD,public_der(self.key),["quotes"])
        with self.assertRaises(Exception):
            self.manager.abort(second,THIRD)

if __name__=="__main__":
    unittest.main()
