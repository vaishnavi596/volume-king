"""Optional BOT KING 226 device authentication API router.

NOT included by the production server by default. Only mount after explicit
owner-approved enrollment setup, HTTPS ingress and persistence review.
"""
from fastapi import APIRouter, Header, Response
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from .device_login_226 import DeviceLoginError
from .device_registry_226 import DeviceRegistryError


class ChallengeRequest(BaseModel):
    device_id: str = Field(min_length=16, max_length=128)


class ProofRequest(ChallengeRequest):
    challenge: str = Field(min_length=32, max_length=256)
    signature: str = Field(min_length=64, max_length=256)


def authorize_readonly_device_session(registry, authorization):
    """Validate an opaque Bearer token; never trust a client-supplied device ID."""
    import re
    if (not isinstance(authorization, str)
            or re.fullmatch(r"Bearer [A-Za-z0-9_-]{32,256}", authorization) is None):
        return False
    return registry.validate_bearer_session(authorization[7:])


def build_device_auth_router(registry, login):
    """Routes intentionally exclude enrollment; owner must approve it out-of-band."""
    local_router = APIRouter(prefix="/v2/device", tags=["device-auth"])

    def no_store_error(status_code, detail):
        # FastAPI's injected Response headers do not survive HTTPException handling.
        # Set no-store on the actual error response, including unauthorized failures.
        return JSONResponse(status_code=status_code, content={"detail": detail},
                            headers={"Cache-Control": "no-store"})

    @local_router.post("/challenge")
    def challenge(body: ChallengeRequest, response: Response):
        response.headers["Cache-Control"] = "no-store"
        try:
            value = login.begin(body.device_id)
        except DeviceLoginError:
            return no_store_error(403, "Device authentication unavailable")
        return {"challenge": value, "expires_in_seconds": 120}

    @local_router.post("/session")
    def session(body: ProofRequest, response: Response):
        response.headers["Cache-Control"] = "no-store"
        try:
            token = login.complete(body.device_id, body.challenge, body.signature)
        except (DeviceLoginError, DeviceRegistryError):
            return no_store_error(403, "Device authentication failed")
        return {"access_token": token, "token_type": "bearer", "expires_in_seconds": 900}

    @local_router.post("/validate")
    def validate(body: ChallengeRequest, response: Response, authorization: str | None = Header(default=None)):
        response.headers["Cache-Control"] = "no-store"
        if not isinstance(authorization, str) or not __import__("re").fullmatch(r"Bearer [A-Za-z0-9_-]{32,256}", authorization):
            return no_store_error(401, "Bearer token required")
        # The session must belong to the exact enrolled device in the request.
        if not registry.validate_session(body.device_id, authorization[7:]):
            return no_store_error(401, "Device session invalid")
        return {"authenticated": True}

    return local_router
