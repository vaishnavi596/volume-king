"""Optional BOT KING 226 device authentication API router.

NOT included by the production server by default. Only mount after explicit
owner-approved enrollment setup, HTTPS ingress and persistence review.
"""
from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from .device_login_226 import DeviceLoginError
from .device_registry_226 import DeviceRegistryError


class ChallengeRequest(BaseModel):
    device_id: str = Field(min_length=16, max_length=128)


class ProofRequest(ChallengeRequest):
    challenge: str = Field(min_length=32, max_length=256)
    signature: str = Field(min_length=64, max_length=256)


def build_device_auth_router(registry, login):
    """Routes intentionally exclude enrollment; owner must approve it out-of-band."""
    local_router = APIRouter(prefix="/v2/device", tags=["device-auth"])

    @local_router.post("/challenge")
    def challenge(body: ChallengeRequest):
        try:
            value = login.begin(body.device_id)
        except DeviceLoginError:
            raise HTTPException(403, "Device authentication unavailable") from None
        return {"challenge": value, "expires_in_seconds": 120}

    @local_router.post("/session")
    def session(body: ProofRequest):
        try:
            token = login.complete(body.device_id, body.challenge, body.signature)
        except (DeviceLoginError, DeviceRegistryError):
            raise HTTPException(403, "Device authentication failed") from None
        return {"access_token": token, "token_type": "bearer", "expires_in_seconds": 900}

    @local_router.post("/validate")
    def validate(body: ChallengeRequest, authorization: str | None = Header(default=None)):
        if not authorization or not authorization.startswith("Bearer "):
            raise HTTPException(401, "Bearer token required")
        token = authorization[7:]
        if not registry.validate_session(body.device_id, token):
            raise HTTPException(401, "Device session invalid")
        return {"authenticated": True}

    return local_router
