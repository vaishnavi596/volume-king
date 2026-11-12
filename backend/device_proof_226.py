"""BOT KING 226 Ed25519 device challenge verification.

Standalone security component only; production enrollment endpoints remain OFF.
Android generates a non-exportable signing key in Android Keystore.
"""
import base64
import secrets
import time

try:
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    from cryptography.hazmat.primitives.asymmetric import ec
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.exceptions import InvalidSignature
except ImportError:
    Ed25519PublicKey = None
    ec = None
    hashes = None
    serialization = None
    InvalidSignature = Exception


class DeviceProofError(ValueError):
    pass


def _decode(value, expected_bytes):
    if not isinstance(value, str) or not value or len(value) > 256:
        raise DeviceProofError("Invalid device proof encoding")
    try:
        raw = base64.b64decode(value, altchars=b"-_", validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise DeviceProofError("Invalid device proof encoding") from exc
    if len(raw) != expected_bytes:
        raise DeviceProofError("Invalid device proof length")
    return raw


def new_challenge():
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")


def verify_device_signature(public_key_b64, challenge_b64, signature_b64):
    if Ed25519PublicKey is None:
        raise DeviceProofError("Cryptographic verification unavailable")
    key = _decode(public_key_b64, 32)
    challenge = _decode(challenge_b64, 32)
    signature = _decode(signature_b64, 64)
    try:
        Ed25519PublicKey.from_public_bytes(key).verify(
            signature, b"BOTKING226:DEVICE-AUTH:v1:" + challenge
        )
    except (InvalidSignature, ValueError) as exc:
        return False
    return True


def verify_android_p256_signature(public_key_der_b64, challenge_b64, signature_der_b64):
    """Android Keystore-compatible EC P-256 SHA256withECDSA proof.

    Public key is DER SubjectPublicKeyInfo, signature is DER ECDSA.
    """
    if ec is None:
        raise DeviceProofError("Cryptographic verification unavailable")
    if not isinstance(public_key_der_b64, str) or len(public_key_der_b64) > 512:
        raise DeviceProofError("Invalid device key encoding")
    if not isinstance(signature_der_b64, str) or len(signature_der_b64) > 256:
        raise DeviceProofError("Invalid signature encoding")
    try:
        key_bytes = base64.b64decode(public_key_der_b64, altchars=b"-_", validate=True)
        sig_bytes = base64.b64decode(signature_der_b64, altchars=b"-_", validate=True)
        public = serialization.load_der_public_key(key_bytes)
    except (ValueError, TypeError, base64.binascii.Error) as exc:
        raise DeviceProofError("Invalid device proof encoding") from exc
    if not isinstance(public, ec.EllipticCurvePublicKey) or not isinstance(public.curve, ec.SECP256R1):
        raise DeviceProofError("Unsupported device signing key")
    if not 8 <= len(sig_bytes) <= 80:
        raise DeviceProofError("Invalid signature length")
    challenge = _decode(challenge_b64, 32)
    try:
        public.verify(sig_bytes, b"BOTKING226:DEVICE-AUTH:v1:" + challenge,
                      ec.ECDSA(hashes.SHA256()))
    except (InvalidSignature, ValueError):
        return False
    return True


class ChallengeStore:
    """One-use challenges. Production needs durable/shared atomic storage."""

    def __init__(self, clock=None, ttl_seconds=120):
        if type(ttl_seconds) is not int or not 30 <= ttl_seconds <= 300:
            raise DeviceProofError("Invalid challenge lifetime")
        self.clock = clock or time.monotonic
        self.ttl_seconds = ttl_seconds
        self._pending = {}

    def issue(self, device_id):
        if not isinstance(device_id, str) or len(device_id) < 16:
            raise DeviceProofError("Invalid device ID")
        challenge = new_challenge()
        self._pending[(device_id, challenge)] = self.clock() + self.ttl_seconds
        return challenge

    def consume(self, device_id, challenge):
        expiry = self._pending.pop((device_id, challenge), None)
        return expiry is not None and self.clock() < expiry
