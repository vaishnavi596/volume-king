import io
import json
import unittest
import urllib.error
from scripts.check_dhan_option_route import check


class Response:
    status = 200
    def __init__(self, body):
        self.body = body
    def __enter__(self):
        return io.BytesIO(json.dumps(self.body).encode())
    def __exit__(self, *args):
        return False


class OracleSmokeTests(unittest.TestCase):
    def test_valid_contract_is_not_live_verified(self):
        def opener(request, timeout):
            self.assertEqual(timeout, 15)
            self.assertEqual(request.get_method(), "POST")
            self.assertNotIn(b"secret", request.data)
            return Response({"source": "dhan", "symbol": "NIFTY",
                             "expiry": "2099-12-31", "freshness": "unverified",
                             "signal_eligible": False, "live_orders_enabled": False,
                             "pcr": 1.2, "max_pain": 23000, "strike_count": 80})
        # Context-managed opener needs an HTTP status on its returned object.
        class HttpResponse(Response):
            def __enter__(self):
                stream = super().__enter__()
                stream.status = 200
                return stream
        result = check("https://example.test", "s" * 40, "NIFTY",
                       "2099-12-31", opener=lambda req, timeout: HttpResponse({
                           "source": "dhan", "symbol": "NIFTY",
                           "expiry": "2099-12-31", "freshness": "unverified",
                           "signal_eligible": False, "live_orders_enabled": False,
                           "pcr": 1.2, "max_pain": 23000, "strike_count": 80}))
        self.assertTrue(result["verified"])
        self.assertEqual(result["reason"], "contract_valid_freshness_unverified")
        self.assertNotIn("s" * 40, json.dumps(result))

    def test_error_status_is_redacted(self):
        def opener(req, timeout):
            raise urllib.error.HTTPError(req.full_url, 429, "rate limit",
                                         {}, io.BytesIO(b"provider secrets"))
        result = check("https://example.test", "s" * 40, "NIFTY",
                       "2099-12-31", opener=opener)
        self.assertEqual(result["http"], 429)
        self.assertEqual(result["reason"], "rate_limited")
        self.assertNotIn("provider secrets", json.dumps(result))

    def test_reject_unverified_underlying_before_request(self):
        with self.assertRaises(ValueError):
            check("https://example.test", "s" * 40, "BANKNIFTY",
                  "2099-12-31", opener=lambda *args, **kwargs: self.fail("network"))


if __name__ == "__main__":
    unittest.main()
