"""Selection handoff and display-time gates using actual app/Flet callbacks."""
import asyncio
import copy
import time
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from unittest.mock import patch

from analysis_reports import presentation_result
from test_audit import event
import test_shared_analysis_runtime as shared_runtime


class ScannerRefreshBatch2Tests(unittest.TestCase):
    def setup_app(self):
        return shared_runtime.SharedAnalysisRuntimeTests().setup_app()

    def test_shared_update_updates_home_summary_and_completed_candle_clock(self):
        _, v, bars = self.setup_app()
        v["refresh_shared_analysis"]("TCS")
        self.assertEqual(v["scan_shared"]["symbol"], "TCS")
        self.assertEqual(v["scan_shared"]["timestamp"], bars[-1][0])
        self.assertEqual(v["scan_last_candle"][0], bars[-1][0])
        checked = v["scan_last_success"][0]
        self.assertIsNotNone(checked)
        v["selected_report_identity"][0] = None
        v["refresh_shared_analysis"]("TCS")
        self.assertEqual(v["scan_last_success"][0], checked)

    def test_switch_to_unloaded_symbol_clears_previous_report_clocks(self):
        _, v, _ = self.setup_app()
        v["refresh_shared_analysis"]("TCS")
        v["quotes"].pop("INFY")
        v["scan_busy"][0] = True
        v["scan_symbol"].value = "INFY"
        v["trigger_scan"](event(v["scan_symbol"]))
        self.assertEqual(v["scan_shared"]["symbol"], "INFY")
        self.assertEqual(v["scan_shared"]["direction"], "WAIT")
        self.assertIsNone(v["scan_last_candle"][0])
        self.assertIsNone(v["scan_last_success"][0])

    def test_super_five_tap_invalidates_busy_scan_without_a_dropdown_event(self):
        _, v, _ = self.setup_app()
        v["refresh_shared_analysis"]("TCS")
        v["scan_busy"][0] = True
        generation = v["scan_generation"][0]
        v["open_candidate_chart"]("INFY")
        self.assertGreater(v["scan_generation"][0], generation)
        self.assertEqual(v["scan_shared"]["symbol"], "INFY")
        self.assertEqual(v["scan_selection_context"][0][0], "INFY")

    def test_programmatic_timeframe_normalizes_period_before_context_is_saved(self):
        _, v, _ = self.setup_app()
        v["scan_busy"][0] = True
        v["scan_tf"].value = "1m"
        v["scan_period"].value = "1mo"
        v["trigger_scan"]()
        self.assertEqual(v["scan_selection_context"][0], ("TCS", "1m", "7d"))
        self.assertEqual(v["prefs"]["scanner_period"], "7d")

    def test_cached_handoff_uses_newest_candle_series_not_newest_price(self):
        _, v, bars = self.setup_app()
        v["refresh_shared_analysis"]()
        old = [row[:] for row in bars]
        old[-1][4] -= .5
        v["quotes"]["INFY"].update(bars=old, fetched_at=time.time(), candle_fetched_at=1)
        v["chart_snapshots"][("INFY", "5m", v["provider_generation"][0])] = {
            "source": "Dhan", "bars": bars, "candle_fetched_at": 2}
        v["scan_busy"][0] = True
        v["scan_symbol"].value = "INFY"
        v["trigger_scan"](event(v["scan_symbol"]))
        self.assertEqual(v["shared_history"]("INFY")["bars"][-1][4], bars[-1][4])
        self.assertEqual(v["scan_shared"]["symbol"], "INFY")

    def test_provider_change_invalidates_home_result_and_clocks(self):
        _, v, _ = self.setup_app()
        v["refresh_shared_analysis"]("TCS")
        v["source"].value = "Yahoo Finance"
        v["source"].on_change(event(v["source"]))
        self.assertEqual(v["scan_shared"]["direction"], "WAIT")
        self.assertIsNone(v["scan_shared"]["timestamp"])
        self.assertFalse(v["shared_analysis_seen"])
        self.assertIsNone(v["scan_last_success"][0])

    def test_chart_toggle_does_not_change_central_analysis_mode_or_filters(self):
        _, v, _ = self.setup_app()
        v["filter_modes"]["EMA 9/21"] = "Chart"
        before = list(v["filter_selected"])
        control = type("Control", (), {"data": "EMA 9/21", "value": False})()
        v["scanner_chart_filter"](event(control))
        self.assertEqual(v["filter_modes"]["EMA 9/21"], "Chart")
        self.assertEqual(v["filter_selected"], before)
        self.assertFalse(v["ema_on_chart"]())

    def test_disconnection_demotes_selected_report_without_http(self):
        _, v, _ = self.setup_app()
        v["refresh_shared_analysis"]("TCS")
        v["dhan_feed"].disconnect()
        with patch.object(v["dhan_feed"], "_call", side_effect=AssertionError("HTTP forbidden")):
            v["refresh_shared_analysis"]()
        self.assertIn("DISCONNECTED", v["scan_shared"]["basis"])
        self.assertTrue(v["scan_shared"]["historical"])

    def test_auto_scan_off_never_starts_a_provider_poll(self):
        _, v, _ = self.setup_app()
        v["scan_tf"].value = "1m"
        v["scan_live"].value = False
        v["scan_busy"][0] = True
        with patch("asyncio.sleep", side_effect=AssertionError("auto scan must stay off")) as sleep:
            asyncio.run(v["auto_scan_loop"](v["scan_auto_generation"][0]))
        sleep.assert_not_called()

    def test_shared_candles_update_while_optional_news_is_busy(self):
        _, v, bars = self.setup_app()
        v["scan_busy"][0] = True
        v["scan_filter_ready"][0] = True
        v["refresh_shared_analysis"]("TCS")
        self.assertEqual(v["scan_shared"]["timestamp"], bars[-1][0])
        self.assertEqual(v["selected_report_identity"][0][0], "TCS")

    def test_symbol_change_releases_obsolete_news_work(self):
        _, v, _ = self.setup_app()
        active = []
        async def blocked_io(*args, **kwargs):
            marker = object()
            active.append(marker)
            try:
                await asyncio.Event().wait()
            finally:
                active.remove(marker)
        async def run():
            task = asyncio.create_task(v["selected_combined"]("TCS", "5m", {}, v["scan_generation"][0]))
            await asyncio.sleep(.02)
            v["scan_generation"][0] += 1
            v["scan_symbol"].value = "INFY"
            self.assertIsNone(await asyncio.wait_for(task, .5))
        with patch("asyncio.to_thread", side_effect=blocked_io):
            asyncio.run(run())
        self.assertEqual(active, [])

    def test_bad_new_series_cannot_leave_previous_selected_result_active(self):
        _, v, _ = self.setup_app()
        v["refresh_shared_analysis"]("TCS")
        v["quotes"]["TCS"]["bars"] = [["invalid", 1, 2, 1, 2, 100]]
        v["refresh_shared_analysis"]("TCS")
        self.assertEqual(v["scan_shared"]["direction"], "WAIT")
        self.assertIsNone(v["scan_shared"]["timestamp"])
        self.assertTrue(v["watch_signal_cache"]["TCS"]["historical"])

    def test_dashboard_uses_same_newer_candles_even_without_an_ltp_price(self):
        import flet as ft
        _, v, bars = self.setup_app()
        falling = [[b[0],200-i,200.2-i,199.8-i,200-i,1000] for i,b in enumerate(bars)]
        v["prefs"]["dashboard_analysis_slot_1"] = "TCS"
        v["quotes"]["TCS"].update(bars=falling, candle_fetched_at=2)
        v["chart_snapshots"][("TCS", "5m", v["provider_generation"][0])] = {
            "source": "Dhan", "bars": bars, "candle_fetched_at": 1}
        values = []
        def walk(control):
            if isinstance(control, ft.Text): values.append(str(control.value))
            for child in control._get_children(): walk(child)
        walk(v["dashboard_index_analysis"]())
        self.assertNotIn("Bearish 100%", values)
        self.assertTrue(any("1m candle votes WAIT" in label for label in values))

    def test_old_cache_cannot_clear_request_failure_but_new_response_can(self):
        _, v, _ = self.setup_app()
        v["refresh_shared_analysis"]("TCS")
        key = (v["provider_generation"][0], "TCS", "5m")
        at = time.time()
        v["scan_fetch_failure"][key] = {"at": at, "detail": "candle fetch • FeedError"}
        v["quotes"]["TCS"].update(candle_fetched_at=at-10,
            live_verified=True, freshness="verified_live")
        v["refresh_shared_analysis"]("TCS")
        self.assertIn(key, v["scan_fetch_failure"])
        self.assertIn("REFRESH FAILED", v["scan_shared"]["basis"])
        self.assertTrue(v["watch_signal_cache"]["TCS"]["historical"])
        self.assertFalse(v["watch_signal_cache"]["TCS"]["live_verified"])
        self.assertEqual(v["analysis_audit"].coverage(["TCS"])[1]["ERROR"], 1)
        v["quotes"]["TCS"]["candle_fetched_at"] = at+1
        v["refresh_shared_analysis"]("TCS")
        self.assertNotIn(key, v["scan_fetch_failure"])
        self.assertEqual(v["analysis_audit"].coverage(["TCS"])[1]["ANALYZED"], 1)

    def test_changing_back_to_dhan_preserves_user_auto_scan_off(self):
        page, v, _ = self.setup_app()
        v["scan_live"].value = False
        v["source"].value = "Yahoo Finance"
        v["source"].on_change(event(v["source"]))
        old = v["scan_auto_generation"][0]
        v["source"].value = "Dhan"
        v["source"].on_change(event(v["source"]))
        self.assertGreater(v["scan_auto_generation"][0], old)
        self.assertFalse(v["scan_live"].value)
        self.assertNotIn((v["auto_scan_loop"], (v["scan_auto_generation"][0],)), page.tasks)


