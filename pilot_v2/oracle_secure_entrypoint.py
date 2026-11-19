"""Fail-closed Oracle V2 ASGI production composition from local private files.

No GitHub secret is accepted as the mobile Master key. A real Android Keystore
P-256 public SPKI, already owner-approved and master-enrolled in the private
SQLite database, is mandatory. Never auto-enroll or bootstrap any identity.
"""
from __future__ import annotations

import os
import hmac
import sqlite3
from pathlib import Path
import stat

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .device_policy import valid_id
from .oracle_runtime_factory import create_oracle_v2_runtime


def _private_file(path, *, max_bytes):
    if type(path) is not str or not path or not Path(path).is_absolute():
        raise ValueError("Absolute protected V2 file path required")
    p = Path(path)
    if p.is_symlink() or not p.is_file():
        raise ValueError("Missing or linked protected V2 file")
    parent = p.parent
    if parent.is_symlink() or stat.S_IMODE(parent.stat().st_mode) & 0o077:
        raise ValueError("Protected V2 directory permissions required")
    info = p.stat()
    if stat.S_IMODE(info.st_mode) & 0o077 or info.st_size < 1 or info.st_size > max_bytes:
        raise ValueError("Protected V2 file permissions or size invalid")
    return p.read_bytes()


def from_private_config(*, device_id, master_der_path, pairing_path, db_path):
    """Construct the real authenticated app, never the disabled demo shell."""
    if not valid_id(device_id):
        raise ValueError("Invalid independently approved Master device")
    public = _private_file(master_der_path, max_bytes=512)
    try:
        parsed = serialization.load_der_public_key(public)
    except (ValueError, TypeError):
        raise ValueError("Invalid Master public SPKI") from None
    if (not isinstance(parsed, ec.EllipticCurvePublicKey) or
            not isinstance(parsed.curve, ec.SECP256R1) or
            parsed.public_bytes(serialization.Encoding.DER,
                                serialization.PublicFormat.SubjectPublicKeyInfo) != public):
        raise ValueError("Canonical P-256 Master public key required")
    pairing_bytes = _private_file(pairing_path, max_bytes=256)
    try:
        pairing = pairing_bytes.decode("ascii")
    except UnicodeDecodeError:
        raise ValueError("Invalid Oracle pairing material") from None
    if (pairing != pairing.strip() or len(pairing) < 32 or
            any(ord(c) < 33 or ord(c) > 126 for c in pairing)):
        raise ValueError("Invalid private Oracle pairing key")
    # Also validate the DB file and parent; factory independently verifies the
    # Master is already present AND enabled, so no bootstrap is possible.
    _private_file(db_path, max_bytes=50_000_000)
    # The enrolled identity must own THIS exact device public key. Merely
    # checking a matching Master device_id is insufficient: an arbitrary
    # replacement P-256 public key could otherwise become trusted at restart.
    try:
        with sqlite3.connect(f"file:{db_path}?mode=ro", uri=True, timeout=5) as db:
            record = db.execute("SELECT k.public_der FROM device_keys AS k "
                "JOIN devices AS d ON d.device=k.device "
                "WHERE k.device=? AND d.master=1 AND d.enabled=1", (device_id,)).fetchone()
    except (sqlite3.Error, OSError):
        raise ValueError("Approved Master key record missing") from None
    if record is None or not hmac.compare_digest(record[0], public):
        raise ValueError("Master key does not match enrolled public key")
    return create_oracle_v2_runtime(
        db_path=db_path, master_device_id=device_id,
        master_public_der=public, pairing_key=pairing)


def create_app():
    """Uvicorn --factory entrypoint. No fallback credentials or fake data."""
    return from_private_config(
        device_id=os.environ.get("BOTKING_V2_MASTER_DEVICE_ID"),
        master_der_path=os.environ.get("BOTKING_V2_MASTER_PUBLIC_DER_PATH"),
        pairing_path=os.environ.get("BOTKING_V2_PAIRING_KEY_PATH"),
        db_path=os.environ.get("BOTKING_V2_DB_PATH"))


__all__ = ["create_app", "from_private_config"]
