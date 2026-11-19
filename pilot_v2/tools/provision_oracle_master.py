"""One-time, owner-approved V2 Master P-256 enrollment on Oracle only.

Offline file provisioning; NO HTTP enrollment endpoint, no private key export,
no broker calls and no V1 reads/writes. The Android KeyStore must have generated
and retained the matching non-exportable private key independently.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import os
from pathlib import Path
import stat

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from pilot_v2.device_policy import valid_id
from pilot_v2.durable_device_sessions import DurableDeviceSessions


def _private_directory(directory):
    if not isinstance(directory, Path) or not directory.is_absolute():
        raise ValueError("Absolute V2-only directory required")
    if directory.is_symlink() or not directory.is_dir():
        raise ValueError("V2 private directory missing or linked")
    if stat.S_IMODE(directory.stat().st_mode) & 0o077:
        raise ValueError("V2 private directory must be 0700")


def _public_spki(path):
    if not isinstance(path, Path) or not path.is_absolute():
        raise ValueError("Absolute Master public key path required")
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 512:
        raise ValueError("Invalid Master public key file")
    data = path.read_bytes()
    try:
        k = serialization.load_der_public_key(data)
    except (ValueError, TypeError):
        raise ValueError("Invalid public key DER") from None
    if (not isinstance(k, ec.EllipticCurvePublicKey)
            or not isinstance(k.curve, ec.SECP256R1)
            or k.public_bytes(serialization.Encoding.DER,
                              serialization.PublicFormat.SubjectPublicKeyInfo) != data):
        raise ValueError("Master must be canonical P-256 public SPKI")
    return data


def enroll_master(*, directory, device_id, public_path, approved_fingerprint):
    """Only called by owner on trusted console with reviewed device fingerprint."""
    directory = Path(directory)
    public_path = Path(public_path)
    _private_directory(directory)
    if public_path.parent.resolve() != directory.resolve():
        raise ValueError("Master public key must be inside protected V2 directory")
    if not valid_id(device_id):
        raise ValueError("Invalid Master device identity")
    data = _public_spki(public_path)
    digest = hashlib.sha256(data).hexdigest()
    if (type(approved_fingerprint) is not str or len(approved_fingerprint) != 64
            or not hmac.compare_digest(digest, approved_fingerprint.lower())):
        raise ValueError("Owner-reviewed public key fingerprint does not match")
    db = directory / "master.sqlite"
    if db.exists() or db.is_symlink():
        raise ValueError("Master DB already exists; never overwrite enrollment")
    old_umask = os.umask(0o077)
    try:
        sessions = DurableDeviceSessions(db)
        db.chmod(0o600)
        sessions.bootstrap(device_id, authorize_bootstrap=lambda candidate: candidate == device_id)
    finally:
        os.umask(old_umask)
    return {"master_enrolled": True, "public_fingerprint_sha256": digest,
            "private_key_exported": False, "orders_enabled": False}


def main():
    p = argparse.ArgumentParser(description="V2 Master physical-device approval and one-time enrollment")
    p.add_argument("--private-directory", required=True)
    p.add_argument("--device-id", required=True)
    p.add_argument("--public-spki-der", required=True)
    p.add_argument("--approved-public-sha256", required=True)
    a = p.parse_args()
    result = enroll_master(directory=a.private_directory, device_id=a.device_id,
                           public_path=a.public_spki_der,
                           approved_fingerprint=a.approved_public_sha256)
    print("V2_MASTER_ENROLLED=YES")
    print("V2_MASTER_PUBLIC_SHA256=" + result["public_fingerprint_sha256"])


if __name__ == "__main__":
    main()
