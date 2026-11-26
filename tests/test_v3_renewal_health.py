import os
import json
import tempfile
import unittest
from pathlib import Path
from datetime import datetime, timezone
from backend.dhan_renewal_health import renewal_health_report

class RenewalHealthTests(unittest.TestCase):
    def test_private_metadata_only_and_no_execution(self):
        now=datetime(2026,11,26,12,tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/"metadata.json"
            p.write_text(json.dumps({"source":"dhan_web","expires_at":"2026-11-26T13:00:00+00:00"}))
            os.chmod(p,0o600)
            before=p.read_bytes()
            report=renewal_health_report(p,now=now)
            self.assertEqual(report["state"],"RENEWAL_DUE")
            self.assertTrue(report["metadata_verified"])
            self.assertFalse(report["renewal_observed"])
            self.assertFalse(report["timer_verified"])
            self.assertEqual(report["provider_requests"],0)
            self.assertEqual(p.read_bytes(),before)
            os.chmod(p,0o644)
            self.assertEqual(renewal_health_report(p,now=now)["state"],"UNVERIFIED")
        self.assertEqual(renewal_health_report(None)["state"],"UNVERIFIED")
    def test_wiring(self):
        root=Path(__file__).resolve().parents[1]
        self.assertIn('@app.get("/clone-v2/renewal-health")',(root/"backend/clone_v2_gateway.py").read_text())
        self.assertIn('data["renewal_health"]=renewal_doctor_snapshot()',(root/"src/main.py").read_text())
