"""Malformed signal rows must be treated as unavailable, not crash the UI."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class SignalRowTypeTests(unittest.TestCase):
    def test_reject_non_dict_signal_rows(self):
        self.assertIn('if not isinstance(row,dict):return None\n        votes=row.get("votes") or []', SOURCE)
        self.assertIn('if not isinstance(votes,(list,tuple)):return None', SOURCE)

if __name__ == "__main__":
    unittest.main()
