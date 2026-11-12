"""Security regression checks for the future native credential-store integration."""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from secure_credentials import (
    DhanSessionRecord,
    SecureStorageUnavailable,
    UnavailableCredentialStore,
)


def test_unavailable_secure_storage_never_persists_secret():
    store = UnavailableCredentialStore()
    assert asyncio.run(store.read("dhan.server_access_key")) is None
    try:
        asyncio.run(store.write("dhan.server_access_key", "example-test-secret"))
    except SecureStorageUnavailable:
        pass
    else:
        raise AssertionError("Secret must not be written without OS secure storage")
    asyncio.run(store.delete("dhan.server_access_key"))
    assert asyncio.run(store.read("dhan.server_access_key")) is None


def test_session_metadata_has_no_secret_field():
    record = DhanSessionRecord("https://example.invalid")
    assert set(vars(record)) == {"server_origin", "provider"}


def test_no_plaintext_dhan_pairing_key_in_preferences():
    """Reject accidental persistence of the pairing key in JSON preferences."""
    source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
    forbidden = (
        'prefs["pairing_key"]',
        "prefs['pairing_key']",
        'prefs["server_access_key"]',
        "prefs['server_access_key']",
        'prefs["server_access"]',
        "prefs['server_access']",
    )
    assert all(pattern not in source for pattern in forbidden)


def test_native_adapter_round_trip_and_explicit_delete():
    from secure_credentials import VerifiedNativeCredentialStore

    class FakeNative:
        def __init__(self):
            self.values = {}

        async def get(self, key):
            return self.values.get(key)

        async def set(self, key, value):
            self.values[key] = value

        async def delete(self, key):
            self.values.pop(key, None)

    async def exercise():
        native = FakeNative()
        store = VerifiedNativeCredentialStore(native)
        await store.write("dhan.server_access_key", "test-only-value")
        assert await store.read("dhan.server_access_key") == "test-only-value"
        await store.delete("dhan.server_access_key")
        assert await store.read("dhan.server_access_key") is None

    asyncio.run(exercise())


def test_native_adapter_fails_closed_without_service():
    from secure_credentials import VerifiedNativeCredentialStore
    try:
        VerifiedNativeCredentialStore(None)
    except SecureStorageUnavailable:
        pass
    else:
        raise AssertionError("Native storage must be mandatory")


def test_native_adapter_rejects_non_string_response():
    from secure_credentials import VerifiedNativeCredentialStore

    class MalformedNative:
        async def get(self, key):
            return {"secret": "unexpected"}

        async def set(self, key, value):
            return None

        async def delete(self, key):
            return None

    async def exercise():
        store = VerifiedNativeCredentialStore(MalformedNative())
        try:
            await store.read("dhan.server_access_key")
        except SecureStorageUnavailable:
            return
        raise AssertionError("Malformed secure storage data must fail closed")

    asyncio.run(exercise())


def test_native_adapter_rejects_empty_credentials():
    from secure_credentials import VerifiedNativeCredentialStore

    class FakeNative:
        async def get(self, key):
            return None

        async def set(self, key, value):
            raise AssertionError("Empty credential reached native storage")

        async def delete(self, key):
            return None

    async def exercise():
        store = VerifiedNativeCredentialStore(FakeNative())
        for invalid in ("", None, 123):
            try:
                await store.write("dhan.server_access_key", invalid)
            except ValueError:
                pass
            else:
                raise AssertionError("Invalid credential was accepted")

    asyncio.run(exercise()
    )


def test_preference_writer_excludes_pairing_and_broker_secrets():
    source = (Path(__file__).resolve().parents[1] / "src" / "main.py").read_text(encoding="utf-8")
    section = source[source.index("    def save():"):source.index("    def txt(", source.index("    def save():"))]
    for name in ("pairing_key", "server_access_key", "server_access",
                 "botking_pairing_key", "dhan_token", "client_secret",
                 "api_key", "api_secret", "access_token", "password", "totp"):
        assert f'"{name}"' in section
    assert "if k not in secret_fields" in section


def test_native_adapter_rejects_explicit_failed_write_and_delete():
    from secure_credentials import VerifiedNativeCredentialStore

    class RejectingNative:
        async def get(self, key):
            return None

        async def set(self, key, value):
            return False

        async def delete(self, key):
            return False

    async def exercise():
        store = VerifiedNativeCredentialStore(RejectingNative())
        for operation in (
            store.write("dhan.server_access_key", "test-only-value"),
            store.delete("dhan.server_access_key"),
        ):
            try:
                await operation
            except SecureStorageUnavailable:
                continue
            raise AssertionError("Native rejection must never be reported as success")

    asyncio.run(exercise())


def test_native_storage_exceptions_do_not_expose_secret_or_native_details():
    from secure_credentials import VerifiedNativeCredentialStore

    class FailingNative:
        async def get(self, key):
            raise RuntimeError("private native detail")

        async def set(self, key, value):
            raise RuntimeError("private native detail " + value)

        async def delete(self, key):
            raise RuntimeError("private native detail")

    async def exercise():
        store = VerifiedNativeCredentialStore(FailingNative())
        actions = (
            store.read("dhan.server_access_key"),
            store.write("dhan.server_access_key", "test-only-secret"),
            store.delete("dhan.server_access_key"),
        )
        for action in actions:
            try:
                await action
            except SecureStorageUnavailable as exc:
                assert "private native detail" not in str(exc)
                assert "test-only-secret" not in str(exc)
                assert exc.__cause__ is None
            else:
                raise AssertionError("Native failure must not report success")

    asyncio.run(exercise())
