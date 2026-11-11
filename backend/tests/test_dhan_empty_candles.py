"""Offline regression checks for the read-only Dhan intraday endpoint.

Run: python -m unittest discover -s backend/tests -p 'test_dhan_empty_candles.py'
No real Dhan credentials, HTTP requests, or orders are used.
"""
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from backend import server


class DhanEmptyCandlesTests(unittest.TestCase):
    def setUp(self):
        self.key = "k" * 40
        self.app = server.create_app(pairing_key=self.key)
        self.endpoint = next(
            route.endpoint for route in self.app.routes
            if getattr(route, "path", None) == "/dhan/intraday"
        )
        self.body = server.DhanIntradayRequest(
            symbol="RELIANCE", interval=5,
            from_date="2026-11-10", to_date="2026-11-10"
        )
        self.env = patch.dict(os.environ, {"DHAN_CLIENT_ID": "test-client"})
        self.env.start()
        self.token = patch.object(server.Path, "read_text", return_value="test-token")
        self.token.start()
        self.addCleanup(self.env.stop)
        self.addCleanup(self.token.stop)

    def invoke(self, response):
        with patch.object(server, "DhanFeed") as feed:
            feed.return_value.intraday.return_value = response
            return self.endpoint(self.body, x_botking_key=self.key)

    def test_empty_session_is_not_provider_failure(self):
        response = self.invoke({
            "open": [], "high": [], "low": [],
            "close": [], "volume": [], "timestamp": []
        })
        self.assertEqual(response["bars"], [])
        self.assertEqual(response["freshness"], "no_candles_available")
        self.assertIs(response["live_orders_enabled"], False)

    def test_inconsistent_empty_arrays_are_rejected(self):
        response = {
            "open": [], "high": [1], "low": [],
            "close": [], "volume": [], "timestamp": []
        }
        with self.assertRaises(HTTPException) as error:
            self.invoke(response)
        self.assertEqual(error.exception.status_code, 502)

    def test_missing_candle_fields_are_rejected(self):
        with self.assertRaises(HTTPException) as error:
            self.invoke({"open": []})
        self.assertEqual(error.exception.status_code, 502)

    def test_pairing_key_required(self):
        with self.assertRaises(HTTPException) as error:
            self.endpoint(self.body, x_botking_key="invalid")
        self.assertEqual(error.exception.status_code, 403)


if __name__ == "__main__":
    unittest.main()
