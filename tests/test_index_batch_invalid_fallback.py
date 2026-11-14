"""Index batch recovery must retry missing and invalid prices, not just absent keys."""
from pathlib import Path
import unittest

MAIN=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")


class IndexBatchRecoveryTests(unittest.TestCase):
    def test_invalid_index_batch_rows_get_independent_retry(self):
        start=MAIN.index("    async def refresh_dhan_index_quotes(force=False):")
        end=MAIN.index("    manual_quote_last_attempt=",start)
        block=MAIN[start:end]
        self.assertIn('not isinstance(snapshots.get(sym),dict)',block)
        self.assertIn('snapshots[sym].get("source")!="Dhan"',block)
        self.assertIn('not math.isfinite(snapshots[sym]["price"])',block)
        self.assertIn('snapshots[sym]["price"]<=0',block)
        self.assertIn('dhan_feed.quote,missing_symbol',block)
        self.assertIn('isinstance(independent,dict)',block)
        self.assertIn('math.isfinite(independent["price"])',block)
        self.assertIn('if not isinstance(snapshot,dict):',block)
        self.assertIn('if isinstance(old,dict) and old.get("source")=="Dhan":',block)


if __name__=="__main__":
    unittest.main()
