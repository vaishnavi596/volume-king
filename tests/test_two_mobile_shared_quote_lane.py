"""Two-device Oracle quote coalescing; offline and no Dhan network calls."""
import sys
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.shared_quote_lane import SharedQuoteLane


class Fake429(RuntimeError):
    pass


class TwoMobileSharedQuoteTests(unittest.TestCase):
    def test_same_quote_request_from_two_phones_calls_provider_once(self):
        lane = SharedQuoteLane(ttl_seconds=60)
        calls = Mock(return_value={"status": "success", "data": {"NSE_EQ": {"1": 42}}})
        results = []
        barrier = threading.Barrier(3)
        def device():
            barrier.wait(timeout=5)
            results.append(lane.run(("selected", "token-fingerprint", ("RELIANCE",)),
                                    calls, lambda row: row["status"] == "success",
                                    rate_limit_error=Fake429))
        threads = [threading.Thread(target=device), threading.Thread(target=device)]
        for thread in threads:
            thread.start()
        barrier.wait(timeout=5)
        for thread in threads:
            thread.join(timeout=5)
            self.assertFalse(thread.is_alive())
        self.assertEqual(calls.call_count, 1)
        self.assertEqual(len(results), 2)

    def test_different_selected_sets_not_reused(self):
        lane = SharedQuoteLane(ttl_seconds=60)
        calls = Mock(side_effect=[
            {"status": "success", "data": {"NSE_EQ": {"1": 11}}},
            {"status": "success", "data": {"NSE_EQ": {"2": 22}}},
        ])
        for key in (("selected", "A"), ("selected", "B")):
            lane.run(key, calls, lambda data: data["status"] == "success",
                     rate_limit_error=Fake429)
        self.assertEqual(calls.call_count, 2)

    def test_token_rotation_never_reuses_old_result(self):
        lane = SharedQuoteLane(ttl_seconds=60)
        fetch = Mock(return_value={"status": "success"})
        for key in (("index", b"old"), ("index", b"new")):
            lane.run(key, fetch, lambda row: True, rate_limit_error=Fake429)
        self.assertEqual(fetch.call_count, 2)

    def test_invalid_response_not_cached(self):
        lane = SharedQuoteLane()
        calls = Mock(side_effect=[{"status": "failure"}, {"status": "success"}])
        for _ in range(2):
            lane.run("index", calls, lambda row: row["status"] == "success",
                     rate_limit_error=Fake429)
        self.assertEqual(calls.call_count, 2)

    def test_429_shared_cooldown_prevents_second_phone_attempt(self):
        now = [100.]
        lane = SharedQuoteLane(clock=lambda: now[0])
        calls = Mock(side_effect=Fake429("429"))
        with self.assertRaises(Fake429):
            lane.run("index", calls, lambda _: True, rate_limit_error=Fake429)
        with self.assertRaises(Fake429):
            lane.run("selected", calls, lambda _: True, rate_limit_error=Fake429)
        self.assertEqual(calls.call_count, 1)
        now[0] += 31
        with self.assertRaises(Fake429):
            lane.run("selected", calls, lambda _: True, rate_limit_error=Fake429)
        self.assertEqual(calls.call_count, 2)

    def test_ttl_expires_and_bounded_cache(self):
        now = [100.]
        lane = SharedQuoteLane(clock=lambda: now[0], max_entries=2)
        fetch = Mock(return_value={"status": "success"})
        for key in ("a", "b", "c"):
            lane.run(key, fetch, lambda _: True, rate_limit_error=Fake429)
        self.assertEqual(fetch.call_count, 3)
        lane.run("a", fetch, lambda _: True, rate_limit_error=Fake429)
        self.assertEqual(fetch.call_count, 4)
        now[0] += 61
        lane.run("a", fetch, lambda _: True, rate_limit_error=Fake429)
        self.assertEqual(fetch.call_count, 5)

    def test_server_routes_reuse_one_lane(self):
        source = (ROOT / "backend/server.py").read_text(encoding="utf-8")
        self.assertIn("shared_quote_lane = SharedQuoteLane", source)
        self.assertEqual(source.count("shared_quote_lane.run("), 2)
        self.assertIn('("indices", client, hashlib.sha256(token.encode()).digest())', source)
        self.assertIn('tuple(sorted(symbols))', source)


if __name__ == "__main__":
    unittest.main()
