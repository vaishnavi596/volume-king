"""BOT KING 226 device-auth primitives; not yet exposed as API routes.

A device PIN unlocks a Keystore-bound credential on Android. Never use a PIN
as the Oracle bearer credential or the Dhan broker PIN.
"""
import hashlib
import hmac
import secrets


class DeviceAuthError(ValueError):
    pass


def validate_pin(pin):
    if not isinstance(pin, str) or len(pin) != 6 or not pin.isascii() or not pin.isdecimal():
        raise DeviceAuthError("PIN must contain exactly six ASCII digits")
    return pin


def hash_pin(pin, *, salt=None, iterations=310_000):
    """Return salted PBKDF2 verifier; caller must store with access controls."""
    validate_pin(pin)
    if type(iterations) is not int or iterations < 310_000:
        raise DeviceAuthError("Weak PIN verifier settings")
    salt = secrets.token_bytes(16) if salt is None else salt
    if not isinstance(salt, bytes) or len(salt) < 16:
        raise DeviceAuthError("Invalid salt")
    digest = hashlib.pbkdf2_hmac("sha256", pin.encode("ascii"), salt, iterations)
    return {"algorithm": "pbkdf2-sha256", "iterations": iterations,
            "salt": salt.hex(), "digest": digest.hex()}


def verify_pin(pin, record):
    """Constant-time verifier comparison; retry limits belong to the caller."""
    try:
        validate_pin(pin)
        if not isinstance(record, dict) or record.get("algorithm") != "pbkdf2-sha256":
            return False
        iterations = record["iterations"]
        if type(iterations) is not int or not 310_000 <= iterations <= 2_000_000:
            return False
        salt = bytes.fromhex(record["salt"])
        digest = bytes.fromhex(record["digest"])
        if len(salt) < 16 or len(digest) != 32:
            return False
        candidate = hashlib.pbkdf2_hmac("sha256", pin.encode("ascii"), salt, iterations)
        return hmac.compare_digest(candidate, digest)
    except (DeviceAuthError, ValueError, TypeError, KeyError, OverflowError):
        return False


def new_session_token():
    """Random opaque session secret; persist only a digest on Oracle."""
    return secrets.token_urlsafe(32)


def session_token_digest(token):
    if not isinstance(token, str) or len(token) < 32:
        raise DeviceAuthError("Invalid device session")
    return hashlib.sha256(token.encode("ascii")).hexdigest()
