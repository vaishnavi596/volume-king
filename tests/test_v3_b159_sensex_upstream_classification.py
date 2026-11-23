"""B159 sanitized quote/candle upstream stage contract; no broker network."""
import io
import unittest
import urllib.error
from unittest.mock import patch
from backend.dhan_feed import DhanFeed, DhanUpstreamError
from backend.clone_v2_gateway import create_app
from fastapi.testclient import TestClient


class UpstreamClassTests(unittest.TestCase):
    def test_upstream_http_classes_never_expose_provider_body(self):
        for status, expected in ((400,"upstream_http_4xx"),(404,"upstream_http_4xx"),
                                 (500,"upstream_http_5xx"),(503,"upstream_http_5xx")):
            with self.subTest(status=status):
                def opener(req, timeout):
                    raise urllib.error.HTTPError(req.full_url,status,
                        "SECRET_TOKEN_NEVER_ECHO",{},io.BytesIO(b"secret-response"))
                with patch.object(DhanFeed,"_retry_after",0.0):
                    with self.assertRaises(DhanUpstreamError) as cm:
                        DhanFeed("client","secret-token",opener=opener).intraday({"securityId":"51"})
                self.assertEqual(cm.exception.category,expected)
                self.assertNotIn("secret",str(cm.exception).lower())

    def test_invalid_json_or_provider_rejection_classified(self):
        class Response:
            def __init__(self,payload):self.payload=payload
            def __enter__(self):return self
            def __exit__(self,*args):return False
            def read(self,limit):return self.payload
        for payload,expected in ((b"NOT_JSON","upstream_payload"),
                                 (b'{"errorType":"SECRET_PAYLOAD"}',"upstream_rejection")):
            with self.subTest(category=expected):
                with patch.object(DhanFeed,"_retry_after",0.0):
                    with self.assertRaises(DhanUpstreamError) as cm:
                        DhanFeed("client","secret",opener=lambda req,timeout: Response(payload)).intraday(
                            {"securityId":"51"})
                self.assertEqual(cm.exception.category,expected)
                self.assertNotIn("SECRET",str(cm.exception))

    def test_candle_provider_429_reports_stage_and_retry_without_leaking_details(self):
        from backend.dhan_feed import DhanRateLimitError
        class ThrottledProvider:
            def intraday(self,args):
                raise DhanRateLimitError("SECRET_UPSTREAM_REQUEST")
        app=create_app(key_bytes=b"K"*40,
                       market_feed_factory=lambda:ThrottledProvider(),
                       market_registry={"RELIANCE":("NSE_EQ",2885)})
        reply=TestClient(app).post("/clone-v2/market/candles",
            headers={"X-BotKing-Key":"K"*40},
            json={"symbol":"RELIANCE","interval":1,
                  "from_date":"2026-11-19","to_date":"2026-11-19"})
        self.assertEqual(reply.status_code,429)
        self.assertEqual(reply.headers.get("Retry-After"),"30")
        self.assertEqual(reply.headers.get("X-BotKing-429-Stage"),"PROVIDER_QUOTA")
        self.assertNotIn("SECRET_UPSTREAM_REQUEST",reply.text)

    def test_clone_logs_enum_without_exposing_http_response(self):
        class BrokenProvider:
            def intraday(self,args):
                raise DhanUpstreamError("upstream_http_5xx")
            def batch_ltp(self,args):
                raise DhanUpstreamError("upstream_rejection")
        import logging
        from datetime import date
        app=create_app(key_bytes=b"K"*40,market_feed_factory=lambda:BrokenProvider(),
                       market_registry={"RELIANCE":("NSE_EQ",2885)})
        client=TestClient(app)
        header={"X-BotKing-Key":"K"*40}
        with self.assertLogs("botking.clone.market",level="WARNING") as logs:
            reply=client.post("/clone-v2/market/candles",headers=header,json={
                "symbol":"SENSEX","interval":1,"from_date":"2026-11-19",
                "to_date":"2026-11-19"})
        self.assertEqual(reply.status_code,502)
        self.assertTrue(any("category=upstream_http_5xx" in row for row in logs.output))
        self.assertNotIn("secret",str(logs.output).lower())

if __name__=="__main__":unittest.main()
