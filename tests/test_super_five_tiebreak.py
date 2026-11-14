"""Super Five ranking must prefer confirmations and freshness over alphabetic symbol order."""
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from scanner_engine import rank_candidates

def candidate(timestamp, extra=False):
    votes = [{"name":"Supertrend","vote":1},{"name":"EMA 9/21","vote":1},
             {"name":"MACD","vote":1},{"name":"RSI 14","vote":0}]
    if extra:
        votes[-1]["vote"] = 1
    return {"bias":"BULLISH","score":100,"timestamp":timestamp,"count":40,
            "votes":votes,"source":"Test","freshness":"verified_live","live_verified":True}

class SuperFiveTieBreak(unittest.TestCase):
    def test_newer_verified_signal_wins_equal_votes(self):
        now=int(datetime.now(timezone.utc).timestamp())
        ranked=rank_candidates({"AAA":candidate(now-120),
                                "ZZZ":candidate(now-10)})
        self.assertEqual([r["symbol"] for r in ranked],["ZZZ","AAA"])

    def test_more_confirmations_win_equal_score(self):
        now=int(datetime.now(timezone.utc).timestamp())
        ranked=rank_candidates({"AAA":candidate(now-10),
                                "ZZZ":candidate(now-120,extra=True)})
        self.assertEqual([r["symbol"] for r in ranked],["ZZZ","AAA"])

    def test_claimed_score_is_capped_by_confirmed_votes(self):
        now=int(datetime.now(timezone.utc).timestamp())
        item=candidate(now)
        item["votes"].append({"name":"VWAP","vote":-1})
        item["score"]=76
        ranked=rank_candidates({"TEST":item})
        self.assertEqual(len(ranked),1)
        self.assertEqual(ranked[0]["score"],75)

    def test_understated_score_is_recomputed_from_votes(self):
        now=int(datetime.now(timezone.utc).timestamp())
        item=candidate(now)
        item["score"]=1
        ranked=rank_candidates({"TEST":item})
        self.assertEqual(len(ranked),1)
        self.assertEqual(ranked[0]["score"],100)

    def test_unverified_dhan_cannot_enter_rankings(self):
        now=int(datetime.now(timezone.utc).timestamp())
        item=candidate(now)
        item.update(source="Dhan",freshness="unverified",live_verified=False)
        self.assertEqual(rank_candidates({"NIFTY":item}),[])

if __name__=="__main__":
    unittest.main()
