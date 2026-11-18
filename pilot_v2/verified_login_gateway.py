"""V2 trusted P-256 proof -> durable, restricted, revocable device session.

No HTTP endpoints and no remote enrollment. The verifier must be populated
only with keys approved by the real owner, not from a mobile login payload.
P256ChallengeVerifier is in-memory test-only; DurableP256ChallengeVerifier\nuses single-host SQLite atomic nonce consumption. Neither offers HTTP routes.
"""
from .device_sessions import SessionDenied
from .device_verifier import P256ChallengeVerifier, DeviceProof
from .durable_challenges import DurableP256ChallengeVerifier
from .durable_device_sessions import DurableDeviceSessions

class VerifiedLoginGateway:
    def __init__(self, verifier, sessions):
        if not isinstance(verifier, (P256ChallengeVerifier, DurableP256ChallengeVerifier)) or not isinstance(
                sessions, DurableDeviceSessions):
            raise ValueError("Trusted P-256 proof verifier and durable sessions required")
        self._verifier = verifier
        self._sessions = sessions

    def challenge(self, device_id):
        return self._verifier.challenge(device_id)

    def login(self, proof):
        # No role/client-provided device identifier is authorized unless its
        # signed single-use challenge verifies against a pre-enrolled P-256 key.
        if not isinstance(proof, DeviceProof):
            raise SessionDenied("P-256 device proof required")
        identity = self._verifier.verify(proof)
        return self._sessions.issue_verified(identity)

    def read_feed(self, bearer, feed):
        """Caller may only use returned authorized identity for data filtering."""
        return self._sessions.authorize(bearer, feed)

    def master_grant(self, bearer, device_id, feeds, *, enabled=True):
        return self._sessions.master_grant(bearer, device_id, feeds, enabled=enabled)

    def master_revoke(self, bearer, device_id):
        return self._sessions.revoke(bearer, device_id)

    def logout(self, bearer):
        return self._sessions.logout(bearer)
