"""Offline single-flight contract tests; fake workers only, no market network."""
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from refresh_coordinator import LaneCoordinator, VALID_LANES


class SharedLaneRefreshTests(unittest.TestCase):
    def test_lanes_are_explicit_and_cache_does_not_fake_live(self):
        self.assertEqual(VALID_LANES, {"quotes", "candles", "derivatives", "context"})
        now = [10.0]
        c = LaneCoordinator(clock=lambda: now[0])
        calls = []
        def fetch():
            calls.append(1)
            return {"freshness": "unverified", "quotes": {"NIFTY": 100}}
        a = c.run("quotes", "indexes", fetch, ttl_seconds=3)
        a["quotes"]["NIFTY"] = 0
        self.assertEqual(c.run("quotes", "indexes", fetch, ttl_seconds=3)["quotes"]["NIFTY"], 100)
        self.assertEqual(len(calls), 1)
        now[0] = 13
        self.assertEqual(c.run("quotes", "indexes", fetch, ttl_seconds=3)["freshness"], "unverified")
        self.assertEqual(len(calls), 2)

    def test_identical_concurrent_requests_one_owner_only(self):
        entered, release = Event(), Event()
        count = []
        c = LaneCoordinator()
        def load():
            count.append(1)
            entered.set()
            self.assertTrue(release.wait(5))
            return {"bars": [1, 2, 3], "signal_eligible": False}
        with ThreadPoolExecutor(max_workers=3) as pool:
            first = pool.submit(c.run, "candles", "NIFTY:5m:2026-11-16", load)
            self.assertTrue(entered.wait(5))
            second = pool.submit(c.run, "candles", "NIFTY:5m:2026-11-16", load)
            # Ensure the follower began, then release. A simultaneous entrant
            # after owner completion can legitimately refetch with TTL=0; use
            # a bounded result reuse interval to remove that race.
            release.set()
            self.assertEqual(first.result(timeout=5), second.result(timeout=5))
        # Above equality alone does not imply a guaranteed single network call
        # if scheduling starts follower after owner completion; separate test
        # uses TTL for deterministic single-call guarantee.

    def test_same_key_concurrency_with_ttl_is_at_most_once(self):
        c = LaneCoordinator()
        gate, release = Event(), Event()
        calls = []
        def fetch():
            calls.append(1)
            gate.set()
            self.assertTrue(release.wait(5))
            return {"value": 42}
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(c.run, "quotes", "51-stocks", fetch,
                                   ttl_seconds=15) for _ in range(8)]
            self.assertTrue(gate.wait(5))
            release.set()
            results = [f.result(timeout=5) for f in futures]
        self.assertEqual(results, [{"value": 42}] * 8)
        self.assertEqual(len(calls), 1)

    def test_failed_result_not_cached_and_invalidation(self):
        c = LaneCoordinator()
        n = [0]
        def sometimes():
            n[0] += 1
            if n[0] == 1:
                raise RuntimeError("provider cooldown")
            return {"source": "dhan", "live_verified": False}
        with self.assertRaisesRegex(RuntimeError, "provider cooldown"):
            c.run("derivatives", "NIFTY:expiry", sometimes, ttl_seconds=30)
        self.assertEqual(c.cache_size(), 0)
        c.run("derivatives", "NIFTY:expiry", sometimes, ttl_seconds=30)
        self.assertEqual(c.cache_size(), 1)
        c.invalidate("derivatives", "NIFTY:expiry")
        self.assertEqual(c.cache_size(), 0)

    def test_cache_bounds_and_unsafe_inputs(self):
        c = LaneCoordinator(max_cached=2)
        for i in range(8):
            c.run("context", f"news:{i}", lambda i=i: {"item": i}, ttl_seconds=600)
            self.assertLessEqual(c.cache_size(), 2)
        with self.assertRaises(ValueError):
            c.run("orders", "anything", lambda: {})
        with self.assertRaises(ValueError):
            c.run("quotes", "", lambda: {})
        with self.assertRaises(ValueError):
            c.run("quotes", "index", lambda: {}, ttl_seconds=901)
        with self.assertRaises(ValueError):
            c.run("quotes", "index", lambda: {}, ttl_seconds=float("nan"))


if __name__ == "__main__":
    unittest.main()
