"""Behavior test: the Doctor must keep the numeric HTTP status of a failed
gateway candle request even though safe_error() hides it from the user text."""
import sys, unittest
from urllib.error import HTTPError
sys.path.insert(0, "src")
from feed_health import http_status_from_exception, safe_error
from market_feed import FeedError


class HttpStatusFromExceptionTest(unittest.TestCase):
    def test_status_survives_safe_error_rewrite(self):
        # Real gateway messages (src/server_feed.py) that safe_error() rewrites
        # to "Dhan upstream temporarily unavailable; retry later".
        for code in (502, 503, 504):
            for text in ("Dhan upstream unavailable or token expired (HTTP %d)" % code,
                         "Dhan server HTTP %d" % code):
                exc = FeedError(text)
                self.assertEqual(safe_error(exc), "Dhan upstream temporarily unavailable; retry later")
                self.assertEqual(http_status_from_exception(exc), code)

    def test_other_gateway_statuses(self):
        self.assertEqual(http_status_from_exception(FeedError("Clone market candles HTTP 429")), 429)
        self.assertEqual(http_status_from_exception(FeedError("Dhan server key rejected (HTTP 403); reconnect")), 403)

    def test_urllib_http_error(self):
        exc = HTTPError("https://example.invalid/x", 502, "Bad Gateway", {}, None)
        self.assertEqual(http_status_from_exception(exc), 502)

    def test_no_status_is_none_and_never_echoes_text(self):
        self.assertIsNone(http_status_from_exception(FeedError("Network timeout")))
        self.assertIsNone(http_status_from_exception(FeedError("HTTP 200 ok")))
        self.assertIsNone(http_status_from_exception(RuntimeError("token=SECRET")))


if __name__ == "__main__":
    unittest.main()
