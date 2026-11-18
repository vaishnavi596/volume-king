"""Isolated V2 P-256 device challenge verifier (no HTTP, credentials or Oracle).

This verifies signatures from *already trusted/provisioned* device public keys.
Actual onboarding must authenticate the owner and register Android Keystore
public keys in a durable server-side store before this is used over HTTP.
"""
import base64
import secrets
import time
from dataclasses import dataclass
from math import isfinite

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .device_policy import valid_id
from .device_sessions import VerifiedDevice, SessionDenied

CONTEXT = b"BOT-KING-V2-DEVICE-LOGIN\x00"

def encode_b64(data):
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")

def decode_b64(text, *, limit):
    if type(text) is not str or not 1 <= len(text) <= limit or any(
            c not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
            for c in text):
        raise SessionDenied("Invalid device proof encoding")
    try:
        data = base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    except (ValueError, base64.binascii.Error):
        raise SessionDenied("Invalid device proof encoding") from None
    if encode_b64(data) != text:
        raise SessionDenied("Noncanonical device proof encoding")
    return data

@dataclass(frozen=True)
class DeviceProof:
    device_id: str
    challenge: str
    signature: str

class P256ChallengeVerifier:
    """In-memory nonce store with one live challenge per trusted device.

    A real server must enforce atomic nonce consumption in a shared store,
    HTTPS, client rate limits, key registration authorization and audit logs.
    """

    def __init__(self, trusted_public_keys, *, clock=None, ttl_seconds=60):
        if type(trusted_public_keys) is not dict or type(ttl_seconds) is not int or not (
                10 <= ttl_seconds <= 120):
            raise ValueError("Invalid trusted key store or challenge TTL")
        self._keys = {}
        for device_id, der in trusted_public_keys.items():
            if not valid_id(device_id) or type(der) is not bytes or len(der) > 512:
                raise ValueError("Invalid trusted device enrollment")
            try:
                key = serialization.load_der_public_key(der)
            except (ValueError, TypeError):
                raise ValueError("Invalid enrolled public key") from None
            if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(
                    key.curve, ec.SECP256R1):
                raise ValueError("Expected P-256 enrolled public key")
            self._keys[device_id] = key
        self._clock = clock or time.monotonic
        self._ttl = ttl_seconds
        self._pending = {}

    def challenge(self, device_id):
        if type(device_id) is not str or device_id not in self._keys:
            raise SessionDenied("Unknown device")
        now = self._clock()
        if type(now) not in (int, float) or not isfinite(now):
            raise SessionDenied("Invalid challenge clock")
        nonce = encode_b64(secrets.token_bytes(32))
        self._pending[device_id] = (nonce, now + self._ttl)
        return nonce

    @staticmethod
    def signed_message(device_id, nonce):
        if not valid_id(device_id) or type(nonce) is not str:
            raise SessionDenied("Invalid signed challenge")
        raw = decode_b64(nonce, limit=48)
        if len(raw) != 32:
            raise SessionDenied("Invalid challenge length")
        return CONTEXT + device_id.encode("ascii") + b"\x00" + raw

    def verify(self, proof):
        if not isinstance(proof, DeviceProof) or type(proof.device_id) is not str:
            raise SessionDenied("Invalid device proof")
        # Pop before cryptographic validation: failed attempts also consume nonce.
        pending = self._pending.pop(proof.device_id, None)
        if pending is None:
            raise SessionDenied("Challenge missing or already used")
        nonce, expiry = pending
        if type(self._clock()) not in (int, float) or self._clock() >= expiry:
            raise SessionDenied("Challenge expired")
        if proof.challenge != nonce:
            raise SessionDenied("Challenge mismatch")
        key = self._keys.get(proof.device_id)
        if key is None:
            raise SessionDenied("Unknown device")
        signature = decode_b64(proof.signature, limit=400)
        try:
            key.verify(signature, self.signed_message(proof.device_id, nonce),
                       ec.ECDSA(hashes.SHA256()))
        except (InvalidSignature, ValueError):
            raise SessionDenied("Cryptographic device proof not verified") from None
        return VerifiedDevice(proof.device_id)
