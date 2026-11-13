"""Paused Dhan scans must not count unattempted symbols as failures."""
from pathlib import Path
import unittest

SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class DhanPauseCountsTests(unittest.TestCase):
    def test_background_pause_exposes_unattempted_count(self):
        self.assertEqual(SOURCE.count('Dhan historical scan paused in background • "+str(max(0,len(symbols)-market_completed[0]))+" symbols not attempted'), 2)
        self.assertIn('background_interrupted=True', SOURCE)

    def test_cooldown_pause_exposes_unattempted_count(self):
        self.assertIn('Dhan historical scan paused after HTTP 429 • "+str(max(0,len(symbols)-market_completed[0]))+" symbols not attempted', SOURCE)
        self.assertIn('waiting for provider cooldown', SOURCE)

if __name__ == "__main__":
    unittest.main()
