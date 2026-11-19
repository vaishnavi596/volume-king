"""Pure standard-library DER checks; no platform Keystore or real login."""
import sys
import unittest
from pathlib import Path
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import ec, utils

SRC = Path(__file__).resolve().parents[1] / "android_app" / "src"
sys.path.insert(0, str(SRC))
from app_p256_signature import P256_ORDER, is_canonical_p256_der_signature


class P256SignatureFormatTests(unittest.TestCase):
    def test_real_p256_signature_is_valid(self):
        key = ec.generate_private_key(ec.SECP256R1())
        sig = key.sign(b"BOT-KING-V2-DEVICE-LOGIN\x00sample", ec.ECDSA(hashes.SHA256()))
        self.assertTrue(is_canonical_p256_der_signature(sig))

    def test_malformed_and_out_of_range_signatures_rejected(self):
        bad = (None, True, "bytes", b"", b"sigbytes", bytes(300),
               b"\x30\x06\x02\x01\x00\x02\x01\x01",  # zero r
               b"\x30\x06\x02\x01\x01\x02\x01\x00",  # zero s
               b"\x30\x06\x02\x01\xff\x02\x01\x01",  # negative r
               b"\x30\x07\x02\x02\x00\x01\x02\x01\x01",  # padded r
               b"\x30\x06\x02\x01\x01\x02\x01\x01\x00",  # trailer
               utils.encode_dss_signature(1, P256_ORDER),
               utils.encode_dss_signature(P256_ORDER, 1))
        for sample in bad:
            with self.subTest(sample=repr(sample)[:30]):
                self.assertFalse(is_canonical_p256_der_signature(sample))
        self.assertTrue(is_canonical_p256_der_signature(utils.encode_dss_signature(1, 1)))


if __name__ == "__main__":
    unittest.main()
