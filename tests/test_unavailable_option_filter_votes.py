"""Batch 3: unavailable option filters must not inflate scanner confidence."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scanner_engine import analyze, OPTION_FILTERS


class UnavailableOptionFilterTests(unittest.TestCase):
    @staticmethod
    def bars():
        now = int(datetime.now(timezone.utc).timestamp())
        end = now - 120
        end -= end % 300
        start = end - 39 * 300
        return [[start + i * 300, 100 + i * .2, 101 + i * .2,
                 99 + i * .2, 100 + i * .2, 1000] for i in range(40)]

    def test_unavailable_option_filters_do_not_vote_or_inflate_score(self):
        result = analyze(self.bars(), ["EMA 9/21", "RSI 14", *OPTION_FILTERS], "5m")
        options = [vote for vote in result["votes"] if vote["name"] in OPTION_FILTERS]
        self.assertEqual(len(options), len(OPTION_FILTERS))
        self.assertTrue(all(v["vote"] is None and "UNAVAILABLE" in v["detail"] for v in options))
        directional = [v for v in result["votes"] if v["vote"] in (-1, 1)]
        self.assertLessEqual(len(directional), 2)
        self.assertEqual(result["bias"], "WAIT")
        self.assertEqual(result["score"], 0)
        self.assertIn("NOT success probability", result["reason"])


if __name__ == "__main__":
    unittest.main()
