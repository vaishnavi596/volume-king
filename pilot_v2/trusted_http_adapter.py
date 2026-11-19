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


def create_trusted_app(*, login, snapshot_provider, manual_snapshot_provider=None,
                       master_roster_updater=None):
    if not isinstance(login, AtomicVerifiedLogin) or not callable(snapshot_provider):
        raise ValueError("Atomic trusted login and internal provider required")
    if manual_snapshot_provider is not None and not callable(manual_snapshot_provider):
        raise ValueError("Verified manual read provider required")
    if master_roster_updater is not None and not callable(master_roster_updater):
        raise ValueError("Trusted Master roster updater required")
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

    @app.get("/v2-pilot/health")
    def health():
        # Process readiness, not proof of fresh Dhan data.
        return JSONResponse({"status": "authenticated_gateway_ready",
                             "live_data_verified": False,
                             "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    def bearer_from_request(request):
        authorization = request.headers.get("authorization", "")
        if (not authorization.startswith("Bearer ") or authorization.count(" ") != 1 or
                not 40 <= len(authorization[7:]) <= MAX_TOKEN):
            raise HTTPException(status_code=401, detail="Verified device bearer required")
        return authorization[7:]

    def read_feed(request, feed, *, manual=False):
        token = bearer_from_request(request)
        try:
            device = login.read_feed(token, feed)
        except SessionDenied:
            raise HTTPException(status_code=403, detail="Device access denied") from None
        try:
            provider = manual_snapshot_provider if manual else snapshot_provider
            if provider is None:
                raise PipelineUnavailable("Manual read not connected")
            snapshot = validate_snapshot(provider(device, feed))
        except (ContractError, ValueError, TypeError, PipelineUnavailable):
            raise HTTPException(status_code=503, detail="Read-only Dhan snapshot unavailable") from None
        return JSONResponse(snapshot, headers={"Cache-Control": "no-store"})

    @app.get("/v2-pilot/indices")
    def indices(request: Request):
        return read_feed(request, "indices")

    @app.get("/v2-pilot/quotes")
    def quotes(request: Request):
        return read_feed(request, "quotes")

    @app.post("/v2-pilot/auth/logout")
    def logout(request: Request):
        token = bearer_from_request(request)
        try:
            login._sessions.logout(token)
        except (SessionDenied, ValueError, TypeError):
            raise HTTPException(status_code=403, detail="Device sign-out denied") from None
        return JSONResponse({"signed_out": True}, headers={"Cache-Control": "no-store"})

    @app.post("/v2-pilot/manual/{feed}")
    def manual_read(feed: str, request: Request):
        if feed not in ("indices", "quotes"):
            raise HTTPException(status_code=404, detail="Unsupported manual feed")
        return read_feed(request, feed, manual=True)

    @app.post("/v2-pilot/master/roster")
    async def master_update_roster(request: Request):
        token = bearer_from_request(request)
        try:
            login._sessions.authorize_master(token)
        except SessionDenied:
            raise HTTPException(status_code=403, detail="Master authorization required") from None
        if master_roster_updater is None:
            raise HTTPException(status_code=503, detail="Private roster control unavailable")
        raw = await request.body()
        if not raw or len(raw) > 4096:
            raise HTTPException(status_code=413, detail="Invalid roster size")
        import json
        try:
            parsed = json.loads(raw)
        except (UnicodeError, ValueError, TypeError):
            raise HTTPException(status_code=400, detail="Invalid roster JSON") from None
        if type(parsed) is not dict or set(parsed) != {"symbols"} or type(parsed["symbols"]) is not list:
            raise HTTPException(status_code=422, detail="Invalid roster request")
        try:
            count = master_roster_updater(parsed["symbols"])
        except (ValueError, TypeError):
            raise HTTPException(status_code=422, detail="Invalid selected equities") from None
        except (PipelineUnavailable, OSError):
            raise HTTPException(status_code=503, detail="Private roster update unavailable") from None
        return JSONResponse({"selected_equities": count},
                            headers={"Cache-Control": "no-store"})

    return app
