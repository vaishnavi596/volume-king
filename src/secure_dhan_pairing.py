"""Fail-closed secure Dhan pairing orchestration.

This is independent of the Android UI and requires a verified native store.
A successful transport call alone never implies an authenticated live feed.
"""
from dataclasses import dataclass
from typing import Awaitable, Callable

from secure_credentials import SecureCredentialStore

KEY_NAME = "botking.dhan.server_access.v1"


@dataclass(frozen=True)
class PairingOutcome:
    connected: bool
    message: str
    stored: bool = False


class SecureDhanPairing:
    def __init__(self, store: SecureCredentialStore, verify: Callable[[str], Awaitable[bool]]):
        self._store = store
        self._verify = verify

    async def connect(self, secret: str) -> PairingOutcome:
        if not isinstance(secret, str) or not secret.strip():
            return PairingOutcome(False, "Server access key required")
        secret = secret.strip()
        try:
            verified = await self._verify(secret)
        except Exception:
            return PairingOutcome(False, "Dhan verification unavailable; nothing saved")
        if not verified:
            return PairingOutcome(False, "Dhan status and NIFTY quote not verified")
        try:
            await self._store.write(KEY_NAME, secret)
        except Exception:
            # Never pretend secure persistence succeeded.
            return PairingOutcome(True, "Connected for this session; secure save unavailable", False)
        return PairingOutcome(True, "Verified and securely saved", True)

    async def reconnect(self) -> PairingOutcome:
        try:
            secret = await self._store.read(KEY_NAME)
        except Exception:
            return PairingOutcome(False, "Secure storage unavailable")
        if not secret:
            return PairingOutcome(False, "No securely saved pairing")
        try:
            verified = await self._verify(secret)
        except Exception:
            # Network interruption must not destroy saved credentials.
            return PairingOutcome(False, "Server unavailable; will need retry")
        if not verified:
            return PairingOutcome(False, "Saved pairing not verified; reconnect required")
        return PairingOutcome(True, "Reconnected after live verification", True)

    async def disconnect(self) -> None:
        # Caller must also disconnect the in-memory market feed.
        await self._store.delete(KEY_NAME)
