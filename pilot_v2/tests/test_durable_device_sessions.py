"""SQLite V2 multi-worker session tests with synthetic verified identities."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from pilot_v2.device_sessions import VerifiedDevice, SessionDenied
from pilot_v2.durable_device_sessions import DurableDeviceSessions

M="master_device_000001"
A="second_device_00001"
B="third_device_000001"
C="fourth_device_000001"

class DurableDeviceSessionTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        path=Path(tmp.name)/"device-sessions.sqlite3"
        self.now=[1000.]
        self.one=DurableDeviceSessions(path,clock=lambda:self.now[0],ttl=60)
        self.two=DurableDeviceSessions(path,clock=lambda:self.now[0],ttl=60)
        self.one.bootstrap(M,authorize_bootstrap=lambda d:d==M)
        self.master=self.one.issue_verified(VerifiedDevice(M))

    def test_restart_shared_master_and_two_delegated_permissions(self):
        self.two.master_grant(self.master,A,["quotes"])
        self.one.master_grant(self.master,B,["indices","candles"])
        a=self.two.issue_verified(VerifiedDevice(A))
        b=self.one.issue_verified(VerifiedDevice(B))
        self.assertEqual(self.one.authorize(a,"quotes"),A)
        self.assertEqual(self.two.authorize(b,"indices"),B)
        with self.assertRaises(SessionDenied):
            self.one.authorize(a,"indices")
        with self.assertRaises(SessionDenied):
            self.two.master_grant(a,C,["quotes"])
        with self.assertRaises(SessionDenied):
            self.two.master_grant(self.master,C,["quotes"])

    def test_disable_revoke_and_new_permissions_drop_old_tokens(self):
        self.one.master_grant(self.master,A,["quotes"])
        previous=self.two.issue_verified(VerifiedDevice(A))
        self.two.master_grant(self.master,A,["indices"])
        with self.assertRaises(SessionDenied):
            self.one.authorize(previous,"quotes")
        fresh=self.one.issue_verified(VerifiedDevice(A))
        self.assertEqual(self.two.authorize(fresh,"indices"),A)
        self.one.master_grant(self.master,A,["indices"],enabled=False)
        with self.assertRaises(SessionDenied):
            self.two.authorize(fresh,"indices")
        with self.assertRaises(SessionDenied):
            self.two.issue_verified(VerifiedDevice(A))
        self.one.revoke(self.master,A)
        with self.assertRaises(SessionDenied):
            self.two.issue_verified(VerifiedDevice(A))

    def test_expiry_rotation_logout_and_malformed_claim(self):
        with self.assertRaises(SessionDenied):
            self.one.issue_verified({"device_id":M,"master":True})
        before=self.two.issue_verified(VerifiedDevice(M))
        with self.assertRaises(SessionDenied):
            self.one.authorize(self.master,"quotes")
        self.two.logout(before)
        with self.assertRaises(SessionDenied):
            self.one.authorize(before,"quotes")
        after=self.two.issue_verified(VerifiedDevice(M))
        self.now[0]+=60
        with self.assertRaises(SessionDenied):
            self.one.authorize(after,"quotes")

    def test_unauthorized_bootstrap_and_master_protection(self):
        with self.assertRaises(SessionDenied):
            self.two.bootstrap(A,authorize_bootstrap=lambda _:True)
        with self.assertRaises(SessionDenied):
            self.two.master_grant(self.master,M,["quotes"])
        with self.assertRaises(SessionDenied):
            self.two.revoke(self.master,M)
        with self.assertRaises(SessionDenied):
            self.two.master_grant(self.master,A,["credentials"])

    def test_only_digests_are_persisted(self):
        raw=self.master
        with sqlite3.connect(self.one._path) as db:
            row=db.execute("SELECT digest FROM sessions WHERE device=?",(M,)).fetchone()
        self.assertNotEqual(row[0],raw)
        self.assertEqual(len(row[0]),64)

if __name__=="__main__":
    unittest.main()
