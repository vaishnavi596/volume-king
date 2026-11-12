"""Fail-closed Flet/native Android Keystore bridge contract for BOT KING 226.

No native plugin is bundled yet. This module never fabricates biometric success,
exports a private key, or stores a PIN in Python preferences.
"""
import base64
import inspect
from dataclasses import dataclass
from cryptography.hazmat.primitives.serialization import load_der_public_key
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature


class AndroidAuthUnavailable(RuntimeError):
    pass


@dataclass(frozen=True)
class DeviceKeyRegistration:
    device_id: str
    public_key: str  # p256:<base64url DER SubjectPublicKeyInfo>


class AndroidDeviceAuthBridge:
    """Native service must provide AndroidKeyStore + OS BiometricPrompt."""

    def __init__(self, native_service):
        methods = ("generate_p256_key", "sign_challenge_with_biometric")
        if native_service is None or not all(
            callable(getattr(native_service, method, None)) for method in methods
        ):
            raise AndroidAuthUnavailable("Verified Android native auth bridge unavailable")
        self._native = native_service

    async def register_key(self, device_id):
        if (not isinstance(device_id, str) or not 16 <= len(device_id) <= 128
                or not all(ch.isascii() and (ch.isalnum() or ch in "_-") for ch in device_id)):
            raise ValueError("Invalid device ID")
        result = self._native.generate_p256_key(device_id)
        if not inspect.isawaitable(result):
            raise AndroidAuthUnavailable("Native bridge must be asynchronous")
        public_key = await result
        if not isinstance(public_key, str) or len(public_key) > 512:
            raise AndroidAuthUnavailable("Invalid Android public key")
        try:
            raw = base64.b64decode(public_key, altchars=b"-_", validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise AndroidAuthUnavailable("Invalid Android public key encoding") from exc
        if not 80 <= len(raw) <= 160:
            raise AndroidAuthUnavailable("Invalid P-256 public key length")
        try:
            key = load_der_public_key(raw)
        except (ValueError, TypeError) as exc:
            raise AndroidAuthUnavailable("Invalid Android public key DER") from exc
        if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(key.curve, ec.SECP256R1):
            raise AndroidAuthUnavailable("Android public key must use P-256")
        return DeviceKeyRegistration(device_id, "p256:" + public_key)

    async def sign_login_challenge(self, device_id, challenge):
        if (not isinstance(device_id, str) or not 16 <= len(device_id) <= 128
                or not all(ch.isascii() and (ch.isalnum() or ch in "_-") for ch in device_id)):
            raise ValueError("Invalid device ID")
        if not isinstance(challenge, str) or len(challenge) != 44:
            raise ValueError("Invalid server challenge")
        try:
            raw = base64.b64decode(challenge, altchars=b"-_", validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise ValueError("Invalid server challenge") from exc
        if len(raw) != 32 or base64.urlsafe_b64encode(raw).decode("ascii") != challenge:
            raise ValueError("Invalid server challenge")
        result = self._native.sign_challenge_with_biometric(device_id, challenge)
        if not inspect.isawaitable(result):
            raise AndroidAuthUnavailable("Native biometric signing unavailable")
        signature = await result
        if not isinstance(signature, str) or len(signature) > 256:
            raise AndroidAuthUnavailable("Invalid native signature")
        try:
            encoded = base64.b64decode(signature, altchars=b"-_", validate=True)
        except (ValueError, base64.binascii.Error) as exc:
            raise AndroidAuthUnavailable("Invalid native signature encoding") from exc
        try:
            r, s = decode_dss_signature(encoded)
        except ValueError as exc:
            raise AndroidAuthUnavailable("Invalid native P-256 signature DER") from exc
        if not (1 <= r < 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551 and 1 <= s < 0xFFFFFFFF00000000FFFFFFFFFFFFFFFFBCE6FAADA7179E84F3B9CAC2FC632551):
            raise AndroidAuthUnavailable("Invalid native P-256 signature")
        return signature
