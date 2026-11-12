"""Fail-closed credential persistence contract for BOT KING.

The current Flet 0.25.2 runtime has no verified Android Keystore bridge.
Never replace this adapter with plaintext preferences, a JSON file, or
reversible encryption with a key bundled in the APK.
"""
from dataclasses import dataclass
from typing import Protocol


class SecureStorageUnavailable(RuntimeError):
    """Native OS-backed credential storage is not installed."""


class SecureCredentialStore(Protocol):
    async def read(self, key: str) -> str | None: ...
    async def write(self, key: str, value: str) -> None: ...
    async def delete(self, key: str) -> None: ...


@dataclass(frozen=True)
class DhanSessionRecord:
    """Non-secret metadata; do not serialize the server access key here."""
    server_origin: str
    provider: str = "Dhan"



def origin_scoped_pairing_key(origin: str) -> str:
    """Non-secret Keystore alias scoped to one validated HTTPS server origin."""
    import hashlib
    from server_feed import server_origin

    normalized = server_origin(origin)
    # Hash the origin to keep hostnames out of storage aliases and logs.
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return "botking.pairing.v1." + digest


class UnavailableCredentialStore:
    """Safe fallback: never persist or silently pretend a secret was saved."""

    async def read(self, key: str) -> str | None:
        return None

    async def write(self, key: str, value: str) -> None:
        raise SecureStorageUnavailable(
            "Android Keystore-backed credential storage is required"
        )

    async def delete(self, key: str) -> None:
        return None


class VerifiedNativeCredentialStore:
    """Adapter for an already-verified native Keystore service.

    The service must implement async get/set/delete and be registered with
    the Flet runtime. Merely installing a Python package is insufficient.
    No filesystem fallback is allowed.
    """

    def __init__(self, native_service):
        if native_service is None or not all(
            callable(getattr(native_service, method, None))
            for method in ("get", "set", "delete")
        ):
            raise SecureStorageUnavailable("Native secure storage service missing")
        self._native = native_service

    async def read(self, key: str) -> str | None:
        try:
            value = await self._native.get(key)
        except Exception:
            raise SecureStorageUnavailable("Native secure storage read failed") from None
        if value is not None and not isinstance(value, str):
            raise SecureStorageUnavailable("Unexpected native storage response")
        return value

    async def write(self, key: str, value: str) -> None:
        if not isinstance(value, str) or not value:
            raise ValueError("Cannot store an empty credential")
        try:
            result = await self._native.set(key, value)
        except Exception:
            raise SecureStorageUnavailable("Native secure storage write failed") from None
        if result is False:
            raise SecureStorageUnavailable("Native secure storage rejected write")

    async def delete(self, key: str) -> None:
        try:
            result = await self._native.delete(key)
        except Exception:
            raise SecureStorageUnavailable("Native secure storage delete failed") from None
        if result is False:
            raise SecureStorageUnavailable("Native secure storage rejected delete")


class OriginScopedPairingStore:
    """Bind a pairing secret to an HTTPS origin, never to a global alias."""

    def __init__(self, credentials: SecureCredentialStore, origin: str):
        self._credentials = credentials
        self._key = origin_scoped_pairing_key(origin)

    async def read(self) -> str | None:
        return await self._credentials.read(self._key)

    async def write(self, value: str) -> None:
        await self._credentials.write(self._key, value)

    async def delete(self) -> None:
        await self._credentials.delete(self._key)


