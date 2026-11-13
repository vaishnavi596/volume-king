"""Watchlist must reject cross-provider or invalid numeric display values."""
from pathlib import Path
import unittest

SOURCE = Path(__file__).resolve().parents[1] / "src" / "main.py"


class WatchlistQuoteValidationTests(unittest.TestCase):
    def test_change_requires_selected_provider_and_connected_feed(self):
        body = SOURCE.read_text(encoding="utf-8").split("    def fill_watch(", 1)[1].split("    def ", 1)[0]
        self.assertIn("valid_change=(quote_source==expected_quote_source and not dhan_offline()", body)
        self.assertIn("not isinstance(change,bool)", body)

    def test_fresh_price_must_be_positive_nonboolean(self):
        body = SOURCE.read_text(encoding="utf-8").split("    def fill_watch(", 1)[1].split("    def ", 1)[0]
        self.assertIn('not isinstance(quote_row["price"],bool)', body)
        self.assertIn('quote_row["price"]>0', body)

    def test_signal_timestamp_must_be_finite_positive_nonboolean(self):
        body = SOURCE.read_text(encoding="utf-8").split("    def fill_watch(", 1)[1].split("    def ", 1)[0]
        self.assertIn("not isinstance(signal_stamp,bool)", body)
        self.assertIn("math.isfinite(signal_stamp) and signal_stamp>0", body)


if __name__ == "__main__":
    unittest.main()
