"""Regression checks for read-only Oracle Dhan diagnostic transport."""
import importlib.util
import pathlib
import unittest
from unittest.mock import patch

PATH = pathlib.Path(__file__).resolve().parents[1] / "backend" / "check-dhan-live.py"
spec = importlib.util.spec_from_file_location("botking_dhan_smoke", PATH)
smoke = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke)


class FakeResponse:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.payload[:n]


class DhanSmokeTransportTests(unittest.TestCase):
    def test_valid_json(self):
        with patch.object(smoke.OPENER, "open", return_value=FakeResponse(b'{"ok":true}')):
            self.assertEqual(smoke.request("/health", "x" * 32), (200, {"ok": True}))

    def test_reject_oversized_response(self):
        with patch.object(smoke.OPENER, "open", return_value=FakeResponse(b"x" * 65537)):
            self.assertEqual(smoke.request("/health", "x" * 32), (0, None))

    def test_reject_invalid_utf8(self):
        with patch.object(smoke.OPENER, "open", return_value=FakeResponse(b"\\xff")):
            self.assertEqual(smoke.request("/health", "x" * 32), (0, None))

    def test_reject_nonfinite_json(self):
        with patch.object(smoke.OPENER, "open", return_value=FakeResponse(b'{"ltp":NaN}')):
            self.assertEqual(smoke.request("/dhan/ltp", "x" * 32), (0, None))

    def test_reject_json_array(self):
        with patch.object(smoke.OPENER, "open", return_value=FakeResponse(b"[]")):
            self.assertEqual(smoke.request("/dhan/status", "x" * 32), (0, None))

    def test_batch_schema_accepts_numeric_prices(self):
        self.assertTrue(smoke.valid_batch_quotes(200, {"RELIANCE": 1234.5}))

    def test_batch_schema_rejects_invalid_prices(self):
        for quotes in ({}, {"RELIANCE": True}, {"RELIANCE": float("nan")},
                       {"RELIANCE": 0}, {"RELIANCE": {"ltp": 123}},
                       {"NIFTY": 25000}):
            with self.subTest(quotes=quotes):
                self.assertFalse(smoke.valid_batch_quotes(200, quotes))
        self.assertFalse(smoke.valid_batch_quotes(502, {"RELIANCE": 1234.5}))

    def test_batch_envelope_requires_read_only_dhan(self):
        good = {"source": "dhan", "live_orders_enabled": False, "unavailable": []}
        self.assertTrue(smoke.valid_batch_quotes(200, {"RELIANCE": 123}, good))
        for bad in ({"source": "yahoo", "live_orders_enabled": False, "unavailable": []},
                    {"source": "dhan", "live_orders_enabled": True, "unavailable": []},
                    {"source": "dhan", "live_orders_enabled": False, "unavailable": {}}):
            with self.subTest(bad=bad):
                self.assertFalse(smoke.valid_batch_quotes(200, {"RELIANCE": 123}, bad))

    def test_candle_schema_valid(self):
        bars = [[100, 100.0, 105.0, 98.0, 102.0, 200],
                [200, 102.0, 106.0, 101.0, 105.0, 150]]
        self.assertTrue(smoke.valid_candle_bars(200, bars))

    def test_candle_schema_rejects_malformed_rows(self):
        valid = [100, 100.0, 105.0, 98.0, 102.0, 200]
        invalid = ([100, 100, 90, 98, 102, 200],
                   [100, 100, 105, 101, 99, 200],
                   [100, 100, 105, 98, 102, -1],
                   [100, 100, 105, 98, 102, float("inf")],
                   [True, 100, 105, 98, 102, 200],
                   [100, 100, 105, 98, 102])
        for row in invalid:
            with self.subTest(row=row):
                self.assertFalse(smoke.valid_candle_bars(200, [row]))
        self.assertFalse(smoke.valid_candle_bars(200, [valid, valid]))
        self.assertFalse(smoke.valid_candle_bars(502, [valid]))
        self.assertFalse(smoke.valid_candle_bars(200, []))

    def test_redirect_is_disabled(self):
        self.assertIsNone(smoke.NoRedirect().redirect_request(None, None, 302, "redirect", {}, "https://example.org"))


if __name__ == "__main__":
    unittest.main()
