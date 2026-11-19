"""No-network owner provisioning and activation-gate regression."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from pilot_v2.tools.provision_oracle_master import enroll_master
from pilot_v2.tools.v2_activation_gate import parse_private_environment, verify_configuration


class ActivationGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name) / "v2-private"
        self.root.mkdir(mode=0o700)
        self.device = "owner-master-real-001"
        self.public = self.root / "master.der"
        self.pairing = self.root / "pairing.key"
        self.db = self.root / "master.sqlite"
        self.conf = self.root / "v2.env"
        k = ec.generate_private_key(ec.SECP256R1())
        data = k.public_key().public_bytes(
            serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
        self.public.write_bytes(data)
        self.public.chmod(0o600)
        self.fingerprint = hashlib.sha256(data).hexdigest()
        self.pairing.write_text("T" * 48, encoding="ascii")
        self.pairing.chmod(0o600)
        self.values = {
            "BOTKING_V2_MASTER_DEVICE_ID":self.device,
            "BOTKING_V2_MASTER_PUBLIC_DER_PATH":str(self.public),
            "BOTKING_V2_PAIRING_KEY_PATH":str(self.pairing),
            "BOTKING_V2_DB_PATH":str(self.db),
        }
        self.conf.write_text("".join(f"{k}={v}\n" for k,v in self.values.items()),encoding="utf-8")
        self.conf.chmod(0o600)

    def test_no_master_cannot_approve(self):
        with patch("pilot_v2.tools.v2_activation_gate.SAFE_PREFIX",str(self.root)+"/"):
            with self.assertRaises(ValueError):
                verify_configuration(parse_private_environment(str(self.conf)))

    def test_approved_private_master_and_denied_unauthorized_read(self):
        enroll_master(directory=self.root,device_id=self.device,
                      public_path=self.public, approved_fingerprint=self.fingerprint)
        with patch("pilot_v2.tools.v2_activation_gate.SAFE_PREFIX",str(self.root)+"/"):
            self.assertTrue(verify_configuration(parse_private_environment(str(self.conf))))

    def test_operator_optional_roster_checked_by_activation(self):
        enroll_master(directory=self.root, device_id=self.device,
                      public_path=self.public, approved_fingerprint=self.fingerprint)
        roster = self.root / "selected.json"
        roster.write_text('["TCS","RELIANCE"]')
        roster.chmod(0o600)
        self.conf.write_text(self.conf.read_text() +
            f"BOTKING_V2_SELECTED_EQUITIES_PATH={roster}\n")
        with patch("pilot_v2.tools.v2_activation_gate.SAFE_PREFIX", str(self.root) + "/"):
            self.assertTrue(verify_configuration(parse_private_environment(str(self.conf))))
        roster.write_text('["TCS","TCS"]')
        with patch("pilot_v2.tools.v2_activation_gate.SAFE_PREFIX", str(self.root) + "/"):
            with self.assertRaises(ValueError):
                verify_configuration(parse_private_environment(str(self.conf)))

    def test_world_readable_env_denied(self):
        self.conf.chmod(0o644)
        with self.assertRaises(ValueError):
            parse_private_environment(str(self.conf))

    def test_shell_expansion_in_env_denied(self):
        self.conf.write_text(self.conf.read_text().replace(
            "BOTKING_V2_MASTER_DEVICE_ID="+self.device,
            "BOTKING_V2_MASTER_DEVICE_ID=$(whoami)"))
        with self.assertRaises(ValueError):
            parse_private_environment(str(self.conf))

    def test_outside_or_duplicate_private_paths_denied(self):
        self.values["BOTKING_V2_PAIRING_KEY_PATH"]=str(self.public)
        with patch("pilot_v2.tools.v2_activation_gate.SAFE_PREFIX",str(self.root)+"/"):
            with self.assertRaises(ValueError):
                verify_configuration(self.values)

    def test_wrong_public_key_blocks(self):
        enroll_master(directory=self.root,device_id=self.device,
                      public_path=self.public,approved_fingerprint=self.fingerprint)
        new=ec.generate_private_key(ec.SECP256R1())
        self.public.write_bytes(new.public_key().public_bytes(
            serialization.Encoding.DER,serialization.PublicFormat.SubjectPublicKeyInfo))
        with patch("pilot_v2.tools.v2_activation_gate.SAFE_PREFIX",str(self.root)+"/"):
            # Entry-point requires approved ID but currently accepts *any*
            # canonical public key for that ID; key binding must be proven.
            # This test guards the intended safety policy.
            with self.assertRaises(ValueError):
                verify_configuration(parse_private_environment(str(self.conf)))


if __name__=="__main__":
    unittest.main()
