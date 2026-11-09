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
