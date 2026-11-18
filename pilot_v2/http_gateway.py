"""Off-by-default read-only V2 FastAPI staging shell. No Oracle deployment."""
from fastapi import FastAPI, HTTPException, Request
from .api_contract import ENABLED_BY_DEFAULT,validate_snapshot
from .device_sessions import SessionDenied
from .durable_device_sessions import DurableDeviceSessions

def create_pilot_app(*,enabled=ENABLED_BY_DEFAULT,sessions=None,snapshot_provider=None):
    if type(enabled) is not bool:
        raise ValueError("Boolean feature flag required")
    app=FastAPI(title="BOT KING V2 Pilot",docs_url=None,redoc_url=None,openapi_url=None)
    if not enabled:
        return app
    if not isinstance(sessions,DurableDeviceSessions) or not callable(snapshot_provider):
        raise ValueError("Trusted durable sessions and internal data provider required")
    def get_feed(request,feed):
        authorization=request.headers.get("authorization","")
        if not authorization.startswith("Bearer ") or authorization.count(" ")!=1:
            raise HTTPException(status_code=401,detail="Device bearer required")
        try:
            device=sessions.authorize(authorization[7:],feed)
        except SessionDenied:
            raise HTTPException(status_code=403,detail="Unauthorized device or feed") from None
        return validate_snapshot(snapshot_provider(device,feed))
    @app.get("/v2-pilot/quotes")
    def quotes(request:Request):
        return get_feed(request,"quotes")
    @app.get("/v2-pilot/indices")
    def indices(request:Request):
        return get_feed(request,"indices")
    return app
