"""Regression for actual budget and independent scanner history counters."""
import pathlib
import unittest
SRC=(pathlib.Path(__file__).resolve().parents[1]/"src"/"main.py").read_text()

class DoctorBudgetProgressTests(unittest.TestCase):
    def test_budget_matches_scheduler(self):
        self.assertIn("if len(warm_times)>=12:",SRC)
        self.assertNotIn("if len(warm_times)>=3:",SRC)
        self.assertIn('"warmup_max_uncached_requests_per_180s":12',SRC)
    def test_history_progress_is_separate_from_ranking(self):
        self.assertIn("history_checked=0,history_total=len(symbols)",SRC)
        self.assertEqual(SRC.count("scan_progress.update(history_checked=market_completed[0]"),2)
        self.assertIn("history_valid=market_completed[0]-history_failed[0]",SRC)
        self.assertIn('"history_checked","history_total","history_valid","history_failed","history_cached"',SRC)
