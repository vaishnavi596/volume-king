"""All 54 configured symbols reject malformed assessment filters at feed boundary.

No network, keys or broker market requests are made in this suite.
"""
import sys
from pathlib import Path
from unittest import TestCase, main
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from server_feed import (ServerDhanReadOnly, DHAN_VERIFIED_SYMBOLS,
                         DHAN_VERIFIED_INDEX_SYMBOLS, DHAN_VERIFIED_EQUITY_SYMBOLS, FeedError)

IDS = ("oi_support", "oi_resistance", "max_pain", "pcr", "candle_trend")


def payload(symbol, bad_id=None):
    rows = [{"id": value, "status": "unavailable"} for value in IDS]
    if bad_id is not None:
        rows[0]["id"] = bad_id
    return {
        "symbol": symbol, "live_orders_enabled": False,
        "signal_eligible": False, "bullish_score": None, "bearish_score": None,
        "factors": {name: {"status": "unavailable"} for name in
                    ("news", "futures", "options", "candle")},
        "assessment_filters": rows,
    }


class AssessmentTransport54Tests(TestCase):
    def test_shared_roster_covers_exactly_51_equities_and_three_indexes(self):
        self.assertEqual(len(DHAN_VERIFIED_EQUITY_SYMBOLS), 51)
        self.assertEqual(DHAN_VERIFIED_INDEX_SYMBOLS,
                         frozenset(("NIFTY", "BANKNIFTY", "SENSEX")))
        self.assertFalse(DHAN_VERIFIED_EQUITY_SYMBOLS & DHAN_VERIFIED_INDEX_SYMBOLS)
        self.assertEqual(DHAN_VERIFIED_SYMBOLS,
                         DHAN_VERIFIED_EQUITY_SYMBOLS | DHAN_VERIFIED_INDEX_SYMBOLS)
        self.assertEqual(len(DHAN_VERIFIED_SYMBOLS), 54)

    def test_client_and_backend_index_ids_are_statically_declared(self):
        import ast
        server = (ROOT / "backend" / "server.py").read_text()
        tree = ast.parse(server)
        declarations = [
            node for node in ast.walk(tree) if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name)
                    and target.id == "DHAN_VERIFIED_INSTRUMENTS"
                    for target in node.targets)
        ]
        self.assertEqual(len(declarations), 1)
        mapping = ast.literal_eval(declarations[0].value)
        self.assertEqual(
            {name: mapping[name][:2] for name in DHAN_VERIFIED_INDEX_SYMBOLS},
            {"NIFTY": ("IDX_I", 13), "BANKNIFTY": ("IDX_I", 25),
             "SENSEX": ("BSE_I", 51)})
        self.assertEqual(set(mapping), DHAN_VERIFIED_SYMBOLS)

    def test_selected_equity_cooldown_observes_route_and_global_backoff(self):
        import time
        feed = ServerDhanReadOnly()
        route = "/dhan/selected-ltp-batch"
        feed._cooldown_until[route] = time.monotonic() + 25
        self.assertGreaterEqual(feed.cooldown_remaining(route), 24)
        feed._cooldown_until[route] = 0
        feed._global_cooldown_until = time.monotonic() + 30
        self.assertGreaterEqual(feed.cooldown_remaining(route), 29)
        feed.disconnect()
        self.assertEqual(feed.cooldown_remaining(route), 0)
        self.assertEqual(feed.cooldown_remaining("/unverified/provider"), 0)

    def test_dynamic_candle_needs_registry_and_resets_on_disconnect(self):
        feed = ServerDhanReadOnly()
        response = {"source": "dhan", "symbol": "DYNAMICABC", "bars": []}
        with patch.object(feed, "_call", return_value=response) as call:
            # Registry lookup precedes the first historical request.
            with self.assertRaises(FeedError):
                feed.intraday("DYNAMICABC", 3, "2026-11-16", "2026-11-16")
            call.assert_not_called()
        registry = {"source": "dhan_registry", "symbols": ["DYNAMICABC"],
                    "live_orders_enabled": False}
        with patch.object(feed, "_call", side_effect=[registry, response, response]) as call:
            feed.intraday("DYNAMICABC", 5, "2026-11-16", "2026-11-16")
            feed.intraday("DYNAMICABC", 5, "2026-11-16", "2026-11-16")
            self.assertEqual(call.call_count, 3)
            self.assertTrue(call.call_args_list[0].args[0].startswith("/v2/instruments/search?"))
            self.assertEqual(call.call_args_list[1].args[0], "/dhan/intraday")
        feed.disconnect()
        self.assertNotIn("DYNAMICABC", feed._verified_dynamic_equities)
        with patch.object(feed, "_call", return_value={
                "source": "dhan_registry", "symbols": []}) as call:
            with self.assertRaises(FeedError):
                feed.intraday("DYNAMICABC", 5, "2026-11-16", "2026-11-16")
            call.assert_called_once()
        with patch.object(feed, "_call") as call:
            with self.assertRaises(FeedError):
                feed.intraday("NOT VALID!", 5, "2026-11-16", "2026-11-16")
            call.assert_not_called()

    def test_index_lane_rejects_unverified_orders_and_extra_symbols(self):
        feed = ServerDhanReadOnly()
        valid = {
            "source": "dhan", "live_orders_enabled": False,
            "quotes": {
                "NIFTY": {"symbol": "NIFTY", "source": "dhan", "ltp": 25000.0},
                "BANKNIFTY": {"symbol": "BANKNIFTY", "source": "dhan", "ltp": 60000.0},
                "SENSEX": {"symbol": "SENSEX", "source": "dhan", "ltp": 81000.0},
            }, "unavailable": [],
        }
        with patch.object(feed, "_call", return_value=valid):
            result = feed.index_batch_quotes()
            self.assertEqual(set(result), DHAN_VERIFIED_INDEX_SYMBOLS)
            self.assertTrue(all(row["freshness"] == "unverified" for row in result.values()))
        for changed in (
            dict(valid, live_orders_enabled=True),
            dict(valid, live_orders_enabled=None),
            dict(valid, quotes=dict(valid["quotes"], RELIANCE={
                "symbol": "RELIANCE", "source": "dhan", "ltp": 1000.0})),
            None,
        ):
            with self.subTest(changed=str(type(changed)) + str(bool(changed))):
                with patch.object(feed, "_call", return_value=changed):
                    with self.assertRaises(FeedError):
                        feed.index_batch_quotes()

    def test_equity_snapshot_rejects_each_index_in_quotes_and_unavailable(self):
        feed = ServerDhanReadOnly()
        for index in sorted(DHAN_VERIFIED_INDEX_SYMBOLS):
            for lane in ("quotes", "unavailable"):
                response = {
                    "protocol": 2, "source": "dhan", "live_orders_enabled": False,
                    "error": None, "collection_status": "recently_collected",
                    "live_verified": False, "age_seconds": 3,
                    "freshness": "unverified", "quote_timestamp": None,
                    "quotes": {"RELIANCE": 1200.0}, "unavailable": [],
                }
                if lane == "quotes":
                    response["quotes"][index] = 24000.0
                else:
                    response["unavailable"].append(index)
                with self.subTest(index=index, lane=lane):
                    with patch.object(feed, "_call", return_value=response):
                        with self.assertRaises(FeedError):
                            feed.batch_quotes()

    def test_54_roster_allows_same_complete_placeholder_contract(self):
        self.assertEqual(len(DHAN_VERIFIED_SYMBOLS), 54)
        feed = ServerDhanReadOnly()
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            with self.subTest(symbol=symbol):
                with patch.object(feed, "_call", return_value=payload(symbol)) as call:
                    self.assertEqual(feed.assessment(symbol)["symbol"], symbol)
                    call.assert_called_once_with("/v2/assessment/" + symbol)

    def test_assessment_selector_contract_for_indexes_equities_and_expiry(self):
        feed = ServerDhanReadOnly()
        examples = (
            ("NIFTY", "1m", "2026-11-26",
             "/v2/assessment/NIFTY?timeframe=1m&expiry=2026-11-26"),
            ("RELIANCE", "3m", None,
             "/v2/assessment/RELIANCE?timeframe=3m"),
            ("BANKNIFTY", "5m", None,
             "/v2/assessment/BANKNIFTY?timeframe=5m"),
        )
        for symbol, timeframe, expiry, path in examples:
            with self.subTest(symbol=symbol, timeframe=timeframe, expiry=expiry):
                with patch.object(feed, "_call", return_value=payload(symbol)) as call:
                    result = feed.assessment(symbol, timeframe=timeframe, expiry=expiry)
                    self.assertEqual(result["symbol"], symbol)
                    call.assert_called_once_with(path)

    def test_assessment_rejects_echoed_selection_mismatch(self):
        feed = ServerDhanReadOnly()
        selected_expiry = "2026-11-26"
        good = dict(payload("NIFTY"), timeframe="3m", expiry=selected_expiry)
        with patch.object(feed, "_call", return_value=good):
            self.assertEqual(feed.assessment(
                "NIFTY", timeframe="3m", expiry=selected_expiry)["timeframe"], "3m")
        for mismatch in ({"timeframe": "1m"}, {"timeframe": "5m"},
                         {"timeframe": None}, {"expiry": "2026-12-03"},
                         {"expiry": None}):
            with self.subTest(mismatch=mismatch):
                with patch.object(feed, "_call", return_value={**good, **mismatch}):
                    with self.assertRaises(FeedError):
                        feed.assessment("NIFTY", timeframe="3m",
                                        expiry=selected_expiry)
        # A legacy read-only WAIT response may omit echoed selectors until
        # the Oracle route is deployed; don't manufacture a verified signal.
        with patch.object(feed, "_call", return_value=payload("NIFTY")):
            response = feed.assessment("NIFTY", timeframe="3m",
                                       expiry=selected_expiry)
            self.assertTrue(all(row["status"] == "unavailable"
                                for row in response["assessment_filters"]))

    def test_assessment_invalid_selectors_fail_before_transport(self):
        feed = ServerDhanReadOnly()
        for timeframe in ("2m", "1", "", "1M", 1, [], False):
            with self.subTest(timeframe=timeframe):
                with patch.object(feed, "_call") as call:
                    with self.assertRaises(FeedError):
                        feed.assessment("NIFTY", timeframe=timeframe)
                    call.assert_not_called()
        for expiry in ("bad-date", "2026-13-01", "2026-2-1", "", 20261126, []):
            with self.subTest(expiry=expiry):
                with patch.object(feed, "_call") as call:
                    with self.assertRaises(FeedError):
                        feed.assessment("NIFTY", expiry=expiry)
                    call.assert_not_called()

    def test_app_assessment_poll_uses_scope_aware_request_and_attempt_key(self):
        # Source contract only; no Flet runtime, Android or network operations.
        app_source = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn('key=(generation,sym,tf,selected_expiry)', app_source)
        self.assertIn('dhan_feed.assessment,sym,timeframe=tf,expiry=selected_expiry', app_source)
        self.assertIn('"timeframe":tf,"expiry":selected_expiry', app_source)
        self.assertIn('date.fromisoformat(', app_source)

    def test_nonobject_assessment_payload_fails_as_feederror_for_every_symbol(self):
        feed = ServerDhanReadOnly()
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            for invalid in (None, [], "not configured", 200):
                with self.subTest(symbol=symbol, invalid=type(invalid).__name__):
                    with patch.object(feed, "_call", return_value=invalid):
                        with self.assertRaises(FeedError):
                            feed.assessment(symbol)

    def test_not_configured_cannot_claim_any_available_filter_or_factor(self):
        feed = ServerDhanReadOnly()
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            for field in ("factor", "filter"):
                response = payload(symbol)
                response["collection_status"] = "not_configured"
                if field == "factor":
                    response["factors"]["options"]["status"] = "available"
                else:
                    response["assessment_filters"][0]["status"] = "available"
                with self.subTest(symbol=symbol, field=field):
                    with patch.object(feed, "_call", return_value=response):
                        with self.assertRaises(FeedError):
                            feed.assessment(symbol)

    def test_malformed_factor_rows_fail_closed_for_all_54_symbols(self):
        feed = ServerDhanReadOnly()
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            for invalid in (None, [], "unavailable", {"status": "unknown"},
                            {"status": None}):
                with self.subTest(symbol=symbol, type=type(invalid).__name__):
                    response = payload(symbol)
                    response["factors"]["options"] = invalid
                    with patch.object(feed, "_call", return_value=response):
                        with self.assertRaises(FeedError):
                            feed.assessment(symbol)

    def test_unhashable_filter_ids_fail_as_feederror_for_every_symbol(self):
        feed = ServerDhanReadOnly()
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            for wrong in ([], {"bad": 1}):
                with self.subTest(symbol=symbol, wrong=type(wrong).__name__):
                    with patch.object(feed, "_call", return_value=payload(symbol, wrong)):
                        with self.assertRaises(FeedError):
                            feed.assessment(symbol)


if __name__ == "__main__":
    main()
