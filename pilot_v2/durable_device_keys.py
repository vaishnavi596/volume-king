"""V2 offline, master-approved P-256 key enrollment and rotation.

All mutations use the same local SQLite file as DurableDeviceSessions.
No remote route, broker, payments, or live token. Real provisioning must
authenticate the owner; never deserialize a claimed admin device from HTTP.
"""
import hashlib
import secrets
import sqlite3
from dataclasses import dataclass

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .device_policy import valid_id
from .device_sessions import SessionDenied
from .device_verifier import DeviceProof, P256ChallengeVerifier, decode_b64, encode_b64
from .durable_device_sessions import DurableDeviceSessions

@dataclass(frozen=True)
class PendingKeyApproval:
    challenge: str
    fingerprint: str

class DurableDeviceKeys:
    """One-host transactional key trust lifecycle; prototype only.

    Completion verifies current master session and possession of the candidate
    private key BEFORE changing the trusted key, grants, or existing sessions.
    """
    def __init__(self, sessions, *, ttl=90):
        if not isinstance(sessions, DurableDeviceSessions) or type(ttl) is not int or not 20 <= ttl <= 120:
            raise ValueError("Durable sessions and safe TTL required")
        self._sessions = sessions
        self._ttl = ttl
        with self._sessions._db() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS device_keys(
                device TEXT PRIMARY KEY, public_der BLOB NOT NULL,
                generation INTEGER NOT NULL CHECK(generation > 0))""")
            db.execute("""CREATE TABLE IF NOT EXISTS pending_device_keys(
                device TEXT PRIMARY KEY, public_der BLOB NOT NULL,
                challenge_digest TEXT NOT NULL, expires REAL NOT NULL)""")

    @staticmethod
    def _valid_der(der):
        if type(der) is not bytes or not 70 <= len(der) <= 512:
            raise SessionDenied("Invalid enrolled public key")
        try:
            k=serialization.load_der_public_key(der)
        except (TypeError, ValueError):
            raise SessionDenied("Invalid P-256 public key") from None
        if not isinstance(k,ec.EllipticCurvePublicKey) or not isinstance(k.curve,ec.SECP256R1):
            raise SessionDenied("Expected P-256 device key")
        if k.public_bytes(serialization.Encoding.DER,
                          serialization.PublicFormat.SubjectPublicKeyInfo)!=der:
            raise SessionDenied("Noncanonical P-256 public key")
        return k

    def request(self, master_bearer, device_id, new_public_der):
        if not valid_id(device_id):
            raise SessionDenied("Invalid device")
        self._valid_der(new_public_der)
        nonce=encode_b64(secrets.token_bytes(32))
        digest=hashlib.sha256(nonce.encode("ascii")).hexdigest()
        with self._sessions._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                owner=self._sessions._identity_tx(db, master_bearer, master=True)
                if device_id==owner:
                    raise SessionDenied("Master key rotation requires separate recovery policy")
                existing=db.execute("SELECT master FROM devices WHERE device=?",(device_id,)).fetchone()
                if existing and existing[0]==1:
                    raise SessionDenied("Cannot edit master key")
                if existing is None and db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]>=3:
                    raise SessionDenied("Maximum three devices")
                expires=self._sessions._now()+self._ttl
                db.execute("""INSERT INTO pending_device_keys
                    (device,public_der,challenge_digest,expires) VALUES(?,?,?,?)
                    ON CONFLICT(device) DO UPDATE SET
                    public_der=excluded.public_der,challenge_digest=excluded.challenge_digest,
                    expires=excluded.expires""",(device_id,new_public_der,digest,expires))
                db.execute("COMMIT")
            except BaseException:
                db.execute("ROLLBACK")
                raise
        return PendingKeyApproval(nonce,hashlib.sha256(new_public_der).hexdigest())

    def complete(self, master_bearer, proof, feeds, *, enabled=True):
        if (not isinstance(proof,DeviceProof) or type(proof.device_id) is not str
                or type(enabled) is not bool):
            raise SessionDenied("Invalid key ownership proof")
        normalized=self._sessions._feeds(feeds)
        with self._sessions._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                owner=self._sessions._identity_tx(db,master_bearer,master=True)
                if proof.device_id==owner:
                    raise SessionDenied("Cannot rotate master")
                row=db.execute("""SELECT public_der,challenge_digest,expires
                     FROM pending_device_keys WHERE device=?""",
                     (proof.device_id,)).fetchone()
                # The pending proof is single-use even if signature is wrong.
                db.execute("DELETE FROM pending_device_keys WHERE device=?",(proof.device_id,))
                now=self._sessions._now()
                if row is None or now>=row[2]:
                    raise SessionDenied("Key approval absent or expired")
                raw=decode_b64(proof.challenge,limit=48)
                if len(raw)!=32 or hashlib.sha256(
                        proof.challenge.encode("ascii")).hexdigest()!=row[1]:
                    raise SessionDenied("Key challenge mismatch")
                key=self._valid_der(row[0])
                signature=decode_b64(proof.signature,limit=400)
                try:
                    key.verify(signature,P256ChallengeVerifier.signed_message(
                        proof.device_id,proof.challenge),ec.ECDSA(hashes.SHA256()))
                except (InvalidSignature,ValueError):
                    raise SessionDenied("Key possession proof invalid") from None
                old=db.execute("SELECT master FROM devices WHERE device=?",
                               (proof.device_id,)).fetchone()
                if old and old[0]==1:
                    raise SessionDenied("Cannot rotate master")
                if old is None and db.execute("SELECT COUNT(*) FROM devices").fetchone()[0]>=3:
                    raise SessionDenied("Maximum three devices")
                db.execute("""INSERT INTO devices(device,master,enabled,feeds)
                    VALUES(?,0,?,?) ON CONFLICT(device) DO UPDATE SET
                    enabled=excluded.enabled,feeds=excluded.feeds""",
                    (proof.device_id,int(enabled),normalized))
                db.execute("""INSERT INTO device_keys(device,public_der,generation)
                    VALUES(?,?,1) ON CONFLICT(device) DO UPDATE SET
                    public_der=excluded.public_der,generation=device_keys.generation+1""",
                    (proof.device_id,row[0]))
                # Revoke all old sessions and outstanding sign-in challenges on
                # rotation; new key activates only after verified possession.
                db.execute("DELETE FROM sessions WHERE device=?",(proof.device_id,))
                db.execute("DELETE FROM login_challenge WHERE device=?",(proof.device_id,))
                db.execute("COMMIT")
            except SessionDenied:
                # Preserve consume-on-failure semantics. Roll back all other
                # state, then atomically remove the attempted approval.
                db.execute("ROLLBACK")
                with self._sessions._db() as cleanup:
                    cleanup.execute("DELETE FROM pending_device_keys WHERE device=?",
                                    (proof.device_id,))
                raise
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def public_key(self, device_id):
        """Trusted server-internal resolver; never a self-registering route."""
        if not valid_id(device_id):
            raise SessionDenied("Invalid device")
        with self._sessions._db() as db:
            row=db.execute("""SELECT k.public_der FROM device_keys k
                JOIN devices d ON d.device=k.device
                WHERE k.device=? AND d.enabled=1""",(device_id,)).fetchone()
        return row[0] if row else None
