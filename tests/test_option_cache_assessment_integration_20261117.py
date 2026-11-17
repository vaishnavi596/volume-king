"""Offline integration: validated cached Dhan metrics -> read-only assessment.

No broker calls, network, credentials, trading or production service needed.
"""
from datetime import date
from pathlib import Path
import importlib.util
import unittest

ROOT = Path(__file__).resolve().parents[1]


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "backend" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cache_module = load("bk_option_evidence_cache_test", "option_evidence_cache.py")
adapter = load("bk_assessment_filter_adapter_test", "assessment_filter_adapter.py")


class OptionCacheToAssessmentTests(unittest.TestCase):
    def setUp(self):
        self.now = 1000
        self.cache = cache_module.OptionEvidenceCache(
            ttl_seconds=120, max_entries=4,
            clock=lambda: self.now,
            today=lambda: date(2026, 11, 17),
        )
        self.metrics = {
            "pcr": 0.83,
            "max_pain": 25100.0,
            "freshness": "unverified",
            "signal_eligible": False,
        }

    def test_cached_metrics_are_informational_never_directional_scores(self):
        self.assertTrue(self.cache.put("NIFTY", "2026-11-26", self.metrics))
        self.metrics["pcr"] = 99.0  # Caller mutation must not change the cache.
        evidence = self.cache.latest("NIFTY")
        self.assertEqual(evidence["pcr"], 0.83)
        report = adapter.read_only_assessment("NIFTY", evidence)
        slots = {row["id"]: row for row in report["assessment_filters"]}
        self.assertEqual(slots["pcr"]["status"], "available")
        self.assertEqual(slots["pcr"]["verification"], "unverified")
        self.assertEqual(slots["max_pain"]["status"], "available")
        self.assertEqual(slots["oi_support"]["status"], "unavailable")
        self.assertEqual(slots["oi_resistance"]["status"], "unavailable")
        self.assertEqual(slots["candle_trend"]["status"], "unavailable")
        self.assertIsNone(report["bullish_score"])
        self.assertIsNone(report["bearish_score"])
        self.assertFalse(report["signal_eligible"])
        self.assertFalse(report["live_orders_enabled"])
        self.assertTrue(all(
            row["status"] == "unavailable"
            for row in report["factors"].values()
        ))

    def test_expired_or_wrong_symbol_has_no_evidence(self):
        self.assertTrue(self.cache.put("NIFTY", "2026-11-26", self.metrics))
        self.assertIsNone(self.cache.latest("SENSEX"))
        self.now += 120
        self.assertIsNone(self.cache.latest("NIFTY"))
        report = adapter.read_only_assessment("NIFTY", self.cache.latest("NIFTY"))
        self.assertEqual(report["collection_status"], "not_configured")
        self.assertFalse(report["signal_eligible"])

    def test_old_expiry_or_unverified_signal_is_rejected(self):
        self.assertFalse(self.cache.put("NIFTY", "2026-11-16", self.metrics))
        bad = dict(self.metrics, signal_eligible=True)
        self.assertFalse(self.cache.put("NIFTY", "2026-11-26", bad))
        bad = dict(self.metrics, freshness="fresh")
        self.assertFalse(self.cache.put("NIFTY", "2026-11-26", bad))
        self.assertIsNone(self.cache.latest("NIFTY"))


if __name__ == "__main__":
    unittest.main()
