"""Isolated V2 opaque device sessions; read-only and NO HTTP/Oracle access.

All identity proof must come from a trusted server-side verifier. Never trust
client-supplied device_id, master flags or access-token claims.
"""
import hashlib
import secrets
import time
from dataclasses import dataclass

from .device_policy import DeviceRegistry, DevicePolicyError, valid_id

class SessionDenied(PermissionError):
    pass

@dataclass(frozen=True)
class VerifiedDevice:
    """Only a trusted server-side verifier may assert this identity."""
    device_id: str

    def __post_init__(self):
        if not valid_id(self.device_id):
            raise ValueError("Invalid verified device identity")

@dataclass(frozen=True)
class _StoredSession:
    device_id: str
    expires_at: float

class DeviceSessionGateway:
    """In-memory prototype. Replace with atomic, shared server-side store later.

    verify_proof(proof) must verify real cryptographic challenge response and
    independently return VerifiedDevice. Mock verifiers are ONLY for offline tests.
    """

    def __init__(self, registry, verify_proof, *, clock=None, ttl_seconds=900):
        if not isinstance(registry, DeviceRegistry) or not callable(verify_proof):
            raise ValueError("Verified identity provider and policy registry required")
        if type(ttl_seconds) is not int or not 30 <= ttl_seconds <= 3600:
            raise ValueError("Invalid session lifetime")
        self._registry = registry
        self._verify_proof = verify_proof
        self._clock = clock or time.monotonic
        self._ttl = ttl_seconds
        self._sessions = {}

    @staticmethod
    def _digest(token):
        if type(token) is not str or not 40 <= len(token) <= 160:
            raise SessionDenied("Invalid device session")
        return hashlib.sha256(token.encode("ascii", "strict")).hexdigest()

    def issue(self, proof):
        try:
            identity = self._verify_proof(proof)
        except (TypeError, ValueError):
            # Malformed or unhashable proof payloads are authentication
            # denials, not an unhandled server exception.
            raise SessionDenied("Cryptographic device proof not verified") from None
        if not isinstance(identity, VerifiedDevice):
            raise SessionDenied("Cryptographic device proof not verified")
        grant = self._registry.grants.get(identity.device_id)
        if not grant or not grant.enabled:
            raise SessionDenied("Device not authorized")
        self._purge()
        # A new successful login invalidates prior sessions for this device.
        for key, row in tuple(self._sessions.items()):
            if row.device_id == identity.device_id:
                del self._sessions[key]
        token = secrets.token_urlsafe(48)
        self._sessions[self._digest(token)] = _StoredSession(
            identity.device_id, self._clock() + self._ttl)
        return token

    def identity(self, token):
        try:
            key = self._digest(token)
        except (UnicodeError, SessionDenied):
            raise SessionDenied("Invalid device session") from None
        row = self._sessions.get(key)
        if row is None or self._clock() >= row.expires_at:
            self._sessions.pop(key, None)
            raise SessionDenied("Session expired or revoked")
        grant = self._registry.grants.get(row.device_id)
        if not grant or not grant.enabled:
            self._sessions.pop(key, None)
            raise SessionDenied("Device disabled or removed")
        return row.device_id

    def check_feed(self, token, feed):
        device_id = self.identity(token)
        if not self._registry.can_access(device_id, feed):
            raise SessionDenied("This device is not permitted to read this feed")
        return device_id

    def assign(self, master_token, device_id, feeds, *, enabled=True):
        master_id = self.identity(master_token)
        self._registry.assign(master_id, device_id, feeds, enabled=enabled)
        if not enabled:
            self._revoke_device_tokens(device_id)

    def revoke(self, master_token, device_id):
        master_id = self.identity(master_token)
        self._registry.revoke(master_id, device_id)
        self._revoke_device_tokens(device_id)

    def logout(self, token):
        try:
            self._sessions.pop(self._digest(token), None)
        except (UnicodeError, SessionDenied):
            pass

    def _revoke_device_tokens(self, device_id):
        for key, row in tuple(self._sessions.items()):
            if row.device_id == device_id:
                del self._sessions[key]

    def _purge(self):
        now = self._clock()
        for key, row in tuple(self._sessions.items()):
            if now >= row.expires_at or row.device_id not in self._registry.grants:
                del self._sessions[key]
