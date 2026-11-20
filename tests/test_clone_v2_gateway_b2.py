"""B2 clone-only SSK handshake regression; no Oracle or provider network use."""
import io
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from clone_v2_gateway import CloneV2Gateway, FeedError


GOOD = {"protocol": "botking-clone-v2", "authenticated": True,
        "read_only": True, "live_orders_enabled": False,
        "pipeline": "dhan-oracle-clone", "status": "ready"}


class Headers:
    def get_content_type(self):
        return "application/json"


class Response:
    def __init__(self, body, url):
        self.body = io.BytesIO(json.dumps(body).encode("utf-8"))
        self.url = url
        self.status = 200
        self.headers = Headers()

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self, n):
        return self.body.read(n)

    def geturl(self):
        return self.url


class FakeOpener:
    def __init__(self, payload=None, code=None):
        self.payload = GOOD if payload is None else payload
        self.code = code
        self.requests = []

    def open(self, req, timeout):
        self.requests.append(req)
        if self.code is not None:
            raise HTTPError(req.full_url, self.code, "blocked", {}, io.BytesIO())
        return Response(self.payload, req.full_url)


class CloneV2GatewayB2Tests(unittest.TestCase):
    def test_genuine_signed_off_readonly_status(self):
        opener = FakeOpener()
        gateway = CloneV2Gateway(opener=opener)
        with patch("clone_v2_gateway.checked_pairing_key", side_effect=lambda v: v):
            with patch("clone_v2_gateway.server_origin", side_effect=lambda v: v):
                status = gateway.connect("https://example.org", "temporary-secret")
        self.assertEqual(status["status"], "connected_read_only")
        self.assertFalse(status["live_market_data_verified"])
        self.assertTrue(gateway.connected)
        self.assertEqual(opener.requests[0].full_url, "https://example.org/clone-v2/status")
        self.assertEqual(opener.requests[0].get_header("X-botking-key"), "temporary-secret")
        gateway.disconnect()
        self.assertFalse(gateway.connected)

    def test_no_legacy_endpoint_fallback(self):
        opener = FakeOpener(code=404)
        gateway = CloneV2Gateway(opener=opener)
        with patch("clone_v2_gateway.checked_pairing_key", side_effect=lambda v: v), patch(
                "clone_v2_gateway.server_origin", side_effect=lambda v: v):
            with self.assertRaisesRegex(FeedError, "not deployed"):
                gateway.connect("https://example.org", "temporary-secret")
        self.assertFalse(gateway.connected)
        self.assertEqual(len(opener.requests), 1)

    def test_auth_denial_fails_closed(self):
        for code in (401, 403, 429):
            with self.subTest(code=code):
                opener = FakeOpener(code=code)
                gateway = CloneV2Gateway(opener=opener)
                with patch("clone_v2_gateway.checked_pairing_key", side_effect=lambda v: v), patch(
                        "clone_v2_gateway.server_origin", side_effect=lambda v: v):
                    with self.assertRaises(FeedError):
                        gateway.connect("https://example.org", "temporary-secret")
                self.assertFalse(gateway.connected)

    def test_invalid_status_never_activates(self):
        bad = [
            {**GOOD, "authenticated": False},
            {**GOOD, "live_orders_enabled": True},
            {**GOOD, "pipeline": "legacy-v1"},
            {**GOOD, "status": "disabled"},
            {**GOOD, "live_verified": True},
            {"status": "ready"},
        ]
        for payload in bad:
            with self.subTest(payload=payload):
                gateway = CloneV2Gateway(opener=FakeOpener(payload=payload))
                with patch("clone_v2_gateway.checked_pairing_key", side_effect=lambda v: v), patch(
                        "clone_v2_gateway.server_origin", side_effect=lambda v: v):
                    with self.assertRaises(FeedError):
                        gateway.connect("https://example.org", "temporary-secret")
                self.assertFalse(gateway.connected)


    def test_clone_b3_market_request_response_never_fake_data(self):
        class QuoteOpener:
            def __init__(self, result):
                self.result = result
                self.requests = []
            def open(self, req, timeout):
                self.requests.append(req)
                return Response(self.result, req.full_url)
        good_quotes = {"source": "dhan", "live_orders_enabled": False,
                       "freshness": "unverified", "unavailable": [],
                       "quotes": {"NIFTY": {"symbol": "NIFTY", "ltp": 25876.0,
                                            "source": "dhan", "freshness": "unverified"}}}
        opener = QuoteOpener(good_quotes)
        gateway = CloneV2Gateway(opener=opener)
        gateway._origin, gateway._key = "https://example.org", "private-in-memory"
        quotes = gateway.market_quotes(["NIFTY"])
        self.assertEqual(quotes, {"NIFTY": 25876.0})
        self.assertEqual(opener.requests[0].get_method(), "POST")
        self.assertEqual(opener.requests[0].full_url,
                         "https://example.org/clone-v2/market/quotes")
        self.assertEqual(json.loads(opener.requests[0].data), {"symbols": ["NIFTY"]})
        self.assertEqual(opener.requests[0].get_header("X-botking-key"), "private-in-memory")
        for body in ({**good_quotes, "live_orders_enabled": True},
                     {**good_quotes, "source": "legacy-v1"},
                     {**good_quotes, "quotes": {"NIFTY": {**good_quotes["quotes"]["NIFTY"], "ltp": -1}}},
                     {**good_quotes, "quotes": {}}):
            gateway._opener = QuoteOpener(body)
            with self.assertRaises(FeedError):
                gateway.market_quotes(["NIFTY"])
        gateway.disconnect()
        with self.assertRaises(FeedError):
            gateway.market_quotes(["NIFTY"])


if __name__ == "__main__":
    unittest.main()
