"""Box Six independent HTTP staging service; NEVER mount on Oracle Dhan gateway.

Use only on loopback with BOTKING_BRAIN_STAGING_ENABLED=1 and separately
provisioned per-device temporary staging proofs. This is NOT production Master
login integration, remote durable backup, or an active M vote.
"""
import os
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, ConfigDict, Field

from v3_brain_staging_memory import StagingBrainLedger, EVENT_TYPES


class EventInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(min_length=8, max_length=128)
    kind: str
    created_at: int = Field(gt=0)
    payload: dict


def create_staging_app(*, database, device_credentials, backup_key=None):
    """Construct isolated app with no brokerage or Oracle gateway dependencies."""
    api = FastAPI(title="BOT KING V3 Brain isolated STAGING", docs_url=None,
                  redoc_url=None, openapi_url=None)
    lock = threading.RLock()
    ledger = StagingBrainLedger(database, device_credentials)

    @api.on_event("shutdown")
    def close_ledger():
        with lock:
            ledger.close()

    def authorized(device_id, proof):
        if not device_id or not proof:
            raise HTTPException(status_code=401, detail="Authorized staging device required")
        try:
            ledger._authorize(device_id, proof)
        except PermissionError:
            raise HTTPException(status_code=403, detail="Invalid staging device credentials")

    @api.get("/brain/v1/health")
    async def health(x_brain_device: str | None = Header(default=None),
                     x_brain_proof: str | None = Header(default=None)):
        authorized(x_brain_device, x_brain_proof)
        with lock:
            return dict(ledger.audit(), service="M_BRAIN_STAGING",
                        status="STANDBY", voting_enabled=False,
                        recovery_status="OFFLINE_RESTORE_ONLY")

    @api.post("/brain/v1/events", status_code=201)
    async def events(body: EventInput, x_brain_device: str | None = Header(default=None),
                     x_brain_proof: str | None = Header(default=None)):
        authorized(x_brain_device, x_brain_proof)
        if body.kind not in EVENT_TYPES:
            raise HTTPException(status_code=422, detail="Unknown Brain event type")
        try:
            with lock:
                return ledger.append(device_id=x_brain_device, credential=x_brain_proof,
                                     event_id=body.event_id, kind=body.kind,
                                     created_at=body.created_at, payload=body.payload)
        except ValueError as e:
            raise HTTPException(status_code=409 if "conflict" in str(e) else 422,
                                detail=str(e))

    @api.get("/brain/v1/sync")
    async def sync(since: int = Query(default=0, ge=0),
                   limit: int = Query(default=100, ge=1, le=500),
                   x_brain_device: str | None = Header(default=None),
                   x_brain_proof: str | None = Header(default=None)):
        authorized(x_brain_device, x_brain_proof)
        with lock:
            rows = ledger.since(device_id=x_brain_device, credential=x_brain_proof,
                                sequence=since, limit=limit)
        return {"events": rows, "next_cursor": rows[-1]["sequence"] if rows else since,
                "m_vote": "STANDBY", "live_eligible": False}

    @api.get("/brain/v1/backup")
    async def backup(x_brain_device: str | None = Header(default=None),
                     x_brain_proof: str | None = Header(default=None)):
        authorized(x_brain_device, x_brain_proof)
        if backup_key is None:
            raise HTTPException(status_code=503, detail="Encrypted backup key unavailable")
        try:
            with lock:
                blob = ledger.encrypted_backup(device_id=x_brain_device,
                        credential=x_brain_proof, encryption_key=backup_key)
        except (ValueError, RuntimeError):
            raise HTTPException(status_code=503, detail="Encrypted backup unavailable")
        return Response(content=blob, media_type="application/octet-stream",
                        headers={"Cache-Control": "no-store",
                                 "Content-Disposition": "attachment; filename=brain-staging-backup.enc"})

    @api.get("/brain/v1/restore")
    async def restore_status(x_brain_device: str | None = Header(default=None),
                             x_brain_proof: str | None = Header(default=None)):
        authorized(x_brain_device, x_brain_proof)
        return {"state": "OFFLINE_ONLY", "automatic_restore": False,
                "overwrite_allowed": False, "m_vote": "STANDBY",
                "instruction": "Restore encrypted backup into NEW isolated staging database after offline review"}

    return api


def run_loopback():
    """Explicit local-only launch; no module-import side effects or prod routes."""
    if os.environ.get("BOTKING_BRAIN_STAGING_ENABLED") != "1":
        raise RuntimeError("Staging disabled: set explicit enable flag")
    device_proofs = {}
    for n in range(1, 5):
        proof = os.environ.get(f"BOTKING_BRAIN_PHONE_{n}_PROOF", "")
        if proof:
            device_proofs[f"phone{n}"] = proof
    if not device_proofs:
        raise RuntimeError("No staging phone credentials configured")
    backup_key = os.environ.get("BOTKING_BRAIN_BACKUP_FERNET_KEY")
    if not backup_key:
        raise RuntimeError("Encrypted staging backup key required")
    database = os.environ.get("BOTKING_BRAIN_STAGING_DB", "")
    if not database or not Path(database).is_absolute():
        raise RuntimeError("Explicit absolute isolated staging database path required")
    import uvicorn
    app = create_staging_app(database=database, device_credentials=device_proofs,
                             backup_key=backup_key.encode("ascii"))
    uvicorn.run(app, host="127.0.0.1", port=8766, proxy_headers=False,
                access_log=False, workers=1)


if __name__ == "__main__":
    run_loopback()
