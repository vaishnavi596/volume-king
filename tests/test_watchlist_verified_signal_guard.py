"""Watchlist must not label unverified Dhan candle votes as live."""
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")


class WatchlistFreshnessGuardTests(unittest.TestCase):
    def test_dhan_signal_requires_verified_freshness(self):
        start=SOURCE.index("            signal_fresh=(signal_row.get(")
        end=SOURCE.index("            signal_available=",start)
        block=SOURCE[start:end]
        self.assertIn('signal_row.get("live_verified") is True',block)
        self.assertIn('signal_row.get("freshness") in ("verified_live","live_verified")',block)
        self.assertIn('not signal_row.get("historical")',block)


if __name__=="__main__":
    unittest.main()
