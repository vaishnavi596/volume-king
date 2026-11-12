"""Offline Oracle 226 device login transport tests; no network."""
import asyncio
import base64
import io
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from oracle_device_login_226 import OracleDeviceLogin226, OracleDeviceLoginError


class Response:
    status = 200
    def __init__(self, data):
        self.stream = io.BytesIO(json.dumps(data).encode())
    def __enter__(self): return self
    def __exit__(self, *args): return False
    def read(self, n): return self.stream.read(n)


class Opener:
    def __init__(self, results):
        self.results = iter(results)
        self.requests = []
    def open(self, req, timeout):
        self.requests.append(req)
        return Response(next(self.results))


class Native:
    async def sign_login_challenge(self, device_id, challenge):
        return "s" * 96


class OracleDeviceLoginTests(unittest.TestCase):
    def test_challenge_session_handshake(self):
        challenge = base64.urlsafe_b64encode(b"c" * 32).decode("ascii")
        opener = Opener([{"challenge": challenge},
                         {"access_token": "t" * 48, "token_type": "bearer",
                          "expires_in_seconds": 900}])
        client = OracleDeviceLogin226("https://example.com", opener=opener)
        token = asyncio.run(client.login("android_owner_device_226", Native()))
        self.assertEqual(token, "t" * 48)
        self.assertEqual(len(opener.requests), 2)
        self.assertNotIn("X-BotKing-Key", opener.requests[0].headers)
        self.assertIn(b'"signature"', opener.requests[1].data)

    def test_invalid_device_ids_fail_before_network(self):
        for device_id in ("a" * 15, "a" * 129, "android owner device", "android_é_device_226", "android/device_226"):
            with self.subTest(device_id=device_id):
                opener = Opener([])
                client = OracleDeviceLogin226("https://example.com", opener=opener)
                with self.assertRaises(OracleDeviceLoginError):
                    asyncio.run(client.login(device_id, Native()))
                self.assertEqual(opener.requests, [])

    def test_bad_challenge_fails_before_signing(self):
        opener = Opener([{"challenge": "bad"}])
        client = OracleDeviceLogin226("https://example.com", opener=opener)
        with self.assertRaises(OracleDeviceLoginError):
            asyncio.run(client.login("android_owner_device_226", Native()))
        self.assertEqual(len(opener.requests), 1)

    def test_noncanonical_challenge_rejected(self):
        opener = Opener([{"challenge": "c" * 44}])
        client = OracleDeviceLogin226("https://example.com", opener=opener)
        with self.assertRaises(OracleDeviceLoginError):
            asyncio.run(client.login("android_owner_device_226", Native()))

    def test_whitespace_token_rejected(self):
        opener = Opener([
            {"challenge": base64.urlsafe_b64encode(b"c" * 32).decode("ascii")},
            {"access_token": "t" * 40 + " ", "token_type": "bearer",
             "expires_in_seconds": 900}])
        client = OracleDeviceLogin226("https://example.com", opener=opener)
        with self.assertRaises(OracleDeviceLoginError):
            asyncio.run(client.login("android_owner_device_226", Native()))

    def test_control_character_and_punctuation_tokens_rejected(self):
        challenge = base64.urlsafe_b64encode(b"c" * 32).decode("ascii")
        for token in ("t" * 40 + "\u0000", "t" * 40 + ".", "t" * 40 + ":"):
            with self.subTest(token_suffix=repr(token[-1])):
                opener = Opener([
                    {"challenge": challenge},
                    {"access_token": token, "token_type": "bearer",
                     "expires_in_seconds": 900}])
                client = OracleDeviceLogin226("https://example.com", opener=opener)
                with self.assertRaises(OracleDeviceLoginError):
                    asyncio.run(client.login("android_owner_device_226", Native()))

    def test_missing_native_bridge_never_posts_session(self):
        opener = Opener([{"challenge": base64.urlsafe_b64encode(b"c" * 32).decode("ascii")}])
        client = OracleDeviceLogin226("https://example.com", opener=opener)
        with self.assertRaises(OracleDeviceLoginError):
            asyncio.run(client.login("android_owner_device_226", None))
        self.assertEqual(len(opener.requests), 0)

    def test_bad_native_signature_never_posts_session(self):
        class InvalidNative:
            async def sign_login_challenge(self, device_id, challenge):
                return "bad signature!"
        opener = Opener([{"challenge": base64.urlsafe_b64encode(b"c" * 32).decode("ascii")}])
        client = OracleDeviceLogin226("https://example.com", opener=opener)
        with self.assertRaises(OracleDeviceLoginError):
            asyncio.run(client.login("android_owner_device_226", InvalidNative()))
        self.assertEqual(len(opener.requests), 1)

    def test_bad_session_fails_closed(self):
        opener = Opener([{"challenge": base64.urlsafe_b64encode(b"c" * 32).decode("ascii")},
                         {"access_token": "t" * 48, "token_type": "bearer",
                          "expires_in_seconds": 99999}])
        client = OracleDeviceLogin226("https://example.com", opener=opener)
        with self.assertRaises(OracleDeviceLoginError):
            asyncio.run(client.login("android_owner_device_226", Native()))


if __name__ == "__main__":
    unittest.main()
