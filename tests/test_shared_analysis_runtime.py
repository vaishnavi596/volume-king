"""Actual Flet controls and app callbacks with supplied candles, no broker I/O."""
import time
import unittest
from unittest.mock import patch

from test_audit import start, event
from server_feed import DHAN_VERIFIED_SYMBOLS


class SharedAnalysisRuntimeTests(unittest.TestCase):
    def setup_app(self):
        page, v = start({"source": "Dhan", "scanner_symbol": "TCS",
                         "scanner_timeframe": "5m", "scanner_live": True})
        v["dhan_feed"]._origin = "https://example.invalid"
        v["dhan_feed"]._pairing_key = "test-only"
        end = int(time.time()) // 300 * 300 - 300
        bars = [[end-(59-i)*300,100+i,102+i,99+i,101+i,1000] for i in range(60)]
        for sym in DHAN_VERIFIED_SYMBOLS:
            v["quotes"][sym] = {"source": "Dhan", "bars": bars,
                "freshness": "unverified", "live_verified": False}
        return page, v, bars

    def test_all_54_update_without_network_and_unchanged_data_is_not_recalculated(self):
        _, v, _ = self.setup_app()
        with patch.object(v["dhan_feed"], "_call", side_effect=AssertionError("unexpected HTTP")):
            v["refresh_shared_analysis"]()
            self.assertEqual(len(v["watch_signal_cache"]), 54)
            self.assertTrue(all(row["symbol"] in v["watch_symbols"] for row in v["top5_candidates"]))
            rows, counts = v["analysis_audit"].coverage(DHAN_VERIFIED_SYMBOLS)
            self.assertEqual(counts["ANALYZED"], 54)
            self.assertTrue(all(r["available_filters"] == 10 for r in rows))
            self.assertTrue(all(r["historical"] for r in v["watch_signal_cache"].values()))
            before = {r["symbol"]: r["received_at"] for r in rows}
            v["refresh_shared_analysis"]()
            self.assertEqual(before, {r["symbol"]: r["received_at"] for r in v["analysis_audit"].coverage(DHAN_VERIFIED_SYMBOLS)[0]})

    def test_same_timestamp_correction_and_filter_change_invalidate_analysis(self):
        _, v, bars = self.setup_app()
        v["refresh_shared_analysis"]()
        previous = v["shared_analysis_seen"]["TCS"]
        corrected = [b[:] for b in bars]
        corrected[-1][4] -= .5
        v["quotes"]["TCS"]["bars"] = corrected
        v["refresh_shared_analysis"]("TCS")
        self.assertNotEqual(v["shared_analysis_seen"]["TCS"], previous)
        v["filter_selected"][:] = ["MACD"]
        v["refresh_shared_analysis"]()
        rows, counts = v["analysis_audit"].coverage(DHAN_VERIFIED_SYMBOLS)
        self.assertEqual(counts["ANALYZED"], 54)
        self.assertTrue(all(r["available_filters"] == 1 for r in rows))

    def test_newer_shared_history_replaces_older_scanner_snapshot(self):
        _, v, bars = self.setup_app()
        v["candles"]["scanner_chart_TCS"] = dict(v["quotes"]["TCS"],
            bars=bars[:-1], _scanner_timeframe="5m", _scanner_generation=v["scan_generation"][0])
        v["refresh_shared_analysis"]("TCS")
        self.assertEqual(v["watch_signal_cache"]["TCS"]["timestamp"], bars[-1][0])

    def test_busy_selection_receives_cached_result_after_work_finishes(self):
        _, v, _ = self.setup_app()
        v["scan_busy"][0] = True
        v["refresh_shared_analysis"]("TCS")
        self.assertIsNone(v["selected_report_identity"][0])
        v["scan_busy"][0] = False
        v["refresh_shared_analysis"]("TCS")
        self.assertEqual(v["selected_report_identity"][0][0], "TCS")
        self.assertTrue(v["scan_result"].controls)

    def test_ltp_receipt_time_cannot_override_newer_candle_revision(self):
        _, v, bars = self.setup_app()
        old = [b[:] for b in bars]
        old[-1][4] -= .5
        v["quotes"]["TCS"].update(bars=old, fetched_at=time.time(), candle_fetched_at=1)
        v["chart_snapshots"][("TCS", "5m", v["provider_generation"][0])] = {
            "source": "Dhan", "bars": bars, "candle_fetched_at": 2,
            "freshness": "unverified", "live_verified": False}
        v["refresh_shared_analysis"]("TCS")
        self.assertIn('160',v["shared_analysis_seen"]["TCS"][4])
        self.assertEqual(v["watch_signal_cache"]["TCS"]["price"], 160)

    def test_filter_editor_has_one_home_and_hidden_fields_do_not_leave_help_rows(self):
        _, v, _ = self.setup_app()
        v["open_filter_settings"]()
        self.assertEqual(v["current"][0], 2)
        v["scan_busy"][0] = True
        v["central_filter_settings"]()
        active = v["filter_selected"][0]
        v["remove_added_filter"](active)
        self.assertNotIn(active,v["filter_selected"])
        self.assertIn(active,[opt.key for opt in v["filter_choice"].options])
        self.assertEqual(v["current"][0], 2)
        field = v["scan_min"]
        field.visible = False
        self.assertIs(v["decorate_help"](field), field)
        field.visible = True
        wrapper = v["decorate_help"](field)
        field.visible = False
        self.assertFalse(v["decorate_help"](wrapper).visible)
        self.assertGreaterEqual(v["txt"]("Caption", 11).size, 14)
