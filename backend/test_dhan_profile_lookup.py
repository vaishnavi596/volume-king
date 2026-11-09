"""Fake HTTP tests for Dhan profile adapter; no external requests."""
import io
import json
import unittest

from dhan_profile_lookup import fetch_dhan_profile, PROFILE_URL


class FakeResponse:
    def __init__(self, payload, status=200):
        self.status = status
        self.buffer = io.BytesIO(payload)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit):
        return self.buffer.read(limit)


class ProfileLookupTests(unittest.TestCase):
    def test_success_and_request_contract(self):
        expected = {"dhanClientId": "TEST_ACCOUNT", "tokenValidity": "10/11/2026 09:43"}
        def opener(request, timeout):
            self.assertEqual(request.full_url, PROFILE_URL)
            self.assertEqual(request.get_method(), "GET")
            self.assertEqual(request.get_header("Access-token"), "FAKE_TOKEN")
            self.assertEqual(timeout, 12)
            return FakeResponse(json.dumps(expected).encode())
        self.assertEqual(fetch_dhan_profile("FAKE_TOKEN", opener), expected)

    def test_invalid_token_never_calls_http(self):
        def forbidden(*args, **kwargs):
            self.fail("Unexpected HTTP call")
        for token in ("", " BAD", "BAD\nTOKEN", None):
            with self.subTest(token=repr(token)), self.assertRaises(ValueError):
                fetch_dhan_profile(token, forbidden)

    def test_http_status_rejected(self):
        with self.assertRaises(ValueError):
            fetch_dhan_profile("FAKE_TOKEN", lambda *a, **k: FakeResponse(b"{}", 403))

    def test_oversized_response_rejected(self):
        with self.assertRaises(ValueError):
            fetch_dhan_profile("FAKE_TOKEN", lambda *a, **k: FakeResponse(b"x" * 65537))

    def test_non_object_response_rejected(self):
        with self.assertRaises(ValueError):
            fetch_dhan_profile("FAKE_TOKEN", lambda *a, **k: FakeResponse(b"[]"))

    def test_malformed_json_rejected_without_body_leak(self):
        with self.assertRaises(ValueError) as ctx:
            fetch_dhan_profile("FAKE_TOKEN", lambda *a, **k: FakeResponse(b"SECRET_RESPONSE{"))
        self.assertNotIn("SECRET_RESPONSE", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()
