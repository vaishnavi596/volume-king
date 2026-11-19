"""V2-only HTTP adapter for externally trusted P-256 and Dhan snapshot inputs.

No enrollment route, no provider SDK calls, no V1 imports. Do not expose to
production until independently provisioned master/device and Dhan producer
have been reviewed and tested.
"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse

from .api_contract import validate_snapshot, ContractError
from .atomic_verified_login import AtomicVerifiedLogin
from .device_verifier import DeviceProof
from .device_sessions import SessionDenied
from .unified_data_pipeline import PipelineUnavailable

MAX_BODY = 1024
MAX_TOKEN = 160


def create_trusted_app(*, login, snapshot_provider):
    if not isinstance(login, AtomicVerifiedLogin) or not callable(snapshot_provider):
        raise ValueError("Atomic trusted login and internal provider required")
    app = FastAPI(title="BOT KING V2 Trusted Adapter", docs_url=None,
                  redoc_url=None, openapi_url=None)

    async def json_body(request, keys):
        raw = await request.body()
        if not raw or len(raw) > MAX_BODY:
            raise HTTPException(status_code=413, detail="Invalid request size")
        import json
        try:
            data = json.loads(raw)
        except (ValueError, UnicodeError):
            raise HTTPException(status_code=400, detail="Invalid request")
        if type(data) is not dict or set(data) != keys:
            raise HTTPException(status_code=400, detail="Invalid request shape")
        if any(type(v) is not str or len(v) > 400 for v in data.values()):
            raise HTTPException(status_code=400, detail="Invalid request field")
        return data

    @app.post("/v2-pilot/auth/challenge")
    async def challenge(request: Request):
        data = await json_body(request, {"device_id"})
        try:
            nonce = login.challenge(data["device_id"])
        except (SessionDenied, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Device not authorized") from None
        return JSONResponse({"challenge": nonce}, headers={"Cache-Control": "no-store"})

    @app.post("/v2-pilot/auth/login")
    async def authorize(request: Request):
        data = await json_body(request, {"device_id", "challenge", "signature"})
        try:
            token = login.login(DeviceProof(**data))
        except (SessionDenied, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Device proof rejected") from None
        return JSONResponse({"device_bearer": token},
                            headers={"Cache-Control": "no-store"})

    def read_feed(request, feed):
        authorization = request.headers.get("authorization", "")
        if (not authorization.startswith("Bearer ") or authorization.count(" ") != 1 or
                not 40 <= len(authorization[7:]) <= MAX_TOKEN):
            raise HTTPException(status_code=401, detail="Verified device bearer required")
        try:
            device = login.read_feed(authorization[7:], feed)
        except SessionDenied:
            raise HTTPException(status_code=403, detail="Device access denied") from None
        try:
            snapshot = validate_snapshot(snapshot_provider(device, feed))
        except (ContractError, ValueError, TypeError, PipelineUnavailable):
            raise HTTPException(status_code=503, detail="Read-only Dhan snapshot unavailable") from None
        return JSONResponse(snapshot, headers={"Cache-Control": "no-store"})

    @app.get("/v2-pilot/indices")
    def indices(request: Request):
        return read_feed(request, "indices")

    @app.get("/v2-pilot/quotes")
    def quotes(request: Request):
        return read_feed(request, "quotes")

    return app
