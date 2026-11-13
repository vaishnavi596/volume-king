"""Invalid quote timestamps must not be marked recently fetched."""
from pathlib import Path
import unittest
SOURCE = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")

class QuoteFetchTimestampTests(unittest.TestCase):
    def test_reject_boolean_and_nonfinite_fetch_times(self):
        self.assertIn('not isinstance(quote_row["fetched_at"],bool) and math.isfinite(quote_row["fetched_at"]) else None', SOURCE)
        self.assertIn('quote_age is not None and 0<=quote_age<=60', SOURCE)

if __name__ == "__main__":
    unittest.main()
