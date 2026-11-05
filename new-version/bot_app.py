"""Single-file monolithic BOT KING gateway v2.3.0 (Optimized & Extended Idle Timeout)"""
import asyncio
import hmac
import math
import os
import secrets
import threading
import time
from collections import deque
from contextlib import asynccontextmanager, suppress
from datetime import date
from typing import Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, SecretStr

from market_feed import AngelFeed, FeedError, SessionExpired


class Login(BaseModel):
    api_key: SecretStr
    client_code: SecretStr
    pin: SecretStr
    totp: SecretStr


class Symbol(BaseModel):
    symbol: str = Field(min_length=1, max_length=32, pattern=r"^[A-Z0-9&_-]+$")


class History(Symbol):
    interval: Literal["1m", "3m", "5m", "15m", "30m", "1h", "1d"]
    period: Literal["1d", "5d", "7d", "1mo", "3mo"]


class Options(Symbol):
    expiry: date
    spot: float = Field(gt=0)


class OptionHistory(Symbol):
    expiry: date
    strike: float = Field(gt=0)
    side: Literal["CE", "PE"]


def create_app(pairing_key=None, feed=None, clock=time.monotonic):
    pairing_key = pairing_key or os.environ.get("BOTKING_PAIRING_KEY", "")
    if len(pairing_key) < 32:
        raise RuntimeError("BOTKING_PAIRING_KEY must contain at least 32 characters")
    feed = feed or AngelFeed()
    lock = threading.RLock()
    state = {"token": "", "issued": 0.0, "last": 0.0}
    attempts = deque()

    @asynccontextmanager
    async def lifespan(app):
        async def expire_idle():
            while True:
                await asyncio.sleep(60)
                if lock.acquire(blocking=False):
                    try:
                        # Idle timeout extended to 2 hours (7200s) to prevent frequent disconnections
                        if state["token"] and (clock() - state["issued"] >= 8 * 3600 or clock() - state["last"] >= 7200):
                            clear()
                    finally:
                        lock.release()
        task = asyncio.create_task(expire_idle())
        try:
            yield
        finally:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            clear()

    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request, exc):
        return JSONResponse(status_code=422, content={"detail": "Invalid request fields"})

    @app.middleware("http")
    async def body_limit(request, call_next):
        try:
            length = int(request.headers.get("content-length", "0"))
        except ValueError:
            return JSONResponse(status_code=400, content={"detail": "Invalid request"})
        if request.url.path.startswith("/v1/"):
            if length > 8192:
                return JSONResponse(status_code=413, content={"detail": "Request too large"})
            body = await request.body()
            if len(body) > 8192:
                return JSONResponse(status_code=413, content={"detail": "Request too large"})
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        return response

    def clear():
        state["token"] = ""
        feed.disconnect()
        feed.instruments = None
        getattr(feed, "resolved", {}).clear()

    def authorized(header):
        now = clock()
        if state["token"] and (now - state["issued"] >= 8 * 3600 or now - state["last"] >= 7200):
            clear()
        supplied = (header or "").removeprefix("Bearer ")
        if not state["token"] or not hmac.compare_digest(supplied.encode(), state["token"].encode()) or not (header or "").startswith("Bearer "):
            raise HTTPException(401, "Session expired; reconnect")
        state["last"] = now

    def run(header, method, *args):
        if not lock.acquire(blocking=False):
            raise HTTPException(429, "Server busy; retry later")
        try:
            authorized(header)
            if any(isinstance(v, float) and not math.isfinite(v) for v in args):
                raise HTTPException(422, "Invalid market value")
            try:
                return getattr(feed, method)(*args)
            except SessionExpired:
                clear()
                raise HTTPException(401, "Broker session expired; reconnect") from None
            except Exception:
                raise HTTPException(502, "Market data unavailable; verify session and listed contract") from None
        finally:
            lock.release()

    @app.get("/health")
    def health():
        return {"status": "ok", "service": "BOT KING", "protocol": 1,
                "broker_connected": bool(state["token"] and feed.connected
                                       and clock() - state["issued"] < 8 * 3600
                                       and clock() - state["last"] < 7200),
                "live_orders_enabled": False}

    @app.post("/v1/login")
    def login(body: Login, x_botking_key: Optional[str] = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        if not lock.acquire(blocking=False):
            raise HTTPException(429, "Server busy; retry later")
        try:
            now = clock()
            while attempts and now - attempts[0] >= 60:
                attempts.popleft()
            if len(attempts) >= 5:
                raise HTTPException(429, "Wait before reconnecting")
            attempts.append(now)
            values = [body.api_key.get_secret_value(), body.client_code.get_secret_value(),
                      body.pin.get_secret_value(), body.totp.get_secret_value()]
            if not all(0 < len(v) <= 256 for v in values) or not values[3].isdigit() or len(values[3]) != 6:
                raise HTTPException(422, "Invalid login fields")
            clear()
            try:
                feed.connect(*values)
            except Exception:
                clear()
                raise HTTPException(401, "Broker login failed; check credentials and current TOTP") from None
            finally:
                values.clear()
            state.update(token=secrets.token_urlsafe(32), issued=clock(), last=clock())
            return {"session": state["token"], "expires_in": 8 * 3600, "live_orders_enabled": False}
        finally:
            lock.release()

    @app.post("/v1/logout")
    def logout(authorization: Optional[str] = Header(default=None)):
        with lock:
            authorized(authorization)
            clear()
        return {"status": "disconnected"}

    @app.post("/v1/history")
    def history(body: History, authorization: Optional[str] = Header(default=None)):
        return run(authorization, "history", body.symbol, body.interval, body.period)

    @app.post("/v1/expiries")
    def expiries(body: Symbol, authorization: Optional[str] = Header(default=None)):
        return run(authorization, "expiries", body.symbol)

    @app.post("/v1/options")
    def options(body: Options, authorization: Optional[str] = Header(default=None)):
        return run(authorization, "option_chain", body.symbol, body.expiry.isoformat(), body.spot)

    @app.post("/v1/option-history")
    def option_history(body: OptionHistory, authorization: Optional[str] = Header(default=None)):
        return run(authorization, "option_history", body.symbol, body.expiry.isoformat(), body.strike, body.side)

    return app
