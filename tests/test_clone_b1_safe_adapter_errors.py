"""Safe Clone adapter diagnostic messages: explain real stage, never expose secrets."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from feed_health import safe_error
from market_feed import FeedError


class CloneSafeAdapterMessages(unittest.TestCase):
    def test_candle_error_types_have_specific_safe_messages(self):
        cases = {
            "Clone market candles HTTP 422": "interval or date rejected",
            "Clone market candles HTTP 424": "authorization required",
            "Clone market candles HTTP 429": "cooldown",
            "Clone market candles HTTP 502": "upstream unavailable",
            "Clone Dhan candles unavailable": "gateway unavailable",
            "Clone candle response not verified": "invalid candle data contract",
            "Clone unsupported candle interval": "timeframe unsupported",
        }
        for raw, expected in cases.items():
            with self.subTest(raw=raw):
                self.assertIn(expected, safe_error(FeedError(raw)).lower())

    def test_option_adapter_error_categories(self):
        for raw in ("Clone listed option expiries invalid",
                    "Clone option evidence unavailable",
                    "Clone Dhan options/expiries unavailable",
                    "Clone Dhan options/chain unavailable"):
            with self.subTest(raw=raw):
                msg = safe_error(FeedError(raw))
                self.assertIn("option", msg.lower())
                self.assertNotIn("Data request failed", msg)

    def test_arbitrary_sensitive_exception_remains_redacted(self):
        secret = "secret-token-12345"
        for raw in ("Clone market candles HTTP 502 " + secret,
                    "Clone Dhan candles unavailable " + secret,
                    "https://private.invalid?token=" + secret):
            message = safe_error(FeedError(raw))
            self.assertNotIn(secret, message)
            self.assertIn("Data request failed", message)


if __name__ == "__main__":
    unittest.main()
