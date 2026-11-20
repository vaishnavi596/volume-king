"""B2 isolated Oracle clone login contract: all checks offline, no broker calls."""
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.clone_v2_gateway import create_app, private_ssk


class CloneOracleAuthTests(unittest.TestCase):
    def setUp(self):
        self.key = b"k" * 40
        self.http = TestClient(create_app(key_bytes=self.key))

    def test_no_key_fails_closed(self):
        res = self.http.get("/clone-v2/status")
        self.assertEqual(res.status_code, 403)

    def test_wrong_key_fails_closed(self):
        res = self.http.get("/clone-v2/status", headers={"X-BotKing-Key": "q" * 40})
        self.assertEqual(res.status_code, 403)

    def test_approved_key_exact_contract(self):
        res = self.http.get("/clone-v2/status", headers={"X-BotKing-Key": self.key.decode()})
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.headers["cache-control"], "no-store")
        self.assertEqual(res.json(), {
            "protocol": "botking-clone-v2",
            "authenticated": True,
            "read_only": True,
            "live_orders_enabled": False,
            "pipeline": "dhan-oracle-clone",
            "status": "ready",
        })

    def test_no_legacy_v1_or_pilot_v2_routes(self):
        for uri in ("/dhan/status", "/v2-pilot/auth/challenge", "/clone-v2/quotes",
                    "/clone-v2/orders"):
            self.assertEqual(self.http.get(uri).status_code, 404)

    def test_health_not_market_data_proof(self):
        res = self.http.get("/clone-v2/health")
        self.assertEqual(res.status_code, 200)
        self.assertFalse(res.json()["live_data_verified"])

    def test_key_provisioning_not_auto_bootstrapped(self):
        with patch.dict(os.environ, {"BOTKING_CLONE_V2_SSK_FILE": ""}):
            with self.assertRaises(ValueError):
                create_app()

    def test_insecure_private_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "key"
            path.write_bytes(self.key)
            path.chmod(0o644)
            with self.assertRaises(ValueError):
                private_ssk(str(path))


if __name__ == "__main__":
    unittest.main()
