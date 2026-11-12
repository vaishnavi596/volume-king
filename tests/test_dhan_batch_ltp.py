"""Offline regression checks for read-only batched Dhan quotes."""
import json
import unittest

from backend.dhan_feed import DhanFeed, DhanFeedError


class Response:
    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return b'{"data":{"NSE_EQ":{}}}'


class BatchLtpTests(unittest.TestCase):
    def setUp(self):
        self.calls = []

        def opener(request, timeout):
            self.calls.append((request.full_url, json.loads(request.data), timeout))
            return Response()

        self.feed = DhanFeed("client", "token", opener=opener)

    def test_batch_deduplicates_and_groups(self):
        self.feed.batch_ltp([("NSE_EQ", 2885), ("NSE_EQ", "2885"), ("IDX_I", 13)])
        self.assertEqual(len(self.calls), 1)
        self.assertEqual(self.calls[0][1], {"NSE_EQ": [2885], "IDX_I": [13]})

    def test_single_quote_uses_same_path(self):
        self.feed.ltp("NSE_EQ", 2885)
        self.assertEqual(self.calls[0][1], {"NSE_EQ": [2885]})

    def test_rejects_invalid_instruments_without_request(self):
        for invalid in ([], [("NSE_EQ", True)], [("BAD", 13)], [("NSE_EQ", -1)]):
            with self.subTest(invalid=invalid):
                with self.assertRaises(DhanFeedError):
                    self.feed.batch_ltp(invalid)
        self.assertFalse(self.calls)

    def test_batch_limit(self):
        with self.assertRaises(DhanFeedError):
            self.feed.batch_ltp([("NSE_EQ", n) for n in range(1, 1002)])
        self.assertFalse(self.calls)


if __name__ == "__main__":
    unittest.main()
