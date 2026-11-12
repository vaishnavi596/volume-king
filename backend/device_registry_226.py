"""BOT KING 226 persistent, owner-enrolled device registry (offline component).

No public enrollment routes are exposed here. The caller must verify owner
approval and cryptographic device proof before issuing any session.
"""
import hmac
import re
import secrets
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

try:
    from .device_auth_226 import new_session_token, session_token_digest
except ImportError:
    from device_auth_226 import new_session_token, session_token_digest

DEVICE_ID = re.compile(r"^[A-Za-z0-9_-]{16,128}$")


class DeviceRegistryError(ValueError):
    pass


class DeviceRegistry:
    def __init__(self, database_path, clock=None):
        self.database_path = str(database_path)
        self.clock = clock or time.time
        Path(self.database_path).parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS devices (
                device_id TEXT PRIMARY KEY,
                public_key TEXT NOT NULL,
                enrolled_at INTEGER NOT NULL,
                revoked_at INTEGER
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS sessions (
                token_digest TEXT PRIMARY KEY,
                device_id TEXT NOT NULL REFERENCES devices(device_id),
                expires_at INTEGER NOT NULL,
                revoked_at INTEGER
            )""")

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.database_path, timeout=5)
        try:
            db.execute("PRAGMA foreign_keys=ON")
            yield db
            db.commit()
        finally:
            db.close()

    def enroll_approved_device(self, device_id, public_key, *, owner_approved=False):
        if owner_approved is not True:
            raise DeviceRegistryError("Owner approval required")
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            raise DeviceRegistryError("Invalid device ID")
        if not isinstance(public_key, str) or not 32 <= len(public_key) <= 4096:
            raise DeviceRegistryError("Invalid device public key")
        with self._connect() as db:
            db.execute("INSERT INTO devices(device_id,public_key,enrolled_at) VALUES (?,?,?)",
                       (device_id, public_key, int(self.clock())))

    def issue_session(self, device_id, *, device_proof_verified=False, ttl_seconds=900):
        if device_proof_verified is not True:
            raise DeviceRegistryError("Device proof required")
        if type(ttl_seconds) is not int or not 60 <= ttl_seconds <= 3600:
            raise DeviceRegistryError("Invalid session duration")
        token = new_session_token()
        with self._connect() as db:
            device = db.execute("SELECT revoked_at FROM devices WHERE device_id=?",
                                (device_id,)).fetchone()
            if device is None or device[0] is not None:
                raise DeviceRegistryError("Unknown or revoked device")
            db.execute("INSERT INTO sessions(token_digest,device_id,expires_at) VALUES (?,?,?)",
                       (session_token_digest(token), device_id, int(self.clock()) + ttl_seconds))
        return token

    def validate_session(self, device_id, token):
        try:
            digest = session_token_digest(token)
        except (ValueError, TypeError):
            return False
        with self._connect() as db:
            row = db.execute("""SELECT s.token_digest FROM sessions s JOIN devices d
                ON s.device_id=d.device_id WHERE s.device_id=? AND
                s.revoked_at IS NULL AND d.revoked_at IS NULL AND s.expires_at>?""",
                (device_id, int(self.clock()))).fetchone()
        return bool(row and hmac.compare_digest(row[0], digest))

    def revoke_device(self, device_id):
        with self._connect() as db:
            now = int(self.clock())
            db.execute("UPDATE devices SET revoked_at=? WHERE device_id=? AND revoked_at IS NULL",
                       (now, device_id))
            db.execute("UPDATE sessions SET revoked_at=? WHERE device_id=? AND revoked_at IS NULL",
                       (now, device_id))

    def revoke_session(self, token):
        digest = session_token_digest(token)
        with self._connect() as db:
            db.execute("UPDATE sessions SET revoked_at=? WHERE token_digest=?",
                       (int(self.clock()), digest))
