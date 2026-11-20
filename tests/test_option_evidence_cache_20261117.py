"""Offline tests for bounded, copy-isolated option evidence handoff."""
import unittest
from datetime import date
from backend.option_evidence_cache import OptionEvidenceCache


class OptionEvidenceCacheTests(unittest.TestCase):
    def test_symbol_isolation_expiry_and_no_mutation(self):
        clock = [100.0]
        cache = OptionEvidenceCache(ttl_seconds=10, clock=lambda: clock[0],
                                    today=lambda: date(2026, 11, 19))
        metrics = {"pcr": 0.8, "freshness": "unverified", "signal_eligible": False}
        self.assertTrue(cache.put("NIFTY", "2026-11-19", metrics))
        metrics["pcr"] = 99
        self.assertIsNone(cache.latest("BANKNIFTY"))
        self.assertEqual(cache.latest("NIFTY")["pcr"], 0.8)
        cache.latest("NIFTY")["pcr"] = 5
        self.assertEqual(cache.latest("NIFTY")["pcr"], 0.8)
        clock[0] += 10
        self.assertIsNone(cache.latest("NIFTY"))

    def test_expiry_date_rollover_invalidates_even_inside_ttl(self):
        today = [date(2026, 11, 19)]
        cache = OptionEvidenceCache(ttl_seconds=120, today=lambda: today[0])
        good = {"signal_eligible": False, "freshness": "unverified", "pcr": 0.8}
        self.assertFalse(cache.put("NIFTY", "2026-11-18", good))
        self.assertFalse(cache.put("NIFTY", "invalid-date", good))
        self.assertTrue(cache.put("NIFTY", "2026-11-19", good))
        self.assertEqual(cache.latest("NIFTY")["pcr"], 0.8)
        today[0] = date(2026, 11, 20)
        self.assertIsNone(cache.latest("NIFTY"))

    def test_explicit_foreign_source_never_enters_dhan_cache(self):
        cache = OptionEvidenceCache(today=lambda: date(2026, 11, 18))
        base = {"pcr": 0.91, "freshness": "unverified",
                "signal_eligible": False}
        for foreign in ("yahoo", "angel", "", None, True):
            with self.subTest(source=foreign):
                self.assertFalse(cache.put(
                    "NIFTY", "2026-11-19", {**base, "source": foreign}))
                self.assertIsNone(cache.latest("NIFTY"))
        self.assertTrue(cache.put(
            "NIFTY", "2026-11-19", {**base, "source": "dhan"}))
        self.assertEqual(cache.latest("NIFTY")["source"], "dhan")

    def test_reject_unverified_eligibility_and_bound_capacity(self):
        cache = OptionEvidenceCache(max_entries=1,
                                    today=lambda: date(2026, 11, 19))
        self.assertFalse(cache.put("A", "2026-11-19", {"signal_eligible": True,
                                                       "freshness": "unverified"}))
        self.assertFalse(cache.put("A", "2026-11-19", {"signal_eligible": False,
                                                       "freshness": "live"}))
        good = {"signal_eligible": False, "freshness": "unverified"}
        self.assertTrue(cache.put("A", "2026-11-19", good))
        self.assertTrue(cache.put("B", "2026-11-19", good))
        self.assertIsNone(cache.latest("A"))
        self.assertEqual(cache.latest("B"), {**good, "expiry": "2026-11-19"})
        self.assertEqual(cache.latest("B", "2026-11-19")["expiry"], "2026-11-19")
        self.assertIsNone(cache.latest("B", "2026-11-26"))
        self.assertEqual(good, {"signal_eligible": False, "freshness": "unverified"})


if __name__ == "__main__":
    unittest.main()
