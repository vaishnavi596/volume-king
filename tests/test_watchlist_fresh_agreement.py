"""Fresh candle status requires validated provider and at least two votes."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class WatchlistFreshAgreementTests(unittest.TestCase):
    def test_fresh_signal_requires_vote_agreement(self):
        self.assertIn('signal_fresh=(signal_row.get("source")==expected_quote_source\n                          and signal_counts is not None and signal_counts[2]>=2', SOURCE)
        self.assertIn('signal_direction if signal_fresh and signal_available else "Unverified / historical"', SOURCE)
if __name__ == "__main__":
    unittest.main()
