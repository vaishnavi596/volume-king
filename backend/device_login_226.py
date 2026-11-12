"""BOT KING 226 offline device login coordinator.

Not mounted as FastAPI routes. The enrollment and challenge transports must
be owner-authenticated and rate-limited before production deployment.
"""
import re
from .device_proof_226 import ChallengeStore, DeviceProofError, verify_device_signature, verify_android_p256_signature
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
        if not self.registry.login_allowed(device_id):
            raise DeviceLoginError("Device temporarily locked")
        key = self.registry.active_public_key(device_id)
        if key is None:
            raise DeviceLoginError("Device not enrolled or revoked")
        return self.registry.issue_challenge(device_id)

    def complete(self, device_id, challenge, signature):
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            raise DeviceLoginError("Invalid device")
        if not self.registry.login_allowed(device_id):
            raise DeviceLoginError("Device temporarily locked")
        # Consume before verification: a failed proof cannot be retried/replayed.
        if not self.registry.consume_challenge(device_id, challenge):
            self.registry.record_login_failure(device_id)
            raise DeviceLoginError("Challenge expired or already used")
        key = self.registry.active_public_key(device_id)
        if key is None:
            raise DeviceLoginError("Device not enrolled or revoked")
        try:
            valid = (verify_android_p256_signature(key[5:], challenge, signature)
                     if key.startswith("p256:") else
                     verify_device_signature(key, challenge, signature))
        except DeviceProofError as exc:
            self.registry.record_login_failure(device_id)
            raise DeviceLoginError("Invalid device proof") from exc
        if not valid:
            self.registry.record_login_failure(device_id)
            raise DeviceLoginError("Invalid device proof")
        if not self.registry.clear_login_failures(device_id):
            raise DeviceLoginError("Device temporarily locked")
        return self.registry.issue_session(device_id, device_proof_verified=True)