class PresentationGateTests(unittest.TestCase):
    def test_verified_evidence_expires_without_mutating_cached_calculation(self):
        raw = {"source": "Dhan", "timestamp": 1000, "bias": "BULLISH", "score": 100,
               "live_verified": True, "freshness": "verified_live", "historical": False}
        original = copy.deepcopy(raw)
        def show(**kw):
            args = dict(expected_source="Dhan", now=1100, fresh_seconds=300,
                        market_open=True, connected=True)
            args.update(kw)
            return presentation_result(raw, **args)
        self.assertEqual(show()["actionable_bias"], "BULLISH")
        for args in ({"now": 1400}, {"now": 999}, {"market_open": False},
                     {"connected": False}, {"expected_source": "Yahoo Finance"}):
            shown = show(**args)
            self.assertEqual(shown["actionable_bias"], "WAIT")
            self.assertFalse(shown["live_verified"])
        mismatch = show(expected_source="Yahoo Finance")
        self.assertFalse(mismatch["votes"])
        self.assertIsNone(mismatch["timestamp"])
        self.assertEqual(raw, original)

    def test_invalid_timestamps_never_reach_datetime_rendering(self):
        for stamp in (None, True, float("nan"), float("inf"), -1):
            shown = presentation_result({"source": "Dhan", "timestamp": stamp},
                expected_source="Dhan", now=1000, fresh_seconds=300,
                market_open=True)
            self.assertIsNone(shown["timestamp"])
            self.assertFalse(shown["live_verified"])
