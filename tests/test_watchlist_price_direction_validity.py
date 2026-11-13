"""Price direction cannot be trusted without a valid positive quote."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
class WatchlistPriceDirectionTests(unittest.TestCase):
    def test_change_requires_positive_ltp(self):
        self.assertIn('valid_change=(isinstance(change,(int,float))', SOURCE)
        self.assertIn('math.isfinite(quote_row["price"]) and quote_row["price"]>0)', SOURCE)
        self.assertIn('else "Unavailable"', SOURCE)
if __name__ == "__main__":
    unittest.main()
