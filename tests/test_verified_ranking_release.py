"""Functional release guards for shared Dashboard/Scanner verified ranking."""
from datetime import datetime, timezone
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scanner_engine import rank_candidates


def candidate(**changes):
    result = {
        "source": "Dhan", "bias": "BULLISH", "score": 100,
        "count": 40, "timestamp": datetime.now(timezone.utc).timestamp() - 60,
        "freshness": "verified_live", "live_verified": True,
        "historical": False, "cached": False,
        "votes": [
            {"name": "Supertrend", "vote": 1},
            {"name": "EMA 9/21", "vote": 1},
            {"name": "RSI 14", "vote": 1},
        ],
    }
    result.update(changes)
    return result


class VerifiedRankingReleaseTests(unittest.TestCase):
    def test_verified_candidate_is_ranked(self):
        self.assertEqual([r["symbol"] for r in rank_candidates({"RELIANCE": candidate()})],
                         ["RELIANCE"])

    def test_unverified_and_historical_are_not_actionable(self):
        cases = [
            {"freshness": "historical_unverified"},
            {"freshness": "unverified"},
            {"freshness": "stale"},
            {"live_verified": False},
            {"historical": True},
            {"cached": True},
            {"source": "Dhan", "freshness": "verified_live", "live_verified": None},
        ]
        for change in cases:
            with self.subTest(change=change):
                self.assertEqual(rank_candidates({"RELIANCE": candidate(**change)}), [])

    def test_duplicate_indicator_cannot_inflate_ranking(self):
        duplicate = [{"name": "Supertrend", "vote": 1}] * 3
        self.assertEqual(rank_candidates({"RELIANCE": candidate(votes=duplicate)}), [])

    def test_unavailable_option_votes_cannot_inflate_top_five(self):
        votes = [
            {"name": "Supertrend", "vote": 1},
            {"name": "EMA 9/21", "vote": 1},
            {"name": "OI Support", "vote": None},
            {"name": "OI Resistance", "vote": None},
            {"name": "OI Profile", "vote": None},
            {"name": "Max Pain", "vote": None},
        ]
        self.assertEqual(rank_candidates({"RELIANCE": candidate(votes=votes, score=100)}), [])

    def test_only_three_independent_confirmations_qualify(self):
        votes = [
            {"name": "Supertrend", "vote": 1},
            {"name": "EMA 9/21", "vote": 1},
            {"name": "RSI 14", "vote": 1},
            {"name": "OI Support", "vote": None},
        ]
        ranked = rank_candidates({"RELIANCE": candidate(votes=votes)})
        self.assertEqual(len(ranked), 1)
        self.assertEqual(ranked[0]["score"], 100)

    def test_verified_equal_scores_have_deterministic_symbol_order(self):
        ranked = rank_candidates({"TCS": candidate(), "RELIANCE": candidate()})
        self.assertEqual([r["symbol"] for r in ranked], ["RELIANCE", "TCS"])


if __name__ == "__main__":
    unittest.main()
