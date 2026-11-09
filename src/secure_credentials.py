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
