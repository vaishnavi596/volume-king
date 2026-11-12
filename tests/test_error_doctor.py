import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from error_doctor import diagnose

class ErrorDoctorTests(unittest.TestCase):
    def test_rate_limit(self):
        self.assertEqual(diagnose("Dhan API rate limited (HTTP 429)")[0], "BK-DHAN-429")
    def test_cooldown(self):
        self.assertEqual(diagnose("Dhan API cooldown active")[0], "BK-DHAN-429")
    def test_auth(self):
        self.assertEqual(diagnose("token expired")[0], "BK-AUTH-401")
    def test_unknown(self):
        self.assertEqual(diagnose("unrecognized problem")[0], "BK-UNKNOWN")
    def test_no_secrets_in_report(self):
        self.assertNotIn("secret", " ".join(diagnose("secret=abc123")))

if __name__ == "__main__":
    unittest.main()
