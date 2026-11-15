"""Full-universe coverage and background failure recovery without provider I/O."""
import asyncio
import time
import unittest
from unittest.mock import patch

import flet as ft
import test_shared_analysis_runtime as shared_runtime
from server_feed import DHAN_VERIFIED_SYMBOLS


def text_values(root):
    values = []
    def walk(control):
        if isinstance(control, ft.Text): values.append(str(control.value))
        for child in control._get_children(): walk(child)
    walk(root)
    return " | ".join(values)


class RemainingFilterBatchTests(unittest.TestCase):
    def setup_app(self):
        return shared_runtime.SharedAnalysisRuntimeTests().setup_app()

    def test_scanner_universe_does_not_shrink_with_watchlists(self):
        _, v, _ = self.setup_app()
        for group in v["watch_groups"]: group.clear()
        self.assertFalse(v["all_watch_symbols"]())
        self.assertEqual(set(v["configured_scan_symbols"]()), DHAN_VERIFIED_SYMBOLS)
        self.assertEqual(len(v["configured_scan_symbols"]()), 54)

    def test_background_failure_remains_active_until_new_candle_response(self):
        _, v, _ = self.setup_app()
        v["refresh_shared_analysis"]("TCS")
        v["remember_candle_failure"]("TCS", "5m", "candle fetch", RuntimeError("secret-not-for-log"))
        self.assertNotIn("secret-not-for-log", repr(v["scan_fetch_failure"]))
        v["refresh_shared_analysis"]("TCS")
        self.assertEqual(v["current_filter_coverage"]()[1]["ERROR"], 1)
        health = text_values(v["data_overview"]())
        self.assertIn("1 active failure(s)", health)
        self.assertIn("1 errors", health)
        self.assertTrue(v["watch_signal_cache"]["TCS"]["historical"])
        self.assertNotIn("No active errors reported", health)
        failure = v["scan_fetch_failure"][(v["provider_generation"][0], "TCS", "5m")]
        v["failed_symbols"]["TCS"] = "previous failure"
        v["quotes"]["TCS"]["candle_fetched_at"] = failure["at"]+1
        v["refresh_shared_analysis"]("TCS")
        self.assertEqual(v["current_filter_coverage"]()[1]["ERROR"], 0)
        self.assertNotIn("TCS", v["failed_symbols"])

    def test_complete_scheduler_attempts_all_54_even_with_empty_watchlists(self):
        _, v, bars = self.setup_app()
        for group in v["watch_groups"]: group.clear()
        v["dhan_batch_cache"].update(generation=v["provider_generation"][0],
            updated=time.monotonic(), quotes={sym: {"source": "Dhan", "price": 100}
                                            for sym in v["watch_symbols"]})
        attempted = set()
        async def fake_io(fn, *args, **kwargs):
            if fn.__name__ == "get_market_data":
                attempted.add(args[0])
                return {"source": "Dhan", "bars": bars, "cached": False,
                        "fetched_at": time.time(), "candle_fetched_at": time.time(),
                        "freshness": "unverified", "live_verified": False}
            return {"items": [], "status": "No headlines"}
        async def stop_after_complete(delay):
            if v["scan_progress"].get("state") == "Complete":
                raise asyncio.CancelledError()
        with patch("asyncio.to_thread", side_effect=fake_io), \
             patch("asyncio.sleep", side_effect=stop_after_complete), \
             patch.object(v["dhan_feed"], "_call", side_effect=AssertionError("HTTP forbidden")):
            with self.assertRaises(asyncio.CancelledError):
                asyncio.run(v["refresh_market"]())
        self.assertEqual(attempted, DHAN_VERIFIED_SYMBOLS)
        self.assertEqual(v["current_filter_coverage"]()[1]["ANALYZED"], 54)
        self.assertTrue(all(row["symbol"] in v["watch_symbols"] for row in v["top5_candidates"]))
