"""No-network Gate 1 HTTPS route reconnaissance regression."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock
from urllib.error import URLError

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "verify_v2_gateway_routes.py"
spec = importlib.util.spec_from_file_location("verify_v2_gateway_routes", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class DummyResponse:
    def __init__(self, url, code):
        self.url, self.status = url, code

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def geturl(self):
        return self.url


class Gate1RoutesTests(unittest.TestCase):
    def test_no_auth_no_post_no_bodies_and_no_live_claim(self):
        requests = []
        def open_request(request, timeout):
            requests.append(request)
            return DummyResponse(request.full_url, 200)
        actual = mod.probe("https://example.test", opener=Mock(open=open_request))
        self.assertEqual(actual["status"], "OPEN_UNVERIFIED")
        self.assertEqual([req.get_method() for req in requests],
                         ["GET"] * len(mod.PATHS))
        for req in requests:
            self.assertIsNone(req.get_header("Authorization"))
            self.assertIsNone(req.data)
        self.assertEqual(actual["tests"][0]["assessment"],
                         "PUBLIC_200_NOT_AUTH_OR_DATA_PROOF")

    def test_post_auth_never_probed_as_get(self):
        observed = []
        def opener(request, timeout):
            observed.append((request.get_method(), request.full_url))
            return DummyResponse(request.full_url, 404)
        report = mod.probe("https://example.test", opener=Mock(open=opener))
        self.assertEqual(report["post_only_not_tested"], [
            "/v2-pilot/auth/challenge", "/v2-pilot/auth/login"])
        self.assertTrue(all(method == "GET" and "/auth/" not in url
                            for method, url in observed))
        self.assertEqual(len(observed), len(mod.PATHS))
        self.assertIn("/v2-pilot/private-backup", mod.PATHS)

    def test_status_indications_are_never_auth_proof(self):
        self.assertEqual(mod._meaning(403), "AUTH_DENIED_ROUTE_UNCONFIRMED")
        self.assertEqual(mod._meaning(405), "METHOD_DENIED_ROUTE_UNCONFIRMED")
        self.assertEqual(mod._meaning(404), "NOT_FOUND_AT_PUBLIC_EDGE")

    def test_no_insecure_origin(self):
        for origin in ("http://example.test",
                       "https://user:pass@example.test",
                       "https://example.test/something",
                       "https://example.test/?a=b"):
            with self.subTest(origin=origin), self.assertRaises(ValueError):
                mod._origin(origin)

    def test_unreachable_never_marked_deployed(self):
        actual = mod.probe("https://example.test",
                           opener=Mock(open=Mock(side_effect=URLError("secret"))))
        self.assertEqual({x["assessment"] for x in actual["tests"]},
                         {"UNREACHABLE_OR_TLS_ERROR"})
        self.assertNotIn("secret", repr(actual))


if __name__ == "__main__":
    unittest.main()
