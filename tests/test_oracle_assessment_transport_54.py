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
