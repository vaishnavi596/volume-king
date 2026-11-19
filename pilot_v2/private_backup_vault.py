"""V2 private preference backup: client-side AES-GCM, server stores opaque ciphertext.

No HTTP route, device key, Dhan credential, or live service is created here.
An independently authenticated Master-session resolver is mandatory to access
the vault. The raw backup password never crosses into ServerBackupVault.
"""
from __future__ import annotations

import base64
import json
import os
import sqlite3
from pathlib import Path
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from .device_policy import valid_id

MAX_PLAINTEXT = 16384
MAX_ENVELOPE = 27000
AAD = b"BOT-KING-V2-LOCAL-PREFERENCES-V1"
FIELD_SET = frozenset(("version", "kdf", "salt", "nonce", "ciphertext"))
BACKUP_FIELDS = frozenset(("kind", "schema_version", "watchlists",
                           "scanner", "smart_data", "analysis_slots",
                           "chart_style", "chart_window", "chart_visible"))


class PrivateBackupDenied(ValueError):
    pass


def _b64(data):
    return base64.b64encode(data).decode("ascii")


def _bytes(value, n=None):
    try:
        if type(value) is not str or len(value) > MAX_ENVELOPE:
            raise ValueError
        b = base64.b64decode(value, validate=True)
        if _b64(b) != value or (n is not None and len(b) != n):
            raise ValueError
        return b
    except (ValueError, TypeError):
        raise PrivateBackupDenied("Invalid encrypted envelope") from None


def _password(value):
    if type(value) is not str or not 12 <= len(value) <= 256:
        raise PrivateBackupDenied("A private backup password is required")
    return value.encode("utf-8")


def _backup_data(text):
    if type(text) is not str or not 1 <= len(text.encode("utf-8")) <= MAX_PLAINTEXT:
        raise PrivateBackupDenied("Invalid local preference payload")
    try:
        data = json.loads(text)
        if (type(data) is not dict or data.get("kind") != "botking-v2-local-preferences"
                or type(data.get("schema_version")) is not int
                or data["schema_version"] not in (1, 2, 3, 4)
                or not {"kind", "schema_version", "watchlists",
                        "scanner", "smart_data", "analysis_slots"}.issubset(data)
                or not set(data).issubset(BACKUP_FIELDS)):
            raise ValueError
    except (ValueError, TypeError, UnicodeError, RecursionError):
        raise PrivateBackupDenied("Not a V2 local preference backup") from None
    # Full cross-field app validation remains the existing parse_local_backup()
    # caller's responsibility, both before sealing and after unsealing.
    return text.encode("utf-8")


def _key(password, salt):
    return Scrypt(salt=salt, length=32, n=2**14, r=8, p=1).derive(
        _password(password))


def seal_local_preferences(backup_json, password):
    """Run on trusted client only; never send password or derived key to server."""
    plaintext = _backup_data(backup_json)
    salt, nonce = os.urandom(16), os.urandom(12)
    encrypted = AESGCM(_key(password, salt)).encrypt(nonce, plaintext, AAD)
    return json.dumps({"version": 1, "kdf": "scrypt-16384-8-1",
                       "salt": _b64(salt), "nonce": _b64(nonce),
                       "ciphertext": _b64(encrypted)},
                      sort_keys=True, separators=(",", ":"))


def inspect_envelope(envelope):
    """Strict opaque validation; does not decrypt, authorize or reveal data."""
    if type(envelope) is not str or not 1 <= len(envelope) <= MAX_ENVELOPE:
        raise PrivateBackupDenied("Invalid encrypted backup size")
    try:
        doc = json.loads(envelope)
        if (type(doc) is not dict or set(doc) != FIELD_SET
                or type(doc["version"]) is not int or doc["version"] != 1
                or doc["kdf"] != "scrypt-16384-8-1"):
            raise ValueError
    except (ValueError, TypeError, RecursionError):
        raise PrivateBackupDenied("Invalid encrypted backup format") from None
    _bytes(doc["salt"], 16)
    _bytes(doc["nonce"], 12)
    cipher = _bytes(doc["ciphertext"])
    if not 16 < len(cipher) <= MAX_PLAINTEXT + 16:
        raise PrivateBackupDenied("Invalid encrypted backup length")
    return envelope


def unseal_local_preferences(envelope, password):
    doc = json.loads(inspect_envelope(envelope))
    try:
        content = AESGCM(_key(password, _bytes(doc["salt"], 16))).decrypt(
            _bytes(doc["nonce"], 12), _bytes(doc["ciphertext"]), AAD)
        return _backup_data(content.decode("utf-8")).decode("utf-8")
    except (ValueError, UnicodeError, RecursionError):
        raise PrivateBackupDenied("Backup password or integrity verification failed") from None
    except Exception as exc:
        from cryptography.exceptions import InvalidTag
        if isinstance(exc, InvalidTag):
            raise PrivateBackupDenied("Backup password or integrity verification failed") from None
        raise


class ServerBackupVault:
    """Opaque per-owner ciphertext store, not an HTTP endpoint.

    master_owner(token) must independently validate a live, revocable Master
    session and return its stable server-owned owner ID. No owner ID is accepted
    from an HTTP payload or from this class's callers.
    """
    def __init__(self, db_path, *, master_owner):
        if not callable(master_owner) or not isinstance(db_path, (str, Path)):
            raise ValueError("Verified Master resolver and database path required")
        path = Path(db_path)
        if path.is_symlink() or not path.parent.is_dir():
            raise ValueError("Unsafe database path")
        self._path = str(path)
        self._master_owner = master_owner
        if not path.exists():
            fd = os.open(self._path, os.O_CREAT | os.O_EXCL | os.O_RDWR, 0o600)
            os.close(fd)
        if path.is_symlink() or os.stat(path).st_mode & 0o077:
            raise ValueError("Private backup database permissions are unsafe")
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS private_backups(
                owner TEXT PRIMARY KEY, revision INTEGER NOT NULL,
                encrypted_envelope TEXT NOT NULL)""")

    def _db(self):
        db = sqlite3.connect(self._path, timeout=10)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _owner(self, token):
        try:
            owner = self._master_owner(token)
        except Exception:
            raise PrivateBackupDenied("Verified Master session required") from None
        if not valid_id(owner):
            raise PrivateBackupDenied("Verified Master session required")
        return owner

    def read(self, token):
        owner = self._owner(token)
        with self._db() as db:
            row = db.execute("SELECT revision,encrypted_envelope FROM private_backups "
                             "WHERE owner=?", (owner,)).fetchone()
        return (row[0], row[1]) if row else (0, None)

    def replace(self, token, envelope, *, expected_revision):
        owner = self._owner(token)
        inspect_envelope(envelope)
        if type(expected_revision) is not int or not 0 <= expected_revision < 2**63 - 1:
            raise PrivateBackupDenied("Invalid expected revision")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT revision FROM private_backups WHERE owner=?",
                             (owner,)).fetchone()
            current = row[0] if row else 0
            if current != expected_revision:
                raise PrivateBackupDenied("Backup changed; restore or reconcile first")
            revision = current + 1
            db.execute("""INSERT INTO private_backups(owner,revision,encrypted_envelope)
                VALUES(?,?,?) ON CONFLICT(owner) DO UPDATE SET
                revision=excluded.revision,encrypted_envelope=excluded.encrypted_envelope""",
                (owner, revision, envelope))
            return revision
