"""BOT KING 226 device-auth primitives; not yet exposed as API routes.

A device PIN unlocks a Keystore-bound credential on Android. Never use a PIN
as the Oracle bearer credential or the Dhan broker PIN.
"""
import hashlib
import hmac
import secrets
import time


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
    try:
        encoded = token.encode("ascii")
    except UnicodeEncodeError as exc:
        raise DeviceAuthError("Invalid device session") from exc
    return hashlib.sha256(encoded).hexdigest()


class PinAttemptLimiter:
    """In-memory fail-closed throttle for offline tests and future integration.

    Production enrollment must use a persistent, per-device limiter across
    Oracle workers and restarts, not this process-local helper alone.
    """

    def __init__(self, max_attempts=5, window_seconds=300, lock_seconds=900, clock=None):
        if type(max_attempts) is not int or max_attempts < 1:
            raise DeviceAuthError("Invalid retry policy")
        if type(window_seconds) not in (int, float) or window_seconds <= 0:
            raise DeviceAuthError("Invalid retry window")
        if type(lock_seconds) not in (int, float) or lock_seconds <= 0:
            raise DeviceAuthError("Invalid lockout period")
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.lock_seconds = lock_seconds
        self.clock = clock or time.monotonic
        self._attempts = {}

    def allowed(self, device_id):
        if not isinstance(device_id, str) or not device_id.strip():
            return False
        now = self.clock()
        state = self._attempts.get(device_id)
        if state is None:
            return True
        failures, locked_until = state
        return now >= locked_until

    def record_failure(self, device_id):
        if not isinstance(device_id, str) or not device_id.strip():
            raise DeviceAuthError("Invalid device ID")
        now = self.clock()
        failures, locked_until = self._attempts.get(device_id, ([], 0.0))
        if now < locked_until:
            return False
        failures = [t for t in failures if now - t < self.window_seconds]
        failures.append(now)
        locked_until = now + self.lock_seconds if len(failures) >= self.max_attempts else 0.0
        self._attempts[device_id] = (failures, locked_until)
        return locked_until == 0.0

    def clear_after_success(self, device_id):
        if not self.allowed(device_id):
            return False
        self._attempts.pop(device_id, None)
        return True
