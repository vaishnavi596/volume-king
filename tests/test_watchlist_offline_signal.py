"""Disconnected Dhan state must not display candle signals as live."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class WatchlistOfflineSignalTests(unittest.TestCase):
    def test_fresh_signal_requires_connected_provider(self):
        self.assertIn('not signal_row.get("historical") and regular_hours() and not dhan_offline()', SOURCE)
        self.assertIn('signal_direction if signal_fresh and signal_available else "Unverified / historical"', SOURCE)
if __name__ == "__main__":
    unittest.main()
