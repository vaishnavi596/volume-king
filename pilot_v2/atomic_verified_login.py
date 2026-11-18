"""Atomic P-256 proof-to-session login for one-host SQLite V2 prototypes.

No HTTP API and no live Dhan/order access. A single BEGIN IMMEDIATE protects
nonce consumption, the CURRENT enabled key, and issuance of a revocable session
against concurrent rekey/revoke by other local worker processes.
"""
import hashlib
import secrets
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec

from .device_sessions import SessionDenied
from .device_verifier import DeviceProof, P256ChallengeVerifier, decode_b64
from .durable_challenges import DurableP256ChallengeVerifier
from .durable_device_sessions import DurableDeviceSessions


class AtomicVerifiedLogin:
    def __init__(self, verifier, sessions):
        if (not isinstance(verifier, DurableP256ChallengeVerifier)
                or not isinstance(sessions, DurableDeviceSessions)
                or verifier._path != sessions._path):
            raise ValueError("One shared local SQLite verifier/session store required")
        self._verifier = verifier
        self._sessions = sessions

    def challenge(self, device_id):
        # The trusted key resolver is checked by the durable verifier.
        return self._verifier.challenge(device_id)

    def login(self, proof):
        if not isinstance(proof, DeviceProof) or type(proof.device_id) is not str:
            raise SessionDenied("P-256 signed device proof required")
        device = proof.device_id
        token = secrets.token_urlsafe(48)
        with self._sessions._db() as db:
            try:
                db.execute("BEGIN IMMEDIATE")
                pending = db.execute(
                    "SELECT digest,issued_at,expires_at FROM login_challenge WHERE device=?",
                    (device,)).fetchone()
                db.execute("DELETE FROM login_challenge WHERE device=?", (device,))
                now = self._sessions._now()
                approved = db.execute(
                    "SELECT master,enabled FROM devices WHERE device=?",
                    (device,)).fetchone()
                # Verify while holding the same write lease used by durable key
                # rotation. Never trust a separately cached delegated public key.
                if pending is None or now < pending[1] or now >= pending[2]:
                    raise SessionDenied("Challenge missing, expired or consumed")
                if approved is None or approved[1] != 1:
                    raise SessionDenied("Device disabled or removed")
                raw = decode_b64(proof.challenge, limit=48)
                if len(raw) != 32 or hashlib.sha256(
                        proof.challenge.encode("ascii")).hexdigest() != pending[0]:
                    raise SessionDenied("Challenge mismatch")
                if approved[0] == 1:
                    key = self._verifier._keys.get(device)
                    if key is None:
                        raise SessionDenied("Master key not independently provisioned")
                else:
                    row = db.execute(
                        "SELECT public_der FROM device_keys WHERE device=?", (device,)
                    ).fetchone()
                    if row is None:
                        raise SessionDenied("Delegated key not enrolled")
                    try:
                        key = serialization.load_der_public_key(row[0])
                    except (ValueError, TypeError):
                        raise SessionDenied("Invalid current P-256 key") from None
                    if not isinstance(key, ec.EllipticCurvePublicKey) or not isinstance(
                            key.curve, ec.SECP256R1):
                        raise SessionDenied("Invalid current P-256 key")
                signature = decode_b64(proof.signature, limit=400)
                try:
                    key.verify(signature, P256ChallengeVerifier.signed_message(
                        device, proof.challenge), ec.ECDSA(hashes.SHA256()))
                except (InvalidSignature, ValueError):
                    raise SessionDenied("Device signature not verified") from None
                # Session replacement is atomic with current-key check.
                db.execute("DELETE FROM sessions WHERE device=?", (device,))
                db.execute("INSERT INTO sessions(digest,device,expiry) VALUES(?,?,?)",
                           (self._sessions._digest(token), device,
                            now + self._sessions._ttl))
                db.execute("COMMIT")
                return token
            except SessionDenied:
                # Commit nonce removal, but no session or key mutations.
                db.execute("COMMIT")
                raise
            except BaseException:
                db.execute("ROLLBACK")
                raise

    def read_feed(self, token, feed):
        return self._sessions.authorize(token, feed)
