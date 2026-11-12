"""BOT KING 226 offline device login coordinator.

Not mounted as FastAPI routes. The enrollment and challenge transports must
be owner-authenticated and rate-limited before production deployment.
"""
import re
from .device_proof_226 import ChallengeStore, DeviceProofError, verify_device_signature
from .device_registry_226 import DEVICE_ID, DeviceRegistryError


class DeviceLoginError(ValueError):
    pass


class DeviceLoginCoordinator:
    def __init__(self, registry, challenges=None):
        self.registry = registry
        self.challenges = challenges or ChallengeStore()

    def begin(self, device_id):
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            raise DeviceLoginError("Invalid device")
        key = self.registry.active_public_key(device_id)
        if key is None:
            raise DeviceLoginError("Device not enrolled or revoked")
        return self.challenges.issue(device_id)

    def complete(self, device_id, challenge, signature):
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            raise DeviceLoginError("Invalid device")
        # Consume before verification: a failed proof cannot be retried/replayed.
        if not self.challenges.consume(device_id, challenge):
            raise DeviceLoginError("Challenge expired or already used")
        key = self.registry.active_public_key(device_id)
        if key is None:
            raise DeviceLoginError("Device not enrolled or revoked")
        try:
            valid = verify_device_signature(key, challenge, signature)
        except DeviceProofError as exc:
            raise DeviceLoginError("Invalid device proof") from exc
        if not valid:
            raise DeviceLoginError("Invalid device proof")
        return self.registry.issue_session(device_id, device_proof_verified=True)
