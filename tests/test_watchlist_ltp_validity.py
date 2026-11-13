"""Invalid or non-positive LTP values must not be shown as recently fetched."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class WatchlistLtpValidityTests(unittest.TestCase):
    def test_fresh_ltp_must_be_positive_finite_number_not_bool(self):
        self.assertIn('not isinstance(quote_row["price"],bool) and math.isfinite(quote_row["price"]) and quote_row["price"]>0', SOURCE)
        self.assertIn('quote_source==expected_quote_source and quote_age is not None and 0<=quote_age<=60', SOURCE)

if __name__ == "__main__":
    unittest.main()
