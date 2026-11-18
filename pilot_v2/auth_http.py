"""Disabled-by-default V2 prototype for P-256 device challenge/session HTTP.

This module adds NO master enrollment route, no trusted key uploads, no broker
OAuth, and no order routes. Do NOT publish without ingress TLS, audited durable
global rate limiting, master provisioning and server hardening.
"""
import json
from fastapi import FastAPI, HTTPException, Request, Response
from .atomic_verified_login import AtomicVerifiedLogin
from .device_policy import valid_id
from .device_sessions import SessionDenied
from .device_verifier import DeviceProof

MAX_LOGIN_BODY = 1024


def create_pilot_auth_app(*, enabled=False, login=None, rate_gate=None):
    """A separate experimental protected ASGI app, not mounted in production."""
    if type(enabled) is not bool:
        raise ValueError("Explicit Boolean V2 auth flag required")
    app = FastAPI(title="BOT KING V2 Auth Pilot", docs_url=None,
                  redoc_url=None, openapi_url=None)
    if not enabled:
        return app
    if not isinstance(login, AtomicVerifiedLogin) or not callable(rate_gate):
        raise ValueError("Atomic P-256 login and approved rate gate required")

    def secure_request(request, action):
        # Reverse-proxy scheme only has meaning behind a trusted TLS gateway.
        if request.scope.get("scheme") != "https":
            raise HTTPException(status_code=403, detail="HTTPS required")
        if rate_gate(request, action) is not True:
            raise HTTPException(status_code=429, detail="Login rate limited")

    async def exact_body(request, keys):
        if request.headers.get("content-type", "").split(";", 1)[0].strip().lower() != "application/json":
            raise HTTPException(status_code=415, detail="JSON required")
        body = await request.body()
        if len(body) > MAX_LOGIN_BODY:
            raise HTTPException(status_code=413, detail="Login payload too large")
        try:
            data = json.loads(body)
        except (ValueError, UnicodeError):
            raise HTTPException(status_code=400, detail="Invalid login body") from None
        if type(data) is not dict or set(data) != set(keys):
            raise HTTPException(status_code=400, detail="Invalid login fields")
        return data

    @app.post("/v2-pilot/auth/challenge")
    async def challenge(request: Request, response: Response):
        secure_request(request, "challenge")
        data = await exact_body(request, ("device_id",))
        if not valid_id(data["device_id"]):
            raise HTTPException(status_code=400, detail="Invalid device ID")
        try:
            nonce = login.challenge(data["device_id"])
        except SessionDenied:
            raise HTTPException(status_code=403, detail="Device not authorized") from None
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return {"challenge": nonce}

    @app.post("/v2-pilot/auth/login")
    async def sign_in(request: Request, response: Response):
        secure_request(request, "login")
        data = await exact_body(request, ("device_id", "challenge", "signature"))
        if (not valid_id(data["device_id"]) or
                type(data["challenge"]) is not str or
                type(data["signature"]) is not str):
            raise HTTPException(status_code=400, detail="Invalid signed proof")
        try:
            bearer = login.login(DeviceProof(
                data["device_id"], data["challenge"], data["signature"]))
        except SessionDenied:
            raise HTTPException(status_code=403, detail="P-256 device proof denied") from None
        response.headers["Cache-Control"] = "no-store"
        response.headers["Pragma"] = "no-cache"
        return {"device_bearer": bearer}

    return app
