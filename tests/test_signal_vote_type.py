"""Boolean vote values must not masquerade as bullish directional votes."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class SignalVoteTypeTests(unittest.TestCase):
    def test_boolean_vote_is_not_bullish(self):
        self.assertIn('type(v.get("vote")) is int and v["vote"]==1', SOURCE)
        self.assertIn('type(v.get("vote")) is int and v["vote"]==-1', SOURCE)
        self.assertIn('return (round(100*bulls/total),round(100*bears/total),total) if total else None', SOURCE)

if __name__ == "__main__":
    unittest.main()
