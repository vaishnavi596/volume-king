"""Offline-only guard for shared server-worker Dhan historical request lane."""
import json
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))
from dhan_feed import DhanFeed, DhanRateLimitError


class FakeResponse:
    def __init__(self):
        self.data = json.dumps({"data": {"open": []}}).encode("utf-8")

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, _max_bytes):
        return self.data


class DhanHistoryUpstreamPacingTests(unittest.TestCase):
    def test_two_instances_share_historical_serial_gate(self):
        called = []
        guard = threading.Lock()

        def opener(request, timeout):
            with guard:
                called.append((request.full_url, time.monotonic()))
            return FakeResponse()

        first = DhanFeed("test-client", "test-token", opener=opener)
        second = DhanFeed("test-client", "test-token", opener=opener)
        with DhanFeed._history_lock:
            saved = DhanFeed._history_next_allowed
            DhanFeed._history_next_allowed = 0.0
        errors = []
        try:
            def call(feed, path):
                try:
                    feed._post(path, {"securityId": "123"})
                except Exception as exc:
                    errors.append(exc)

            threads = [
                threading.Thread(target=call, args=(first, "/charts/intraday")),
                threading.Thread(target=call, args=(second, "/charts/historical")),
            ]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=5)
            self.assertFalse(any(thread.is_alive() for thread in threads))
            self.assertEqual(errors, [])
            self.assertEqual(len(called), 2)
            self.assertGreaterEqual(called[1][1] - called[0][1], 1.0)
        finally:
            with DhanFeed._history_lock:
                DhanFeed._history_next_allowed = saved

    def test_global_cooldown_prevents_history_outbound(self):
        requests = []
        feed = DhanFeed("test-client", "test-token",
                        opener=lambda req, timeout: requests.append(req) or FakeResponse())
        with DhanFeed._rate_lock:
            previous = DhanFeed._retry_after
            DhanFeed._retry_after = time.monotonic() + 30
        try:
            with self.assertRaises(DhanRateLimitError):
                feed._post("/charts/intraday", {"securityId": "123"})
            self.assertEqual(requests, [])
        finally:
            with DhanFeed._rate_lock:
                DhanFeed._retry_after = previous


if __name__ == "__main__":
    unittest.main()
