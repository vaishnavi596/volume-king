import asyncio
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from secure_dhan_pairing import KEY_NAME, SecureDhanPairing


class MemoryNativeStub:
    def __init__(self):
        self.data = {}
    async def read(self, key):
        return self.data.get(key)
    async def write(self, key, value):
        self.data[key] = value
    async def delete(self, key):
        self.data.pop(key, None)


class SecurePairingTests(unittest.IsolatedAsyncioTestCase):
    async def test_verified_pairing_saves_and_reconnects(self):
        store = MemoryNativeStub()
        async def verify(secret):
            return secret == "valid"
        pairing = SecureDhanPairing(store, verify)
        self.assertTrue((await pairing.connect("valid")).stored)
        self.assertEqual(store.data[KEY_NAME], "valid")
        self.assertTrue((await pairing.reconnect()).connected)
        await pairing.disconnect()
        self.assertNotIn(KEY_NAME, store.data)

    async def test_unverified_pairing_never_saves(self):
        store = MemoryNativeStub()
        async def verify(secret):
            return False
        pairing = SecureDhanPairing(store, verify)
        self.assertFalse((await pairing.connect("wrong")).connected)
        self.assertEqual(store.data, {})

    async def test_network_outage_retains_saved_key(self):
        store = MemoryNativeStub()
        store.data[KEY_NAME] = "valid"
        async def outage(secret):
            raise TimeoutError()
        pairing = SecureDhanPairing(store, outage)
        self.assertFalse((await pairing.reconnect()).connected)
        self.assertEqual(store.data[KEY_NAME], "valid")

    async def test_unavailable_store_does_not_claim_saved(self):
        from secure_credentials import UnavailableCredentialStore
        async def verify(secret):
            return True
        pairing = SecureDhanPairing(UnavailableCredentialStore(), verify)
        outcome = await pairing.connect("valid")
        self.assertTrue(outcome.connected)
        self.assertFalse(outcome.stored)
        self.assertIn("unavailable", outcome.message)

    async def test_connect_network_failure_never_saves(self):
        store = MemoryNativeStub()
        async def outage(secret):
            raise TimeoutError("unreachable")
        outcome = await SecureDhanPairing(store, outage).connect("valid")
        self.assertFalse(outcome.connected)
        self.assertFalse(outcome.stored)
        self.assertEqual(store.data, {})
