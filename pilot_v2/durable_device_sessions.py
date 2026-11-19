"""Offline SQLite V2 session store, shared by workers on ONE secure local host.

Not an HTTP endpoint. Caller supplies a cryptographically verified device ID
from an independent P-256 challenge verifier. Trusted bootstrap/enrollment must
be provisioned separately. Never grant auth from a claimed mobile device ID.
"""
import hashlib
import secrets
import sqlite3
import time
from pathlib import Path

from .device_policy import ALLOWED_FEEDS, MAX_DEVICES, valid_id
from .device_sessions import VerifiedDevice, SessionDenied


class DurableDeviceSessions:
    def __init__(self, db_path, *, clock=None, ttl=900):
        if (not isinstance(db_path, (str, Path)) or not str(db_path)
                or type(ttl) is not int or not 60 <= ttl <= 3600):
            raise ValueError("Invalid session store configuration")
        self._path = str(db_path)
        self._clock = clock or time.time  # wall-clock persists across process restarts
        self._ttl = ttl
        with self._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS devices(
                device TEXT PRIMARY KEY, master INTEGER NOT NULL,
                enabled INTEGER NOT NULL, feeds TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS sessions(
                digest TEXT PRIMARY KEY, device TEXT NOT NULL,
                expiry REAL NOT NULL)""")

    def _db(self):
        db = sqlite3.connect(self._path, isolation_level=None, timeout=10)
        db.execute("PRAGMA busy_timeout=10000")
        return db

    def _now(self):
        from math import isfinite
        x = self._clock()
        if type(x) not in (int, float) or not isfinite(x) or x < 0:
            raise SessionDenied("Invalid session clock")
        return float(x)

    @staticmethod
    def _digest(token):
        if type(token) is not str or not 40 <= len(token) <= 160:
            raise SessionDenied("Invalid bearer")
        try:
            return hashlib.sha256(token.encode("ascii")).hexdigest()
        except UnicodeEncodeError:
            raise SessionDenied("Invalid bearer") from None

    @staticmethod
    def _feeds(value):
        if type(value) not in (tuple, list, set, frozenset):
            raise SessionDenied("Invalid requested feeds")
        selected = frozenset(value)
        if not selected or not selected.issubset(ALLOWED_FEEDS):
            raise SessionDenied("Invalid allowed feeds")
        return ",".join(sorted(selected))

    def bootstrap(self, device_id, *, authorize_bootstrap):
        """Trusted server configuration hook only. Never map to an HTTP route."""
        if not valid_id(device_id) or not callable(authorize_bootstrap):
            raise SessionDenied("Invalid trusted bootstrap")
        if authorize_bootstrap(device_id) is not True:
            raise SessionDenied("Master bootstrap was not authorized")
        with self._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                if db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]:
                    raise SessionDenied("Master already provisioned")
                db.execute("INSERT INTO devices VALUES(?,?,?,?)",
                           (device_id, 1, 1, self._feeds(ALLOWED_FEEDS)))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def issue_verified(self, identity):
        """Only pass a VerifiedDevice produced by a trusted crypto verifier."""
        if not isinstance(identity, VerifiedDevice):
            raise SessionDenied("Cryptographic identity missing")
        now = self._now()
        token = secrets.token_urlsafe(48)
        with self._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                row = db.execute("SELECT enabled FROM devices WHERE device=?",
                                 (identity.device_id,)).fetchone()
                if row is None or row[0] != 1:
                    raise SessionDenied("Device disabled or unknown")
                db.execute("DELETE FROM sessions WHERE device=?",
                           (identity.device_id,))
                db.execute("INSERT INTO sessions VALUES(?,?,?)",
                           (self._digest(token), identity.device_id, now + self._ttl))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return token

    def _identity_tx(self, db, token, *, feed=None, master=False):
        digest = self._digest(token)
        row = db.execute("""SELECT s.device,s.expiry,d.enabled,d.master,d.feeds
            FROM sessions s JOIN devices d ON d.device=s.device
            WHERE s.digest=?""", (digest,)).fetchone()
        if row is None or row[1] <= self._now() or row[2] != 1:
            raise SessionDenied("Device session expired or revoked")
        if master and row[3] != 1:
            raise SessionDenied("Master session required")
        if feed is not None and feed not in row[4].split(","):
            raise SessionDenied("Feed access denied")
        return row[0]

    def authorize(self, token, feed):
        if type(feed) is not str or feed not in ALLOWED_FEEDS:
            raise SessionDenied("Unknown read-only data feed")
        with self._db() as db:
            db.execute("BEGIN")
            try:
                device = self._identity_tx(db, token, feed=feed)
                db.execute("COMMIT")
                return device
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def authorize_master(self, token):
        """Verify a live Master session for internal private-data operations."""
        with self._db() as db:
            db.execute("BEGIN")
            try:
                master_id = self._identity_tx(db, token, master=True)
                db.execute("COMMIT")
                return master_id
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def master_grant(self, token, device_id, feeds, *, enabled=True):
        """Changes are atomic with session revocation on disable/update."""
        if not valid_id(device_id) or type(enabled) is not bool:
            raise SessionDenied("Invalid delegated device")
        normalized = self._feeds(feeds)
        with self._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                master_id = self._identity_tx(db, token, master=True)
                if device_id == master_id:
                    raise SessionDenied("Cannot modify master")
                old = db.execute("SELECT master FROM devices WHERE device=?",
                                 (device_id,)).fetchone()
                if old and old[0] == 1:
                    raise SessionDenied("Cannot modify master")
                if old is None and db.execute("SELECT COUNT(*) FROM devices").fetchone()[0] >= MAX_DEVICES:
                    raise SessionDenied("Maximum four devices")
                db.execute("""INSERT INTO devices(device,master,enabled,feeds)
                    VALUES(?,?,?,?) ON CONFLICT(device) DO UPDATE SET
                    enabled=excluded.enabled,feeds=excluded.feeds""",
                    (device_id, 0, int(enabled), normalized))
                # Any changed permission invalidates old sessions; login anew.
                db.execute("DELETE FROM sessions WHERE device=?", (device_id,))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def revoke(self, token, device_id):
        with self._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                master_id = self._identity_tx(db, token, master=True)
                if device_id == master_id:
                    raise SessionDenied("Cannot revoke master")
                db.execute("DELETE FROM sessions WHERE device=?", (device_id,))
                db.execute("DELETE FROM devices WHERE device=? AND master=0",
                           (device_id,))
                # Revocation must erase the trust root and pending enrollment,
                # not just a bearer. These auxiliary tables are optional when
                # the basic session-store prototype is used without key modules.
                for table in ("device_keys", "pending_device_keys", "login_challenge"):
                    exists = db.execute(
                        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                        (table,)).fetchone()
                    if exists:
                        db.execute("DELETE FROM " + table + " WHERE device=?",
                                   (device_id,))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def logout(self, token):
        digest = self._digest(token)
        with self._db() as db:
            db.execute("DELETE FROM sessions WHERE digest=?", (digest,))
