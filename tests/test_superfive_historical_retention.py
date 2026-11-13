"""Super Five must retain only safe, same-provider historical candidates."""
from pathlib import Path
import unittest

SOURCE=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")

class SuperFiveHistoricalRetentionTests(unittest.TestCase):
    def setUp(self):
        self.body=SOURCE.split('    def publish_partial_ranking(results):',1)[1].split('    async def super_five_minute_refresh():',1)[0]

    def test_retention_is_dhan_only(self):
        self.assertIn('row.get("source")=="Dhan"',self.body)
        self.assertIn('row.get("source")!="Dhan"',self.body)

    def test_retained_rows_cannot_be_actionable(self):
        self.assertIn('dict(row,bias="WAIT",score=0,historical=True',self.body)
        self.assertIn('Historical/unverified; no live signal',self.body)

    def test_partial_results_preserved_without_duplicates(self):
        self.assertIn('used={row.get("symbol") for row in chosen}',self.body)
        self.assertIn('row["symbol"] in used',self.body)
        self.assertIn('top5_candidates[:]=chosen',self.body)

if __name__=="__main__":
    unittest.main()
