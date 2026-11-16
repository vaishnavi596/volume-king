"""Concurrent two-phone /dhan/intraday requests share one validated upstream result."""
import concurrent.futures
import os
import threading
import time
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.server import create_app

KEY = "test-only-pairing-key-32-characters-long"
REQUEST = {"symbol": "NIFTY", "interval": 5,
           "from_date": "2025-10-09", "to_date": "2025-10-09"}


class StubAngel:
    connected = False
    instruments = None
    resolved = {}
    def disconnect(self): pass


class SingleFlightTests(unittest.TestCase):
    def test_simultaneous_identical_history_requests_share_one_upstream_call(self):
        calls = []
        entered = threading.Event()
        release = threading.Event()

        class SlowDhan:
            def __init__(self, client, token):
                pass
            def intraday(self, payload):
                calls.append(payload)
                entered.set()
                self_outer = release.wait(timeout=4)
                if not self_outer:
                    raise RuntimeError("test request release timed out")
                return {"open": [100], "high": [102], "low": [99],
                        "close": [101], "volume": [50], "timestamp": [1760000000]}

        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}), \
             patch("backend.server.Path.read_text", return_value="fake-token"), \
             patch("backend.server.DhanFeed", SlowDhan):
            app = create_app(pairing_key=KEY, feed=StubAngel())
            client = TestClient(app)
            with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
                first = executor.submit(client.post, "/dhan/intraday", json=REQUEST,
                                        headers={"X-BotKing-Key": KEY})
                self.assertTrue(entered.wait(timeout=3))
                second = executor.submit(client.post, "/dhan/intraday", json=REQUEST,
                                         headers={"X-BotKing-Key": KEY})
                time.sleep(0.15)
                release.set()
                responses = [first.result(timeout=6), second.result(timeout=6)]
            self.assertEqual([x.status_code for x in responses], [200, 200])
            self.assertEqual(len(calls), 1)
            self.assertEqual(responses[0].json()["bars"], responses[1].json()["bars"])
            self.assertEqual(responses[1].json()["freshness"], "historical_unverified")
            self.assertFalse(responses[1].json()["live_orders_enabled"])

    def test_distinct_date_windows_do_not_reuse_wrong_candles(self):
        calls = []

        class DateDhan:
            def __init__(self, client, token):
                pass
            def intraday(self, payload):
                calls.append(payload["fromDate"])
                price = 100 if "2025-10-09" in payload["fromDate"] else 200
                return {"open": [price], "high": [price + 2],
                        "low": [price - 1], "close": [price + 1],
                        "volume": [50], "timestamp": [1760000000]}

        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}), \
             patch("backend.server.Path.read_text", return_value="fake-token"), \
             patch("backend.server.DhanFeed", DateDhan):
            client = TestClient(create_app(pairing_key=KEY, feed=StubAngel()))
            first = client.post("/dhan/intraday", json=REQUEST,
                                headers={"X-BotKing-Key": KEY})
            other = dict(REQUEST, from_date="2025-10-10", to_date="2025-10-10")
            second = client.post("/dhan/intraday", json=other,
                                 headers={"X-BotKing-Key": KEY})
        self.assertEqual((first.status_code, second.status_code), (200, 200))
        self.assertEqual(len(calls), 2)
        self.assertNotEqual(first.json()["bars"][0][1], second.json()["bars"][0][1])

    def test_failed_upstream_does_not_poison_cache(self):
        calls = []

        class FlakyDhan:
            def __init__(self, client, token):
                pass
            def intraday(self, payload):
                calls.append(1)
                if len(calls) == 1:
                    return {"status": "failure"}
                return {"open": [100], "high": [102], "low": [99],
                        "close": [101], "volume": [50], "timestamp": [1760000000]}

        with patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"}), \
             patch("backend.server.Path.read_text", return_value="fake-token"), \
             patch("backend.server.DhanFeed", FlakyDhan):
            client = TestClient(create_app(pairing_key=KEY, feed=StubAngel()))
            first = client.post("/dhan/intraday", json=REQUEST,
                                headers={"X-BotKing-Key": KEY})
            second = client.post("/dhan/intraday", json=REQUEST,
                                 headers={"X-BotKing-Key": KEY})
        self.assertEqual(first.status_code, 502)
        self.assertEqual(second.status_code, 200)
        self.assertEqual(len(calls), 2)
        self.assertFalse(second.json()["live_orders_enabled"])

    def test_reentrant_stripe_supports_nested_derived_history_without_deadlock(self):
        """Oracle's 3m->1m and 30m->5m recursion must never deadlock a lane."""
        lanes = tuple(threading.RLock() for _ in range(32))
        for derived, base in ((3, 1), (30, 5)):
            # Force the worst-case collision: both calls take the SAME lane.
            lane = lanes[0]
            seen = []
            def history(interval):
                with lane:
                    seen.append(interval)
                    if interval == derived:
                        return history(base)
                    return "validated-base"
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                result = executor.submit(history, derived).result(timeout=2)
            self.assertEqual(result, "validated-base")
            self.assertEqual(seen, [derived, base])

    def test_reentrant_lane_serializes_other_threads(self):
        """RLock allows same-thread recursion but excludes another mobile thread."""
        lane = threading.RLock()
        entered = threading.Event()
        release = threading.Event()
        order = []
        def first():
            with lane:
                with lane:
                    order.append("first")
                    entered.set()
                    self.assertTrue(release.wait(timeout=3))
        def second():
            with lane:
                order.append("second")
        with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
            a = executor.submit(first)
            self.assertTrue(entered.wait(timeout=2))
            z = executor.submit(second)
            time.sleep(0.1)
            self.assertEqual(order, ["first"])
            release.set()
            a.result(timeout=3)
            z.result(timeout=3)
        self.assertEqual(order, ["first", "second"])

    def test_missing_pairing_key_does_not_invoke_upstream(self):
        app = create_app(pairing_key=KEY, feed=StubAngel())
        with patch("backend.server.DhanFeed", side_effect=AssertionError("unexpected Dhan call")):
            response = TestClient(app).post("/dhan/intraday", json=REQUEST)
        self.assertEqual(response.status_code, 403)


if __name__ == "__main__":
    unittest.main()
