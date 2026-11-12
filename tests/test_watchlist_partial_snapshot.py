"""Guard against showing stale equity prices after a partial Dhan snapshot."""
import unittest
from pathlib import Path


class WatchlistPartialSnapshotTests(unittest.TestCase):
    def test_missing_quotes_are_cleared_before_publishing_batch(self):
        text=(Path(__file__).resolve().parents[1]/"src"/"main.py").read_text(encoding="utf-8")
        start=text.index("    async def refresh_watch_batch():")
        end=text.index("        finally:",start)
        body=text[start:end]
        self.assertIn('if ticker not in batch and (quotes.get(ticker) or {}).get("source")=="Dhan":',body)
        self.assertIn('quotes.pop(ticker,None)',body)
        self.assertLess(body.index('quotes.pop(ticker,None)'),body.index('for ticker,snapshot in batch.items():'))
        self.assertIn('missing prices cleared',body)


if __name__=="__main__":
    unittest.main()
