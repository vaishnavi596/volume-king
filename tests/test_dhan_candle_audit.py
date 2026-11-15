"""Offline safety tests for read-only Dhan 51-equity candle audit."""
import datetime as dt
import importlib.util
import pathlib
import unittest
import io
from contextlib import redirect_stdout
from unittest.mock import patch

ROOT = pathlib.Path(__file__).resolve().parents[1]
PATH = ROOT / "backend" / "audit-dhan-51-candles.py"
SPEC = importlib.util.spec_from_file_location("audit_dhan_51_candles", PATH)
AUDIT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(AUDIT)


class CandleAuditSessionTests(unittest.TestCase):
    def test_equity_and_full_universes_have_no_missing_indices(self):
        self.assertEqual(len(AUDIT.audit_symbols()), 51)
        self.assertEqual(len(AUDIT.audit_symbols(True)), 54)
        self.assertEqual(set(AUDIT.audit_symbols(True))-set(AUDIT.audit_symbols()),
                         {"NIFTY", "BANKNIFTY", "SENSEX"})

    def test_app_and_gateway_mapping_names_and_segment_ids_match_contract(self):
        import ast
        tree = ast.parse((ROOT/"backend"/"server.py").read_text())
        mapping = next(ast.literal_eval(node.value) for node in tree.body
            if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and
                t.id == "DHAN_VERIFIED_INSTRUMENTS" for t in node.targets))
        self.assertEqual(set(mapping), set(AUDIT.audit_symbols(True)))
        self.assertEqual(len({(segment, sid) for segment, sid, _ in mapping.values()}), 54)
        for symbol in AUDIT.audit_symbols():
            segment, sid, kind = mapping[symbol]
            self.assertEqual((segment, kind), ("NSE_EQ", "EQUITY"))
            self.assertIs(type(sid), int)
            self.assertGreater(sid, 0)

    def test_full_server_audit_runs_all_54_filters_without_real_http(self):
        seen = []
        key = type("Key", (), {"read_text": lambda self, **kw: "x"*40})()
        def response(path, secret, payload=None):
            if path == "/dhan/status":
                return 200, {"authenticated": True, "market_data_configured": True,
                             "live_orders_enabled": False}
            self.assertEqual(path, "/dhan/intraday")
            seen.append(payload["symbol"])
            return 200, {"source": "dhan", "symbol": payload["symbol"],
                         "bars": self.bars, "live_orders_enabled": False}
        output = io.StringIO()
        with patch.object(AUDIT.module, "KEY_FILE", key), \
             patch.object(AUDIT.module, "request", side_effect=response), \
             patch.object(AUDIT.time, "sleep") as sleep, redirect_stdout(output):
            result = AUDIT.main(["--all-symbols", "--date", self.day.isoformat()])
        self.assertEqual(result, 0)
        self.assertEqual(set(seen), set(AUDIT.audit_symbols(True)))
        self.assertEqual(len(seen), 54)
        self.assertEqual(output.getvalue().count("filters 10/10"), 54)
        self.assertNotIn("x"*40, output.getvalue())
        self.assertEqual(sleep.call_count, 53)
        self.assertTrue(all(call.args == (1.5,) for call in sleep.call_args_list))

    def test_full_audit_stops_at_first_rate_limit(self):
        key = type("Key", (), {"read_text": lambda self, **kw: "x"*40})()
        def response(path, secret, payload=None):
            if path == "/dhan/status":
                return 200, {"authenticated": True, "market_data_configured": True,
                             "live_orders_enabled": False}
            return 429, None
        with patch.object(AUDIT.module, "KEY_FILE", key), \
             patch.object(AUDIT.module, "request", side_effect=response) as request, \
             patch.object(AUDIT.time, "sleep") as sleep, redirect_stdout(io.StringIO()):
            result = AUDIT.main(["--all-symbols", "--date", self.day.isoformat()])
        self.assertEqual(result, 3)
        self.assertEqual(request.call_count, 2)
        sleep.assert_not_called()

    def setUp(self):
        self.day = dt.date(2026, 11, 12)
        start = dt.datetime(2026, 11, 12, 9, 15, tzinfo=AUDIT.IST).timestamp()
        self.bars = [[start + i * 300, 100, 101, 99, 100, 1000] for i in range(30)]

    def test_valid_trading_session(self):
        self.assertTrue(AUDIT.bars_match_requested_day(self.bars, self.day))

    def test_wrong_day_rejected(self):
        self.assertFalse(AUDIT.bars_match_requested_day(self.bars, self.day - dt.timedelta(days=1)))

    def test_insufficient_candles_rejected(self):
        self.assertFalse(AUDIT.bars_match_requested_day(self.bars[:29], self.day))

    def test_before_open_and_at_close_rejected(self):
        before = [row[:] for row in self.bars]
        before[0][0] -= 300
        self.assertFalse(AUDIT.bars_match_requested_day(before, self.day))
        after = [row[:] for row in self.bars]
        after[-1][0] = dt.datetime(2026, 11, 12, 15, 30, tzinfo=AUDIT.IST).timestamp()
        self.assertFalse(AUDIT.bars_match_requested_day(after, self.day))

    def test_invalid_timestamp_fails_closed(self):
        for timestamp in (float("inf"), 10**30, None):
            invalid = [row[:] for row in self.bars]
            invalid[0][0] = timestamp
            self.assertFalse(AUDIT.bars_match_requested_day(invalid, self.day))


if __name__ == "__main__":
    unittest.main()
