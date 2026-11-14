"""Guard Dashboard Super Five against bypassing Scanner's verified ranking gate."""
from pathlib import Path
import unittest


MAIN = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")


class DashboardRankingParityTests(unittest.TestCase):
    def test_dashboard_uses_shared_verified_ranker(self):
        start = MAIN.index("    def publish_partial_ranking(results):")
        end = MAIN.index("    async def super_five_minute_refresh():", start)
        section = MAIN[start:end]
        self.assertIn("verified=rank_candidates(", section)
        self.assertIn("chosen=list(verified)", section)
        self.assertIn('bias="WAIT",score=0,historical=True', section)
        self.assertLess(section.index("chosen=list(verified)"),
                        section.index("for row in available:", section.index("chosen=list(verified)")))

    def test_ranking_does_not_promote_historical_to_live(self):
        start = MAIN.index("    def publish_partial_ranking(results):")
        end = MAIN.index("    async def super_five_minute_refresh():", start)
        section = MAIN[start:end]
        self.assertIn("Historical/unverified; no live signal", section)
        self.assertIn('max_results=5', section)


if __name__ == "__main__":
    unittest.main()
