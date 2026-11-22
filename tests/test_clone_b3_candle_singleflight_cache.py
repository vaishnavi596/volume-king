"""Clone-only candle cache/singleflight: fake Dhan provider, no network."""
import concurrent.futures
import threading
import time
import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

from fastapi.testclient import TestClient
from backend.clone_v2_gateway import create_app


class CloneCandleCacheTests(unittest.TestCase):
    KEY = b"k" * 40
    def setUp(self):
        self.today = datetime.now(timezone(timedelta(hours=5, minutes=30))).date()
        self.headers = {"X-BotKing-Key": self.KEY.decode()}
        self.path = "/clone-v2/market/candles"

    def request(self, symbol="SENSEX", interval=1, date=None):
        day = (date or self.today).isoformat()
        return {"symbol": symbol, "interval": interval,
                "from_date": day, "to_date": day}

    def feed(self, fails=False, empty=False):
        class Fake:
            def __init__(self):
                self.calls = []
                self.lock = threading.Lock()
            def intraday(self, args):
                with self.lock:
                    self.calls.append(dict(args))
                time.sleep(0.02)
                if fails:
                    raise ValueError("private broker detail must not be echoed")
                bars = [] if empty else [1800000000, 1800000060]
                return {"status": "success", "timestamp": bars,
                        "open": [100, 101][:len(bars)],
                        "high": [102, 103][:len(bars)],
                        "low": [99, 100][:len(bars)],
                        "close": [101, 102][:len(bars)],
                        "volume": [100, 110][:len(bars)]}
        obj = Fake()
        http = TestClient(create_app(key_bytes=self.KEY,
                                      market_feed_factory=lambda: obj,
                                      market_registry={"RELIANCE": ("NSE_EQ", 2885)}))
        return obj, http

    def test_repeated_same_window_hits_validated_cache(self):
        feed, http = self.feed()
        payload = self.request()
        first = http.post(self.path, headers=self.headers, json=payload)
        second = http.post(self.path, headers=self.headers, json=payload)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(first.json(), second.json())
        self.assertEqual(len(feed.calls), 1)
        self.assertEqual(first.json()["freshness"], "historical_unverified")

    def test_normalized_bars_digest_matches_exact_gateway_payload(self):
        import hashlib
        import json
        _, http = self.feed()
        res = http.post(self.path, headers=self.headers, json=self.request())
        self.assertEqual(res.status_code, 200)
        body = res.json()
        expected = hashlib.sha256(json.dumps(
            body["bars"], separators=(",",":"), allow_nan=False
        ).encode("utf-8")).hexdigest()
        self.assertEqual(body["normalized_bars_sha256"], expected)
        self.assertEqual(body["freshness"], "historical_unverified")
        self.assertFalse(body["live_orders_enabled"])

    def test_concurrent_matching_requests_single_provider_call(self):
        feed, http = self.feed()
        payload = self.request()
        with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(
                lambda _: http.post(self.path, headers=self.headers, json=payload),
                range(4)))
        self.assertTrue(all(r.status_code == 200 for r in results))
        self.assertEqual(len(feed.calls), 1)

    def test_symbol_interval_and_date_are_distinct(self):
        feed, http = self.feed()
        yesterday = self.today - timedelta(days=1)
        payloads = [self.request(), self.request(interval=5),
                    self.request(symbol="NIFTY"), self.request(date=yesterday)]
        for payload in payloads:
            self.assertEqual(http.post(self.path, headers=self.headers,
                                       json=payload).status_code, 200)
        self.assertEqual(len(feed.calls), 4)

    def test_empty_bars_not_cached(self):
        feed, http = self.feed(empty=True)
        for _ in range(2):
            res = http.post(self.path, headers=self.headers, json=self.request())
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.json()["freshness"], "no_candles_available")
        self.assertEqual(len(feed.calls), 2)

    def test_provider_error_not_cached(self):
        feed, http = self.feed(fails=True)
        with patch("backend.clone_v2_gateway.DIAGNOSTIC_LOGGER.warning"):
            for _ in range(2):
                self.assertEqual(http.post(self.path, headers=self.headers,
                                           json=self.request()).status_code, 502)
        self.assertEqual(len(feed.calls), 2)

    def test_unauthorized_does_not_serve_cache(self):
        feed, http = self.feed()
        payload = self.request()
        self.assertEqual(http.post(self.path, headers=self.headers,
                                   json=payload).status_code, 200)
        self.assertEqual(http.post(self.path, json=payload).status_code, 403)
        self.assertEqual(len(feed.calls), 1)


if __name__ == "__main__":
    unittest.main()
