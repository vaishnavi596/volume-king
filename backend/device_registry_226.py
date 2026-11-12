"""BOT KING 226 persistent, owner-enrolled device registry (offline component).

No public enrollment routes are exposed here. The caller must verify owner
approval and cryptographic device proof before issuing any session.
"""
import os
import hashlib
import secrets
import re
import stat
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
        if self.database_path == ":memory:":
            raise DeviceRegistryError("Persistent device database required")
        database = Path(self.database_path)
        database.parent.mkdir(parents=True, exist_ok=True)
        if database.is_symlink():
            raise DeviceRegistryError("Symlink device database rejected")
        if database.exists() and (not database.is_file() or database.stat().st_mode & 0o077):
            raise DeviceRegistryError("Device database permissions must be private")
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
            db.execute("""CREATE TABLE IF NOT EXISTS login_limits (
                device_id TEXT PRIMARY KEY, failures INTEGER NOT NULL DEFAULT 0,
                first_failure_at INTEGER NOT NULL DEFAULT 0,
                locked_until INTEGER NOT NULL DEFAULT 0)""")
            db.execute("""CREATE TABLE IF NOT EXISTS device_challenges (
                challenge_digest TEXT PRIMARY KEY, device_id TEXT NOT NULL,
                expires_at INTEGER NOT NULL)""")
        os.chmod(self.database_path, stat.S_IRUSR | stat.S_IWUSR)

    @contextmanager
    def _connect(self):
        db = sqlite3.connect(self.database_path, timeout=5)
        db.execute("PRAGMA busy_timeout=5000")
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

    def issue_challenge(self, device_id, ttl_seconds=120):
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            raise DeviceRegistryError("Invalid device")
        if not self.login_allowed(device_id) or self.active_public_key(device_id) is None:
            raise DeviceRegistryError("Device unavailable")
        if type(ttl_seconds) is not int or not 30 <= ttl_seconds <= 300:
            raise DeviceRegistryError("Invalid challenge lifetime")
        import base64
        challenge = base64.urlsafe_b64encode(secrets.token_bytes(32)).decode("ascii")
        digest = hashlib.sha256(challenge.encode("ascii")).hexdigest()
        with self._connect() as db:
            db.execute("DELETE FROM device_challenges WHERE expires_at<=?",
                       (int(self.clock()),))
            db.execute("INSERT INTO device_challenges VALUES(?,?,?)",
                       (digest, device_id, int(self.clock()) + ttl_seconds))
        return challenge

    def consume_challenge(self, device_id, challenge):
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            return False
        if not isinstance(challenge, str) or len(challenge) > 256:
            return False
        try:
            digest = hashlib.sha256(challenge.encode("ascii")).hexdigest()
        except UnicodeEncodeError:
            return False
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT expires_at FROM device_challenges WHERE challenge_digest=? AND device_id=?",
                             (digest, device_id)).fetchone()
            db.execute("DELETE FROM device_challenges WHERE challenge_digest=? AND device_id=?",
                       (digest, device_id))
        return row is not None and int(self.clock()) < row[0]

    def login_allowed(self, device_id):
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            return False
        with self._connect() as db:
            row = db.execute("SELECT locked_until FROM login_limits WHERE device_id=?",
                             (device_id,)).fetchone()
        return row is None or int(self.clock()) >= row[0]

    def record_login_failure(self, device_id, max_attempts=5, window_seconds=300,
                             lock_seconds=900):
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            return False
        now = int(self.clock())
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("""SELECT failures,first_failure_at,locked_until
                FROM login_limits WHERE device_id=?""", (device_id,)).fetchone()
            if row and now < row[2]:
                return False
            count = row[0] + 1 if row and now - row[1] < window_seconds else 1
            first = row[1] if row and now - row[1] < window_seconds else now
            until = now + lock_seconds if count >= max_attempts else 0
            db.execute("""INSERT INTO login_limits(device_id,failures,first_failure_at,locked_until)
                VALUES(?,?,?,?) ON CONFLICT(device_id) DO UPDATE SET
                failures=excluded.failures,first_failure_at=excluded.first_failure_at,
                locked_until=excluded.locked_until""", (device_id, count, first, until))
        return until == 0

    def clear_login_failures(self, device_id):
        if not self.login_allowed(device_id):
            return False
        with self._connect() as db:
            db.execute("DELETE FROM login_limits WHERE device_id=?", (device_id,))
        return True

    def active_public_key(self, device_id):
        """Read only an active enrolled device's public key."""
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            return None
        with self._connect() as db:
            row = db.execute(
                "SELECT public_key FROM devices WHERE device_id=? AND revoked_at IS NULL",
                (device_id,)
            ).fetchone()
        return row[0] if row else None

    def issue_session(self, device_id, *, device_proof_verified=False, ttl_seconds=900):
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            raise DeviceRegistryError("Invalid device ID")
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
        if not isinstance(device_id, str) or not DEVICE_ID.fullmatch(device_id):
            return False
        try:
            digest = session_token_digest(token)
        except (ValueError, TypeError):
            return False
        with self._connect() as db:
            row = db.execute("""SELECT s.token_digest FROM sessions s JOIN devices d
                ON s.device_id=d.device_id WHERE s.device_id=? AND s.token_digest=? AND
                s.revoked_at IS NULL AND d.revoked_at IS NULL AND s.expires_at>?""",
                (device_id, digest, int(self.clock()))).fetchone()
        return row is not None

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
