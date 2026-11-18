"""V2-only in-memory master-approved device enrollment with P-256 key proof.

Offline staging prototype, NOT an exposed HTTP endpoint. Production requires
one atomic shared transaction, audited master approval, TLS and stored trust
anchors. No Dhan credentials, no OAuth renewal and no real trading.
"""
import hashlib
import time
from dataclasses import dataclass
from math import isfinite

from .device_policy import ALLOWED_FEEDS, DeviceRegistry, valid_id
from .device_sessions import DeviceSessionGateway, SessionDenied
from .device_verifier import DeviceProof, P256ChallengeVerifier

@dataclass
class _Pending:
    device_id: str
    der: bytes
    feeds: frozenset
    expires_at: float
    verifier: P256ChallengeVerifier

class EnrollmentManager:
    """Master session must be valid at approval AND at final enrollment."""

    def __init__(self, sessions, registry, *, clock=None, ttl_seconds=120):
        if (not isinstance(sessions, DeviceSessionGateway)
                or not isinstance(registry, DeviceRegistry)
                or type(ttl_seconds) is not int or not 20 <= ttl_seconds <= 120):
            raise ValueError("Invalid enrollment coordinator")
        self._sessions = sessions
        self._registry = registry
        self._clock = clock or time.monotonic
        self._ttl = ttl_seconds
        self._pending = {}

    @staticmethod
    def fingerprint(der):
        if type(der) is not bytes:
            raise SessionDenied("Invalid device key")
        return hashlib.sha256(der).hexdigest()

    def request(self, master_session, device_id, der, feeds):
        master_id = self._sessions.identity(master_session)
        self._registry._require_master(master_id)
        if (not valid_id(device_id) or device_id == self._registry.master_id
                or device_id in self._registry.grants
                or type(feeds) not in (list, tuple, set, frozenset)):
            raise SessionDenied("Invalid new device enrollment")
        grants = frozenset(feeds)
        if not grants or not grants.issubset(ALLOWED_FEEDS):
            raise SessionDenied("Invalid device feed grant")
        if len(self._registry.grants) >= 3:
            raise SessionDenied("Device capacity reached")
        # Registration validates strict P-256 DER public key before creating
        # the pending object; no raw key is considered trusted until proof.
        if type(der) is not bytes:
            raise SessionDenied("Invalid device public key")
        try:
            verifier = P256ChallengeVerifier(
                {device_id: der}, clock=self._clock,
                ttl_seconds=min(self._ttl, 120))
        except ValueError:
            raise SessionDenied("Invalid device public key") from None
        now = self._clock()
        if type(now) not in (int, float) or not isfinite(now):
            raise SessionDenied("Invalid enrollment clock")
        # Same device request supersedes previous: prevents stale approvals.
        challenge = verifier.challenge(device_id)
        self._pending[device_id] = _Pending(
            device_id, der, grants, now + self._ttl, verifier)
        return challenge, self.fingerprint(der)

    def complete(self, master_session, proof):
        # Verify master before taking any effect. The pending challenge must
        # be consumed even if the signature is wrong.
        master_id = self._sessions.identity(master_session)
        self._registry._require_master(master_id)
        if not isinstance(proof, DeviceProof):
            raise SessionDenied("Invalid enrollment proof")
        pending = self._pending.pop(proof.device_id, None)
        if pending is None or self._clock() >= pending.expires_at:
            raise SessionDenied("Enrollment missing or expired")
        if proof.device_id != pending.device_id:
            raise SessionDenied("Device mismatch")
        pending.verifier.verify(proof)
        # No effect until possession proof succeeds and current master
        # permission and device capacity remain valid.
        self._registry.assign(master_id, proof.device_id, pending.feeds)
        return pending.der

    def abort(self, master_session, device_id):
        master_id = self._sessions.identity(master_session)
        self._registry._require_master(master_id)
        self._pending.pop(device_id, None)
