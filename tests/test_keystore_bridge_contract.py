"""Contract tests for the experimental Flet native Keystore adapter.

These do not prove device-backed Android Keystore persistence.
"""
import asyncio
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from keystore_control import KeystoreControl
from secure_credentials import SecureStorageUnavailable, VerifiedNativeCredentialStore


class MockNative(KeystoreControl):
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    async def invoke_method_async(self, method, args, wait_for_result=False):
        self.calls.append((method, args, wait_for_result))
        return self.responses.get(method)


class KeystoreBridgeContractTests(unittest.TestCase):
    def test_roundtrip_method_contract(self):
        async def run():
            native = MockNative({"get": "secret", "set": "1", "delete": "1"})
            store = VerifiedNativeCredentialStore(native)
            key = "botking.dhan.server_access.v1"
            await store.write(key, "secret")
            self.assertEqual(await store.read(key), "secret")
            await store.delete(key)
            self.assertEqual([c[0] for c in native.calls], ["set", "get", "delete"])
            self.assertTrue(all(c[2] for c in native.calls))
        asyncio.run(run())

    def test_failed_native_write_is_not_reported_as_saved(self):
        async def run():
            native = MockNative({"set": None})
            with self.assertRaises(SecureStorageUnavailable):
                await VerifiedNativeCredentialStore(native).write(
                    "botking.dhan.server_access.v1", "secret"
                )
        asyncio.run(run())

    def test_unknown_key_is_rejected_before_native_call(self):
        async def run():
            native = MockNative()
            with self.assertRaises(ValueError):
                await native.set("other.key", "secret")
            self.assertEqual(native.calls, [])
        asyncio.run(run())


if __name__ == "__main__":
    unittest.main()
