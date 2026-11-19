"""Opt-in AndroidKeyStore P-256 device adapter for the V2 signed-login boundary.

JNI availability and native ABI MUST be proven on an actual Flet 0.25.2 APK
before certifying this adapter. Android hardware-backed status is not assumed:
AndroidKeyStore may be software-backed; owner enrollment remains server-side.
This module never exports a private key or persists a bearer/credential.
"""
import hashlib

from app_keystore_login_binding import AndroidKeystoreLoginBinding
from app_p256_login import _device_id_ok, LOGIN_CONTEXT
from secure_https_reader import FeedError

_ALIAS_PREFIX = "botking_v2_device_"


def _alias_for_device(device_id):
    if not _device_id_ok(device_id):
        raise FeedError("Approved V2 device identity required")
    return _ALIAS_PREFIX + hashlib.sha256(device_id.encode("ascii")).hexdigest()


def _safe_byte_string(java_bytes):
    """Java signed byte[] -> immutable unsigned bytes, with a strict limit."""
    try:
        values = list(java_bytes)
        if len(values) > 1024 or any(
                type(value) is not int or value < -128 or value > 255
                for value in values):
            raise ValueError("Invalid signed Java byte array")
        # Java byte[] is signed, but some JNI adapters expose unsigned 0..255.
        # Reject values outside BOTH representations instead of masking them.
        result = bytes(value if value >= 0 else value + 256 for value in values)
    except (TypeError, ValueError, OverflowError):
        raise FeedError("Android Keystore byte encoding unavailable") from None
    return result


class AndroidNativeP256Provider:
    """Android native KEYSTORE ONLY. No file/private-key fallback allowed."""

    def __init__(self, device_id, *, autoclass=None):
        self.device_id = device_id
        self.alias = _alias_for_device(device_id)
        if autoclass is None:
            try:
                from jnius import autoclass as native_autoclass
            except (ImportError, OSError, RuntimeError):
                raise FeedError("Android Keystore native runtime not installed") from None
            autoclass = native_autoclass
        if not callable(autoclass):
            raise FeedError("Android Keystore native runtime unavailable")
        try:
            self._KeyStore = autoclass("java.security.KeyStore")
            self._KeyPairGenerator = autoclass("java.security.KeyPairGenerator")
            self._ECGenParameterSpec = autoclass("java.security.spec.ECGenParameterSpec")
            self._KeyProperties = autoclass("android.security.keystore.KeyProperties")
            self._Builder = autoclass(
                "android.security.keystore.KeyGenParameterSpec$Builder")
            self._Signature = autoclass("java.security.Signature")
            self._store = self._KeyStore.getInstance("AndroidKeyStore")
            self._store.load(None)
        except Exception:
            raise FeedError("Android Keystore runtime unavailable") from None

    def _load_existing_public(self):
        try:
            if not self._store.containsAlias(self.alias):
                return None
            cert = self._store.getCertificate(self.alias)
            if cert is None:
                raise ValueError("Missing certificate")
            return _safe_byte_string(cert.getPublicKey().getEncoded())
        except Exception:
            raise FeedError("Android device public key unavailable") from None

    def ensure_public_spki(self):
        """Explicit owner-initiated enrollment key creation, never per login."""
        existing = self._load_existing_public()
        if existing is not None:
            return existing
        try:
            builder = self._Builder(self.alias, self._KeyProperties.PURPOSE_SIGN)
            builder.setAlgorithmParameterSpec(self._ECGenParameterSpec("secp256r1"))
            builder.setDigests(self._KeyProperties.DIGEST_SHA256)
            builder.setUserAuthenticationRequired(False)
            generator = self._KeyPairGenerator.getInstance("EC", "AndroidKeyStore")
            generator.initialize(builder.build())
            generator.generateKeyPair()
        except Exception:
            raise FeedError("Android device key creation unavailable") from None
        public = self._load_existing_public()
        if public is None:
            raise FeedError("Android device public key unavailable")
        return public

    def public_spki(self):
        public = self._load_existing_public()
        if public is None:
            raise FeedError("Device enrollment key not created")
        return public

    def sign_login_message(self, message):
        # Guard at BOTH native entry and public binding. Python callers
        # must not use this method as a generic AndroidKeyStore signing oracle.
        prefix = LOGIN_CONTEXT + self.device_id.encode("ascii") + b"\x00"
        if (type(message) is not bytes
                or len(message) != len(prefix) + 32
                or not message.startswith(prefix)):
            raise FeedError("Unsupported native signing input")
        try:
            key = self._store.getKey(self.alias, None)
            if key is None:
                raise ValueError("Missing enrolled key")
            signature = self._Signature.getInstance("SHA256withECDSA")
            signature.initSign(key)
            signature.update(message)
            return _safe_byte_string(signature.sign())
        except Exception:
            raise FeedError("Android device signature unavailable") from None

    def binding(self):
        """Validate public SPKI before exposing the protocol-specific signer."""
        return AndroidKeystoreLoginBinding(
            self.device_id, self.public_spki, self.sign_login_message)
