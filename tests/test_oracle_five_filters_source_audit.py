"""Guard five Oracle assessment filters against fabricated bullish percentages.

The live Oracle deployment has NOT been verified by this source-only test.
"""
import sys
from pathlib import Path
from unittest import TestCase, main

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from shared_assessment_ui import FILTER_NAMES, assessment_lines


class OracleFiveFiltersSourceAudit(TestCase):
    def test_five_filter_identifiers_are_stable(self):
        self.assertEqual(FILTER_NAMES, ("oi_support", "oi_resistance",
                                        "max_pain", "pcr", "candle_trend"))

    def test_missing_cache_is_wait_not_bullish_percentage(self):
        messages = assessment_lines("RELIANCE", {}, now=100)
        self.assertIn("WAIT", " ".join(messages))
        self.assertNotIn("Bullish 100%", " ".join(messages))

    def test_unavailable_five_filters_cannot_be_promoted_by_pcr_value(self):
        payload = {
            "symbol": "RELIANCE", "live_orders_enabled": False,
            "signal_eligible": False,
            "factors": {name: {"status": "unavailable", "bullish": None,
                               "bearish": None} for name in
                        ("news", "futures", "options", "candle")},
            "assessment_filters": [
                {"id": name, "status": "unavailable", "value": 0.8 if name == "pcr" else None}
                for name in FILTER_NAMES],
            "bullish_score": None, "bearish_score": None,
        }
        rows = assessment_lines("RELIANCE", {
            "RELIANCE": {"fetched": 100, "data": payload}}, now=101)
        joined = " | ".join(rows)
        self.assertIn("PCR: WAIT", joined)
        self.assertIn("OI Support: WAIT", joined)
        self.assertIn("Candle: WAIT", joined)
        self.assertIn("no verified 0–100 scores", joined)

    def test_not_configured_explains_wait_on_compact_cards(self):
        payload = {
            "symbol": "RELIANCE", "collection_status": "not_configured",
            "live_orders_enabled": False, "signal_eligible": False,
            "factors": {name: {"status": "unavailable"} for name in
                        ("news", "futures", "options", "candle")},
            "assessment_filters": [
                {"id": name, "status": "unavailable"} for name in FILTER_NAMES],
        }
        rows = assessment_lines("RELIANCE", {
            "RELIANCE": {"fetched": 100, "data": payload}}, now=101)
        self.assertEqual(len(rows), 1)
        self.assertIn("WAIT", rows[0])
        self.assertIn("server producer not configured", rows[0])
        self.assertNotIn("100%", rows[0])

    def test_incomplete_not_configured_payload_is_malformed_not_proven(self):
        payload = {
            "symbol": "RELIANCE", "collection_status": "not_configured",
            "live_orders_enabled": False, "signal_eligible": False,
        }
        rows = assessment_lines("RELIANCE", {
            "RELIANCE": {"fetched": 100, "data": payload}}, now=101)
        self.assertIn("malformed response", rows[0])
        self.assertNotIn("server producer not configured", rows[0])

    def test_not_configured_does_not_override_unsafe_order_guard(self):
        payload = {
            "symbol": "RELIANCE", "collection_status": "not_configured",
            "live_orders_enabled": True, "signal_eligible": True,
        }
        rows = assessment_lines("RELIANCE", {
            "RELIANCE": {"fetched": 100, "data": payload}}, now=101)
        self.assertIn("unsafe response", rows[0])

    def test_nonfinite_assessment_cache_age_fails_closed_for_any_symbol(self):
        for symbol in ("RELIANCE", "HDFCBANK", "NIFTY", "BANKNIFTY", "SENSEX"):
            payload = {
                "symbol": symbol, "live_orders_enabled": False,
                "signal_eligible": False, "collection_status": "not_configured",
                "factors": {key: {"status": "unavailable"} for key in
                            ("news", "futures", "options", "candle")},
                "assessment_filters": [
                    {"id": key, "status": "unavailable"} for key in FILTER_NAMES],
            }
            for timestamp in (float("nan"), float("inf"), -float("inf"), True):
                rows = assessment_lines(symbol, {
                    symbol: {"fetched": timestamp, "data": payload}}, now=100)
                self.assertIn("cached assessment expired", rows[0])
            rows = assessment_lines(symbol, {
                symbol: {"fetched": 90, "data": payload}}, now=float("nan"))
            self.assertIn("cached assessment expired", rows[0])
            rows = assessment_lines(symbol, {
                symbol: {"fetched": 90, "data": payload}}, now=100, max_age=float("inf"))
            self.assertIn("cached assessment expired", rows[0])

    def test_malformed_filter_ids_do_not_crash_any_shared_symbol_view(self):
        for symbol in ("RELIANCE", "NIFTY", "BANKNIFTY", "SENSEX"):
            for bad_id in ([], {"unhashable": True}, None, 123):
                filters = [{"id": name, "status": "unavailable"}
                           for name in FILTER_NAMES]
                filters[0]["id"] = bad_id
                payload = {
                    "symbol": symbol, "collection_status": "not_configured",
                    "live_orders_enabled": False, "signal_eligible": False,
                    "factors": {key: {"status": "unavailable"} for key in
                                ("news", "futures", "options", "candle")},
                    "assessment_filters": filters,
                }
                lines = assessment_lines(symbol, {
                    symbol: {"fetched": 100, "data": payload}}, now=101)
                self.assertIn("incomplete filters", lines[0])
                self.assertNotIn("server producer not configured", lines[0])

    def test_incomplete_factor_rows_do_not_mask_placeholder_on_any_index(self):
        for symbol in ("RELIANCE", "NIFTY", "BANKNIFTY", "SENSEX"):
            for bad_row in ([], None, {"status": "unknown"}):
                data = {
                    "symbol": symbol, "collection_status": "not_configured",
                    "live_orders_enabled": False, "signal_eligible": False,
                    "factors": {
                        "news": {"status": "unavailable"},
                        "futures": {"status": "unavailable"},
                        "options": bad_row,
                        "candle": {"status": "unavailable"},
                    },
                    "assessment_filters": [
                        {"id": key, "status": "unavailable"} for key in FILTER_NAMES],
                }
                rows = assessment_lines(symbol, {
                    symbol: {"fetched": 100, "data": data}}, now=101)
                self.assertIn("incomplete factors", rows[0])
                self.assertNotIn("server producer not configured", rows[0])

    def test_not_configured_with_available_row_reports_inconsistency(self):
        for symbol in ("RELIANCE", "NIFTY", "BANKNIFTY", "SENSEX"):
            for row_type in ("filter", "factor"):
                payload = {
                    "symbol": symbol, "collection_status": "not_configured",
                    "live_orders_enabled": False, "signal_eligible": False,
                    "factors": {key: {"status": "unavailable"} for key in
                                ("news", "futures", "options", "candle")},
                    "assessment_filters": [
                        {"id": name, "status": "unavailable"} for name in FILTER_NAMES],
                }
                if row_type == "filter":
                    payload["assessment_filters"][0]["status"] = "available"
                else:
                    payload["factors"]["news"]["status"] = "available"
                rows = assessment_lines(symbol, {
                    symbol: {"fetched": 100, "data": payload}}, now=101)
                self.assertIn("inconsistent server response", rows[0])
                self.assertNotIn("server producer not configured", rows[0])

    def test_invalid_five_filter_status_is_incomplete_for_all_54(self):
        from server_feed import DHAN_VERIFIED_SYMBOLS
        for symbol in sorted(DHAN_VERIFIED_SYMBOLS):
            for wrong in ("unknown", None, [], 7):
                payload = {
                    "symbol": symbol, "live_orders_enabled": False,
                    "signal_eligible": False, "collection_status": "not_configured",
                    "factors": {name: {"status": "unavailable"} for name in
                                ("news", "futures", "options", "candle")},
                    "assessment_filters": [
                        {"id": key, "status": "unavailable"} for key in FILTER_NAMES],
                }
                payload["assessment_filters"][0]["status"] = wrong
                rows = assessment_lines(symbol, {
                    symbol: {"fetched": 100, "data": payload}}, now=101)
                self.assertIn("incomplete filters", rows[0])
                self.assertNotIn("server producer not configured", rows[0])

    def test_backend_has_no_assessment_producer_yet(self):
        source = (ROOT / "backend" / "server.py").read_text(encoding="utf-8")
        begin = source.index('    @app.get("/v2/assessment/{symbol}")')
        end = source.index('    @app.get("/v2/server-readiness")', begin)
        route = source[begin:end]
        self.assertIn('"collection_status": "not_configured"', route)
        self.assertIn('"bullish_score": None', route)
        self.assertIn('"bearish_score": None', route)
        self.assertIn('"status": "unavailable"', route)
        self.assertIn('"signal_eligible": False', route)
        self.assertNotIn("DhanFeed(", route)

    def test_historical_percentages_are_not_assessment_filter_scores(self):
        source = (ROOT / "src" / "main.py").read_text(encoding="utf-8")
        self.assertIn("historical_candle_balance(", source)
        # Explicit per-screen contexts replaced the old symbol-only UI call.
        # Historical percentages stay separate from Oracle evidence.
        self.assertIn('oracle_assessment_notes(sym,"watchlist")', source)
        self.assertIn('oracle_assessment_notes(scan_symbol.value or "NIFTY","scanner")', source)
        self.assertIn('oracle_assessment_notes(row["symbol"],"overview")', source)
        self.assertIn("five_engine_summary(symbol)", source)


if __name__ == "__main__":
    main()
