"""Future Android Keystore to P-256 login boundary; no native module loaded.

The platform callbacks must be independently installed from a reviewed
non-exportable Android Keystore implementation; Python cannot attest that.
The only public value crossing enrollment is canonical P-256 SPKI DER.
Only the protocol-specific signed challenge may reach the native signer.
"""
import hashlib
import hmac
from app_p256_login import LOGIN_CONTEXT, V2P256LoginHTTPSClient, _device_id_ok
from app_p256_public_key import export_validated_p256_public_spki
from app_p256_signature import is_canonical_p256_der_signature
from secure_https_reader import FeedError


class AndroidKeystoreLoginBinding:
    def __init__(self, device_id, export_public_spki, sign_message):
        if not _device_id_ok(device_id) or not callable(sign_message):
            raise FeedError("Approved device identifier and native signer required")
        try:
            public = export_validated_p256_public_spki(export_public_spki)
        except ValueError:
            raise FeedError("Approved public P-256 Keystore key unavailable") from None
        self._device_id = device_id
        self._public = public
        self._export_public_spki = export_public_spki
        self._sign_message = sign_message

    def _confirmed_public(self):
        """Re-check key identity for every enrollment/read/sign operation."""
        try:
            current = export_validated_p256_public_spki(self._export_public_spki)
        except ValueError:
            raise FeedError("Native device public key unavailable") from None
        if not hmac.compare_digest(current, self._public):
            raise FeedError("Native device key changed; enrollment required")
        return current

    def public_spki_for_owner_enrollment(self):
        """Public key only; actual Master must approve enrollment server-side."""
        return self._confirmed_public()

    def public_key_fingerprint_sha256(self):
        """Comparison checksum only: never attestation or authorization."""
        return hashlib.sha256(self._confirmed_public()).hexdigest()

    def sign_login_challenge(self, message):
        prefix = LOGIN_CONTEXT + self._device_id.encode("ascii") + b"\x00"
        if (type(message) is not bytes or
                len(message) != len(prefix) + 32 or not message.startswith(prefix)):
            raise FeedError("Unsupported device login signing operation")
        # A replaced native key must not sign under a previous enrollment.
        self._confirmed_public()
        try:
            signature = self._sign_message(message)
        except Exception:
            raise FeedError("Native device login signature unavailable") from None
        if not is_canonical_p256_der_signature(signature):
            raise FeedError("Invalid native P-256 login signature")
        return signature

    def login_client(self, approved_https_origin, *, opener=None, timeout=10):
        """Fail closed on a replaced key before creating a network client.

        This is a local preflight, not native attestation or owner approval.
        Actual sign-time verification is independently repeated.
        """
        self._confirmed_public()
        return V2P256LoginHTTPSClient(
            approved_https_origin, self._device_id, self.sign_login_challenge,
            opener=opener, timeout=timeout)
