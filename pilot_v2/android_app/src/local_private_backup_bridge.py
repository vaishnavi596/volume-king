"""V2 local backup policy bridge for future trusted Android crypto integration.

No server imports, network, secrets persistence or Flet-native dependencies.
A production-tested platform encryption callback must be provided explicitly.
This module does not itself implement native Android encryption or upload.
"""
import base64
import binascii
import json
from local_settings_backup import parse_local_backup, LocalBackupError

MAX_PLAINTEXT = 16384
MAX_ENVELOPE = 27000
FIELDS = frozenset(("version", "kdf", "salt", "nonce", "ciphertext"))


class LocalPrivateBackupError(ValueError):
    pass


def _validate_local(text):
    if type(text) is not str or not 0 < len(text.encode("utf-8")) <= MAX_PLAINTEXT:
        raise LocalPrivateBackupError("Invalid preference backup")
    try:
        # Existing strict V2 schema, symbol roster and context checks are the
        # single source of truth; never accept vault-only shape checks.
        return parse_local_backup(text)
    except (LocalBackupError, ValueError, TypeError, UnicodeError):
        raise LocalPrivateBackupError("Invalid preference backup") from None


def _envelope(envelope):
    """Match the server's strict opaque V2 envelope without importing it.

    This validates the wire format, NOT cryptographic authenticity; the
    injected trusted unseal callback must perform AEAD integrity verification.
    """
    if type(envelope) is not str or not 0 < len(envelope) <= MAX_ENVELOPE:
        raise LocalPrivateBackupError("Invalid encrypted backup")
    try:
        document = json.loads(envelope)
        if (type(document) is not dict or set(document) != FIELDS
                or type(document["version"]) is not int
                or document["version"] != 1
                or document["kdf"] != "scrypt-16384-8-1"):
            raise ValueError("Unsupported envelope")
        for key, expected in (("salt", 16), ("nonce", 12),
                              ("ciphertext", None)):
            value = document[key]
            if type(value) is not str or len(value) > MAX_ENVELOPE:
                raise ValueError("Invalid encoded data")
            raw = base64.b64decode(value, validate=True)
            if base64.b64encode(raw).decode("ascii") != value:
                raise ValueError("Noncanonical encoding")
            if expected is not None and len(raw) != expected:
                raise ValueError("Invalid length")
            if key == "ciphertext" and not 16 < len(raw) <= MAX_PLAINTEXT + 16:
                raise ValueError("Invalid ciphertext length")
    except (ValueError, TypeError, RecursionError, binascii.Error):
        raise LocalPrivateBackupError("Invalid encrypted backup") from None
    return envelope


def prepare_private_backup(local_json, password, *, seal):
    """Validate *before* handing a local preference export to trusted crypto."""
    _validate_local(local_json)
    if type(password) is not str or not 12 <= len(password) <= 256:
        raise LocalPrivateBackupError("Invalid private backup password")
    if not callable(seal):
        raise LocalPrivateBackupError("Trusted platform encryption unavailable")
    try:
        result = seal(local_json, password)
    except Exception:
        # Crypto failures must not surface sensitive exception strings.
        raise LocalPrivateBackupError("Private backup encryption unavailable") from None
    return _envelope(result)


def preview_private_restore(envelope, password, *, unseal):
    """Decrypt and validate, but never mutate app settings or auto-restore."""
    _envelope(envelope)
    if type(password) is not str or not 12 <= len(password) <= 256:
        raise LocalPrivateBackupError("Invalid private backup password")
    if not callable(unseal):
        raise LocalPrivateBackupError("Trusted platform decryption unavailable")
    try:
        local_json = unseal(envelope, password)
    except Exception:
        raise LocalPrivateBackupError("Decryption or integrity verification failed") from None
    # Return validated parsed objects for the existing explicit, confirmation-
    # gated Settings restore callback. No state mutation here.
    return _validate_local(local_json)
