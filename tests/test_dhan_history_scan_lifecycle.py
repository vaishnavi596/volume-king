"""Batch 3 source guard: Dhan's 51-symbol history scan must remain paced and resumable."""
from pathlib import Path
import unittest

MAIN = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
START = MAIN.index("    async def refresh_market():")
END = MAIN.find("\n    async def ", START + 10)
SCAN = MAIN[START:END if END != -1 else None]


class DhanHistoryScanSafetyTests(unittest.TestCase):
    def test_dhan_history_tail_is_serial_and_paced(self):
        self.assertIn("for sym in symbols[1:]:", SCAN)
        self.assertIn("results.append(await load_one(sym))", SCAN)
        self.assertIn("if not cache_ready:", SCAN)
        self.assertIn("await asyncio.sleep(1.5)", SCAN)
        self.assertIn("dhan_feed.cooldown_remaining(\"/dhan/intraday\")", SCAN)
        self.assertLess(SCAN.index("for sym in symbols[1:]:"), SCAN.index("results.append(await load_one(sym))"))

    def test_background_interrupt_keeps_generation_pending_and_ranking(self):
        self.assertIn("if lifecycle_background[0]:", SCAN)
        self.assertIn("background_interrupted=True", SCAN)
        self.assertIn("last_scanned_generation=None", SCAN)
        self.assertIn("last ranking retained", SCAN)
        self.assertIn("if prefs.get(\"source\")==\"Dhan\" and (lifecycle_background[0] or background_interrupted):", SCAN)

    def test_429_does_not_count_unrequested_symbols_as_failed(self):
        self.assertIn("symbols not attempted", SCAN)
        self.assertIn("last_scanned_generation=None", SCAN)
        self.assertIn("Dhan historical scan paused: HTTP 429 / cooldown", SCAN)


if __name__ == "__main__":
    unittest.main()
