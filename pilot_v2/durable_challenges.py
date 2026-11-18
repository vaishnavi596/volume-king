"""Offline single-host atomic SQLite P-256 login challenge prototype.

Master is statically provisioned; delegated keys may come from current durable\nkey resolver after master-approved enrollment. Does not
expose HTTP, provision keys, accept arbitrary client keys, or call Dhan.
Production demands local protected SQLite storage, rate limits and audited
key enrollment. Uses wall clock for restart-safe challenge expiration.
"""
import hashlib
import secrets
import sqlite3
import time
from pathlib import Path
from math import isfinite

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .device_policy import valid_id
from .device_sessions import SessionDenied, VerifiedDevice
from .device_verifier import DeviceProof, P256ChallengeVerifier, encode_b64, decode_b64

class DurableP256ChallengeVerifier:
    def __init__(self, db_path, trusted_public_keys, *, clock=None, ttl_seconds=60,
                 trusted_key_resolver=None):
        if (not isinstance(db_path, (str,Path)) or not str(db_path)
                or type(trusted_public_keys) is not dict
                or type(ttl_seconds) is not int or not 10 <= ttl_seconds <= 120):
            raise ValueError("Invalid verifier configuration")
        if trusted_key_resolver is not None and not callable(trusted_key_resolver):
            raise ValueError("Trusted key resolver must be callable")
        self._resolver=trusted_key_resolver
        self._path=str(db_path)
        self._keys={}
        self._clock=clock or time.time
        self._ttl=ttl_seconds
        for device, der in trusted_public_keys.items():
            if not valid_id(device) or type(der) is not bytes or len(der)>512:
                raise ValueError("Invalid trusted enrollment")
            try:
                key=serialization.load_der_public_key(der)
            except (TypeError,ValueError):
                raise ValueError("Invalid trusted P-256 enrollment") from None
            if not isinstance(key,ec.EllipticCurvePublicKey) or not isinstance(
                    key.curve,ec.SECP256R1):
                raise ValueError("Trusted public key must be P-256")
            self._keys[device]=key
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS login_challenge(
                device TEXT PRIMARY KEY, digest TEXT NOT NULL,
                issued_at REAL NOT NULL, expires_at REAL NOT NULL)""")

    def _db(self):
        db=sqlite3.connect(self._path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _now(self):
        v=self._clock()
        if type(v) not in (int,float) or not isfinite(v) or v<0:
            raise SessionDenied("Invalid login clock")
        return float(v)

    def _current_key(self, device_id):
        if not valid_id(device_id):
            raise SessionDenied("Unknown device")
        # Static allowlist is for trusted, separately provisioned master only.
        # Delegated devices are resolved from the current durable enrollment,
        # not from an old startup snapshot.
        if device_id in self._keys:
            return self._keys[device_id]
        if self._resolver is None:
            raise SessionDenied("Unknown device")
        der=self._resolver(device_id)
        if der is None:
            raise SessionDenied("Unknown or disabled device")
        if type(der) is not bytes or len(der)>512:
            raise SessionDenied("Invalid current public key")
        try:
            key=serialization.load_der_public_key(der)
        except (ValueError,TypeError):
            raise SessionDenied("Invalid current public key") from None
        if not isinstance(key,ec.EllipticCurvePublicKey) or not isinstance(
                key.curve,ec.SECP256R1):
            raise SessionDenied("Invalid current P-256 key")
        return key

    def challenge(self, device_id):
        self._current_key(device_id)
        nonce=encode_b64(secrets.token_bytes(32))
        now=self._now()
        digest=hashlib.sha256(nonce.encode("ascii")).hexdigest()
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                db.execute("""INSERT INTO login_challenge(device,digest,issued_at,expires_at)
                    VALUES(?,?,?,?) ON CONFLICT(device) DO UPDATE SET
                    digest=excluded.digest,issued_at=excluded.issued_at,
                    expires_at=excluded.expires_at""",
                    (device_id,digest,now,now+self._ttl))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return nonce

    def verify(self, proof):
        if not isinstance(proof,DeviceProof) or type(proof.device_id) is not str:
            raise SessionDenied("P-256 device proof required")
        now=self._now()
        with self._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row=db.execute("""SELECT digest,issued_at,expires_at
                    FROM login_challenge WHERE device=?""",(proof.device_id,)).fetchone()
                # Consume under a writer lock, even if the signature or nonce
                # is bad. Other workers cannot redeem the same proof.
                db.execute("DELETE FROM login_challenge WHERE device=?",
                           (proof.device_id,))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        if row is None or now<row[1] or now>=row[2]:
            raise SessionDenied("Challenge missing, expired or already used")
        raw=decode_b64(proof.challenge,limit=48)
        if len(raw)!=32 or hashlib.sha256(proof.challenge.encode("ascii")).hexdigest()!=row[0]:
            raise SessionDenied("Challenge mismatch")
        # Resolve the current key again: successful enrollment/rotation
        # invalidates a previously cached delegated signing key.
        key=self._current_key(proof.device_id)
        signature=decode_b64(proof.signature,limit=400)
        try:
            key.verify(signature,P256ChallengeVerifier.signed_message(
                proof.device_id,proof.challenge),ec.ECDSA(hashes.SHA256()))
        except (InvalidSignature,ValueError):
            raise SessionDenied("Cryptographic device proof not verified") from None
        return VerifiedDevice(proof.device_id)
