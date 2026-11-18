"""Offline synthetic tests for the SHA-pinned, non-executing T09 audit."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from scripts.audit_oracle_t09_observation_provenance_readonly import audit

SOURCE = """
def persist_candle_cache(entry):
    entry["observed_at"] = 123
    return entry

def cached_candles(entry):
    data = {"bars": entry.get("bars"), "observed_at": entry.get("observed_at"),
            "freshness": "historical_unverified", "signal_eligible": False}
    return data

def dhan_intraday(body):
    return {"bars": body, "freshness": "historical_unverified",
            "interval": "3m"}
"""
CANDIDATE = SOURCE + """
def _bk_publish_completed_intraday(response):
    rows = response.get("bars")
    return {"bars": rows}
"""


class T09ObservationProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "server.py"
        self.candidate = Path(self.temp.name) / "candidate.py"
        self.root.write_text(SOURCE, encoding="utf-8")
        self.candidate.write_text(CANDIDATE, encoding="utf-8")

    def run_audit(self, source_hash=None):
        return audit(
            self.root, self.candidate,
            source_hash or hashlib.sha256(SOURCE.encode()).hexdigest(),
            hashlib.sha256(CANDIDATE.encode()).hexdigest())

    def test_synthetic_lineage_is_bounded_and_never_executed(self):
        result = self.run_audit()
        self.assertEqual(result["status"], "SOURCE_ONLY_PASS")
        self.assertFalse(result["runtime_verified"])
        self.assertFalse(result["deployment_approved"])
        self.assertEqual(result["dhan_requests"], 0)
        records = result["function_field_operations"]
        self.assertTrue(any(x["operation"] == "subscript_assignment"
                            and x["field"] == "observed_at"
                            for x in records["persist_candle_cache"]))
        self.assertTrue(any(x["field"] == "observed_at"
                            for x in records["cached_candles"]))
        self.assertFalse(any(x["field"] == "observed_at"
                             for x in records["dhan_intraday"]))
        self.assertTrue(any(x["field"] == "bars"
                            for x in records["staged_intraday_helper"]))

    def test_sha_drift_rejected(self):
        with self.assertRaisesRegex(ValueError, "SERVER_SHA_MISMATCH"):
            self.run_audit(source_hash="0" * 64)

    def test_missing_candidate_rejected(self):
        self.candidate.unlink()
        with self.assertRaisesRegex(ValueError, "CANDIDATE_MISSING_OR_SYMLINK"):
            self.run_audit()


if __name__ == "__main__":
    unittest.main()
