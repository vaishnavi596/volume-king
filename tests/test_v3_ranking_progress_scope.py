"""FT2: ranker 5m progress must not masquerade as selected 1m scanner failures."""
from pathlib import Path
import unittest


class RankingProgressScopeTests(unittest.TestCase):
    def test_master_doctor_exposes_separate_ranking_timeframe(self):
        main = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text()
        self.assertIn('scan_progress={"checked":0,"total":51,"valid":0,"failed":0,"cached":0,"state":"Waiting","timeframe":"5m"}', main)
        self.assertIn('scan_progress.update(checked=0,total=len(ranking_symbols),valid=0,failed=0,cached=0,timeframe="5m"', main)
        self.assertIn('"No valid 5m ranking candles; 1m/3m may still be available; last saved results retained"', main)
        self.assertGreaterEqual(main.count('("checked","total","valid","failed","cached","state","timeframe")'), 2)
        self.assertNotIn('scan_progress["state"]="Complete" if scan_progress["valid"]', main)


if __name__ == "__main__":
    unittest.main()
