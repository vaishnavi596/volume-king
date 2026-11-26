"""Standalone V3 M Brain staging ledger and encrypted backup (no gateway wiring).

Pure offline foundation. No web routes, broker orders, Oracle production hooks,
phone preferences, implicit six-engine quorum, or stored login credentials.
Encrypted backup requires cryptography; lack of it fails closed.
"""
import hashlib
import hmac
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

EVENT_TYPES = frozenset(("prediction_event", "vote_evidence_reference",
                         "outcome_event", "model_policy_version"))
_FORBIDDEN = frozenset(("password", "token", "access_token", "api_key",
                         "api_secret", "client_secret", "totp", "private_key"))
SCHEMA = 1


def _canonical(payload):
    if not isinstance(payload, dict):
        raise ValueError("Event payload must be an object")
    # Inspect nested objects as well as top-level keys before serialization.
    pending=[(payload,0)]
    visited=0
    while pending:
        value,depth=pending.pop()
        visited+=1
        if depth>32 or visited>10000:
            raise ValueError("Brain event nesting or item budget exceeded")
        if isinstance(value,dict):
            if _FORBIDDEN.intersection(str(k).strip().lower() for k in value):
                raise ValueError("Secrets cannot be stored in Brain events")
            pending.extend((v,depth+1) for v in value.values())
        elif isinstance(value,(list,tuple)):
            pending.extend((v,depth+1) for v in value)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"),
                         allow_nan=False, ensure_ascii=False)
    if len(encoded.encode("utf-8")) > 65536:
        raise ValueError("Brain event exceeds bounded payload size")
    return encoded


class StagingBrainLedger:
    """Caller passes Master-authorized device credentials, held in memory only.

    This is NOT deployed authentication. A server must validate signed Master
    identity and authorize device scope before instantiating the ledger.
    """
    def __init__(self, database, device_credentials):
        if not isinstance(device_credentials, dict) or not device_credentials:
            raise ValueError("Authorized staging devices required")
        if len(device_credentials) > 4:
            raise ValueError("Maximum four authorized devices")
        if any(not isinstance(k, str) or not k or not isinstance(v, str) or
               len(v) < 16 for k, v in device_credentials.items()):
            raise ValueError("Invalid staging device credentials")
        self._credentials = dict(device_credentials)
        self.database = str(database)
        # The isolated ASGI service serializes every ledger operation with a
        # process-local RLock; its event loop can differ from bootstrap thread.
        self._db = sqlite3.connect(self.database, check_same_thread=False)
        self._db.execute("PRAGMA foreign_keys=ON")
        self._db.execute("""CREATE TABLE IF NOT EXISTS brain_events (
            seq INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL,
            device_id TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            payload_json TEXT NOT NULL,
            digest TEXT NOT NULL
        )""")
        self._db.commit()

    def close(self):
        self._db.close()

    def _authorize(self, device_id, credential):
        expected = self._credentials.get(device_id) if isinstance(device_id,str) else None
        if (not isinstance(expected, str) or not isinstance(credential, str)
                or not hmac.compare_digest(expected.encode("utf-8"), credential.encode("utf-8"))):
            raise PermissionError("Master-authorized device required")

    def append(self, *, device_id, credential, event_id, kind, created_at, payload):
        self._authorize(device_id, credential)
        if kind not in EVENT_TYPES:
            raise ValueError("Unknown immutable event kind")
        if (not isinstance(event_id, str) or not 8 <= len(event_id) <= 128
                or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_:."
                       for c in event_id)):
            raise ValueError("Invalid idempotent event ID")
        if type(created_at) is not int or created_at <= 0:
            raise ValueError("Explicit positive event timestamp required")
        data = _canonical(payload)
        digest = hashlib.sha256(json.dumps(
            [SCHEMA, event_id, kind, device_id, created_at, data],
            separators=(",", ":")).encode("utf-8")).hexdigest()
        with self._db:
            old = self._db.execute(
                "SELECT digest,seq FROM brain_events WHERE event_id=?",
                (event_id,)).fetchone()
            if old is not None:
                if not hmac.compare_digest(old[0], digest):
                    raise ValueError("Immutable event ID conflict")
                return {"sequence": old[1], "idempotent_replay": True}
            cur = self._db.execute("""INSERT INTO brain_events
                (event_id,kind,device_id,created_at,payload_json,digest)
                VALUES (?,?,?,?,?,?)""",
                (event_id, kind, device_id, created_at, data, digest))
        return {"sequence": cur.lastrowid, "idempotent_replay": False}

    def since(self, *, device_id, credential, sequence=0, limit=100):
        self._authorize(device_id, credential)
        if (type(sequence) is not int or sequence < 0 or type(limit) is not int
                or not 1 <= limit <= 500):
            raise ValueError("Invalid bounded sync cursor")
        rows = self._db.execute("""SELECT seq,event_id,kind,device_id,
                 created_at,payload_json FROM brain_events
                 WHERE seq>? ORDER BY seq LIMIT ?""",
                 (sequence, limit)).fetchall()
        return [dict(sequence=row[0], event_id=row[1], kind=row[2],
                     device_id=row[3], created_at=row[4],
                     payload=json.loads(row[5])) for row in rows]

    def encrypted_backup(self, *, device_id, credential, encryption_key):
        """Encrypt serialized SQLite bytes in RAM; never create plaintext backup."""
        self._authorize(device_id, credential)
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:
            raise RuntimeError("Encryption dependency missing; backup blocked") from exc
        if self._db.in_transaction:
            raise RuntimeError("Commit ledger transaction before backup")
        raw = self._db.serialize()
        return Fernet(encryption_key).encrypt(raw)

    @classmethod
    def restore_to_new(cls, *, destination, encrypted_blob, encryption_key,
                       device_credentials):
        """Staging restore only, never overwrite a nonempty/existing database."""
        try:
            from cryptography.fernet import Fernet
        except ImportError as exc:
            raise RuntimeError("Encryption dependency missing; restore blocked") from exc
        target = Path(destination)
        if target.exists() or target.is_symlink():
            raise FileExistsError("Restore must not overwrite an existing database")
        if not isinstance(encrypted_blob, bytes):
            raise ValueError("Encrypted backup bytes required")
        raw = Fernet(encryption_key).decrypt(encrypted_blob)
        temp = sqlite3.connect(":memory:")
        try:
            temp.deserialize(raw)
            match = temp.execute("PRAGMA integrity_check").fetchone()
            if match != ("ok",):
                raise ValueError("SQLite backup integrity check failed")
            schema = temp.execute("PRAGMA table_info(brain_events)").fetchall()
            names = {row[1] for row in schema}
            if not {"seq", "event_id", "kind", "device_id", "created_at",
                    "payload_json", "digest"} <= names:
                raise ValueError("Invalid Brain ledger schema")
            target.parent.mkdir(parents=True, exist_ok=True)
            import os
            fd=os.open(str(target),os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
            os.close(fd)
            try:
                dest=sqlite3.connect(str(target))
                try:
                    temp.backup(dest)
                finally:
                    dest.close()
            except BaseException:
                target.unlink(missing_ok=True)
                raise
        finally:
            temp.close()
        return cls(target, device_credentials)

    def audit(self):
        count, last = self._db.execute(
            "SELECT COUNT(*),COALESCE(MAX(seq),0) FROM brain_events").fetchone()
        return {"schema": SCHEMA, "stored_events": count,
                "last_sequence": last, "live_votes_enabled": False,
                "broker_requests": 0, "orders_sent": 0,
                "environment": "STAGING_ONLY_NOT_DEPLOYED"}
