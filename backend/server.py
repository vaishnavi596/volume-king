"""Single-file monolithic BOT KING gateway v2.3.0
- Extended 2-Hour Idle Session Timeout
- Dedicated Heartbeat / Ping Support
- Hardened Single-Owner Security
"""
import asyncio
import hmac
import math
import os
import secrets
import threading
import time
import requests
from urllib.parse import quote
from fastapi.responses import HTMLResponse
from collections import deque
from contextlib import asynccontextmanager, suppress
from datetime import date, datetime, timedelta, timezone
from typing import Literal, Optional

from fastapi import FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, SecretStr

try:
    from .market_feed import AngelFeed, FeedError, SessionExpired
except ImportError:
    try:
        from market_feed import AngelFeed, FeedError, SessionExpired
    except ImportError:
        from src.market_feed import AngelFeed, FeedError, SessionExpired
try:
    from .dhan_feed import DhanFeed, DhanFeedError
except ImportError:  # Direct execution on the Oracle backend directory
    from dhan_feed import DhanFeed, DhanFeedError
from pathlib import Path


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


DHAN_VERIFIED_INSTRUMENTS = {
    "NIFTY": ("IDX_I", 13, "INDEX"),
    "RELIANCE": ("NSE_EQ", 2885, "EQUITY"),
    "HDFCBANK": ("NSE_EQ", 1333, "EQUITY"),
    "ICICIBANK": ("NSE_EQ", 4963, "EQUITY"),
    "TCS": ("NSE_EQ", 11536, "EQUITY"),
    "INFY": ("NSE_EQ", 1594, "EQUITY"),
    "BHARTIARTL": ("NSE_EQ", 10604, "EQUITY"),
    "SBIN": ("NSE_EQ", 3045, "EQUITY"),
    "ITC": ("NSE_EQ", 1660, "EQUITY"),
    "LT": ("NSE_EQ", 11483, "EQUITY"),
    "AXISBANK": ("NSE_EQ", 5900, "EQUITY"),
    "KOTAKBANK": ("NSE_EQ", 1922, "EQUITY"),
    "HINDUNILVR": ("NSE_EQ", 1394, "EQUITY"),
    "BAJFINANCE": ("NSE_EQ", 317, "EQUITY"),
    "BAJAJFINSV": ("NSE_EQ", 16675, "EQUITY"),
    "MARUTI": ("NSE_EQ", 10999, "EQUITY"),
    "M&M": ("NSE_EQ", 2031, "EQUITY"),
    "TITAN": ("NSE_EQ", 3506, "EQUITY"),
    "SUNPHARMA": ("NSE_EQ", 3351, "EQUITY"),
    "ULTRACEMCO": ("NSE_EQ", 11532, "EQUITY"),
    "ASIANPAINT": ("NSE_EQ", 236, "EQUITY"),
    "NTPC": ("NSE_EQ", 11630, "EQUITY"),
    "POWERGRID": ("NSE_EQ", 14977, "EQUITY"),
    "TMPV": ("NSE_EQ", 3456, "EQUITY"),
    "TMCV": ("NSE_EQ", 759782, "EQUITY"),
    "TATASTEEL": ("NSE_EQ", 3499, "EQUITY"),
    "JSWSTEEL": ("NSE_EQ", 11723, "EQUITY"),
    "HCLTECH": ("NSE_EQ", 7229, "EQUITY"),
    "WIPRO": ("NSE_EQ", 3787, "EQUITY"),
    "TECHM": ("NSE_EQ", 13538, "EQUITY"),
    "NESTLEIND": ("NSE_EQ", 17963, "EQUITY"),
    "HINDALCO": ("NSE_EQ", 1363, "EQUITY"),
    "ONGC": ("NSE_EQ", 2475, "EQUITY"),
    "COALINDIA": ("NSE_EQ", 20374, "EQUITY"),
    "ADANIENT": ("NSE_EQ", 25, "EQUITY"),
    "ADANIPORTS": ("NSE_EQ", 15083, "EQUITY"),
    "BEL": ("NSE_EQ", 383, "EQUITY"),
    "TRENT": ("NSE_EQ", 1964, "EQUITY"),
    "EICHERMOT": ("NSE_EQ", 910, "EQUITY"),
    "GRASIM": ("NSE_EQ", 1232, "EQUITY"),
    "CIPLA": ("NSE_EQ", 694, "EQUITY"),
    "DRREDDY": ("NSE_EQ", 881, "EQUITY"),
    "APOLLOHOSP": ("NSE_EQ", 157, "EQUITY"),
    "DIVISLAB": ("NSE_EQ", 10940, "EQUITY"),
    "SBILIFE": ("NSE_EQ", 21808, "EQUITY"),
    "HDFCLIFE": ("NSE_EQ", 467, "EQUITY"),
    "BAJAJ-AUTO": ("NSE_EQ", 16669, "EQUITY"),
    "HEROMOTOCO": ("NSE_EQ", 1348, "EQUITY"),
    "BRITANNIA": ("NSE_EQ", 547, "EQUITY"),
    "INDUSINDBK": ("NSE_EQ", 5258, "EQUITY"),
    "SHRIRAMFIN": ("NSE_EQ", 4306, "EQUITY"),
    "BPCL": ("NSE_EQ", 526, "EQUITY"),
}


class DhanIntradayRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=32, pattern=r"^[A-Z0-9&_-]+$")
    interval: Literal[1, 5, 15, 25, 60]
    from_date: date
    to_date: date


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
    dhan_pending = {"until": 0.0, "active": False}
    dhan_session = {"access_token": "", "expires_at": ""}

    @asynccontextmanager
    async def lifespan(app):
        async def expire_idle():
            while True:
                await asyncio.sleep(60)
                if lock.acquire(blocking=False):
                    try:
                        # 2 Hours (7200s) idle timeout and 8 Hours total session limit
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
        if request.url.path.startswith(("/v1/", "/dhan/")):
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

    def dhan_credentials():
        vals = tuple(os.environ.get(n, "").strip() for n in
                     ("DHAN_CLIENT_ID", "DHAN_API_KEY", "DHAN_API_SECRET"))
        if not all(vals):
            raise HTTPException(503, "Dhan credentials not configured")
        return vals

    @app.post("/dhan/start")
    def dhan_start(x_botking_key: Optional[str] = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        client, key, secret = dhan_credentials()
        with lock:
            if dhan_pending["active"] and clock() < dhan_pending["until"]:
                raise HTTPException(409, "Dhan login already pending")
            dhan_pending.update(active=False, until=0.0)
            try:
                response = requests.post(
                    "https://auth.dhan.co/app/generate-consent",
                    params={"client_id": client},
                    headers={"app_id": key, "app_secret": secret},
                    timeout=12,
                )
                response.raise_for_status()
                consent = response.json().get("consentAppId")
                if not isinstance(consent, str) or not consent or len(consent) > 200:
                    raise ValueError("Missing consent ID")
            except (requests.RequestException, ValueError):
                raise HTTPException(502, "Dhan consent request failed") from None
            dhan_pending.update(active=True, until=clock() + 300)
        return {"login_url": "https://auth.dhan.co/login/consentApp-login?consentAppId=" + quote(consent, safe=""),
                "expires_in": 300, "live_orders_enabled": False}

    @app.get("/dhan/callback", response_class=HTMLResponse)
    def dhan_callback(tokenId: Optional[str] = None):
        headers = {"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
        with lock:
            if not dhan_pending["active"] or clock() >= dhan_pending["until"]:
                raise HTTPException(403, "No pending Dhan login")
            dhan_pending.update(active=False, until=0.0)
            if not tokenId or len(tokenId) > 2048:
                raise HTTPException(400, "Invalid Dhan callback")
            client, key, secret = dhan_credentials()
            try:
                response = requests.get(
                    "https://auth.dhan.co/app/consumeApp-consent",
                    params={"tokenId": tokenId},
                    headers={"app_id": key, "app_secret": secret},
                    timeout=12,
                )
                response.raise_for_status()
                result = response.json()
                token = result.get("accessToken")
                if (not isinstance(token, str) or not token
                        or str(result.get("dhanClientId")) != client):
                    raise ValueError("Invalid Dhan account or token")
            except (requests.RequestException, ValueError):
                raise HTTPException(502, "Dhan authentication failed") from None
            dhan_session.update(access_token=token, expires_at=str(result.get("expiryTime", "")))
        return HTMLResponse(
            "<!doctype html><html><head><meta name='referrer' content='no-referrer'></head>"
            "<body><h2>BOT KING: Dhan login successful</h2>"
            "<p>You may close this page. Trading remains disabled.</p></body></html>",
            headers=headers,
        )

    @app.get("/dhan/status")
    def dhan_status(x_botking_key: Optional[str] = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        # A manually provisioned read-only token may be usable even when the
        # interactive Dhan consent flow has not populated dhan_session.
        # Never expose token contents, paths or account credentials.
        try:
            token_configured = bool(Path("/etc/bot-king/dhan-token").read_text(encoding="utf-8").strip())
        except OSError:
            token_configured = False
        market_data_configured = bool(os.environ.get("DHAN_CLIENT_ID", "").strip()) and token_configured
        with lock:
            return {"authenticated": bool(dhan_session["access_token"]),
                    "market_data_configured": market_data_configured,
                    "login_pending": bool(dhan_pending["active"] and clock() < dhan_pending["until"]),
                    "expires_at": dhan_session["expires_at"],
                    "live_orders_enabled": False}

    @app.post("/dhan/ltp")
    def dhan_ltp(body: Symbol, x_botking_key: Optional[str] = Header(default=None)):
        """Read-only paired quotes for Dhan instrument-master-verified IDs."""
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        mapping = DHAN_VERIFIED_INSTRUMENTS
        if body.symbol not in mapping:
            raise HTTPException(422, "Dhan instrument mapping not verified")
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        try:
            token = Path("/etc/bot-king/dhan-token").read_text(encoding="utf-8").strip()
        except OSError:
            raise HTTPException(503, "Dhan token file unavailable") from None
        if not client or not token:
            raise HTTPException(503, "Dhan credentials not configured")
        segment, sid, _instrument = mapping[body.symbol]
        try:
            data = DhanFeed(client, token).ltp(segment, sid)
            price = data["data"][segment][str(sid)]["last_price"]
            if data.get("status") != "success" or isinstance(price, bool):
                raise ValueError("Invalid quote")
            price = float(price)
            if not math.isfinite(price) or price <= 0:
                raise ValueError("Invalid price")
        except DhanFeedError:
            raise HTTPException(502, "Dhan market data unavailable or token expired") from None
        except (ValueError, TypeError, KeyError, OverflowError, AttributeError):
            raise HTTPException(502, "Invalid Dhan quote response") from None
        return {"symbol": body.symbol, "source": "dhan", "exchange_segment": segment,
                "security_id": str(sid), "ltp": price, "freshness": "unverified",
                "live_orders_enabled": False}

    @app.post("/dhan/ltp-batch")
    def dhan_ltp_batch(x_botking_key: Optional[str] = Header(default=None)):
        """One read-only Dhan request for the verified equity watchlist."""
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        try:
            token = Path("/etc/bot-king/dhan-token").read_text(encoding="utf-8").strip()
        except OSError:
            raise HTTPException(503, "Dhan token file unavailable") from None
        if not client or not token:
            raise HTTPException(503, "Dhan credentials not configured")
        ids = [sid for segment, sid, _ in DHAN_VERIFIED_INSTRUMENTS.values() if segment == "NSE_EQ"]
        try:
            data = DhanFeed(client, token)._post("/marketfeed/ltp", {"NSE_EQ": ids})
        except DhanFeedError:
            raise HTTPException(502, "Dhan batch market data unavailable") from None
        entries = data.get("data", {}).get("NSE_EQ", {})
        if data.get("status") != "success" or not isinstance(entries, dict):
            raise HTTPException(502, "Invalid Dhan batch quote response")
        quotes = {}
        unavailable = []
        for symbol, (segment, sid, _) in DHAN_VERIFIED_INSTRUMENTS.items():
            if segment != "NSE_EQ":
                continue
            try:
                raw = entries[str(sid)]["last_price"]
                if isinstance(raw, bool):
                    raise ValueError("Boolean price")
                price = float(raw)
                if not math.isfinite(price) or price <= 0:
                    raise ValueError("Invalid price")
                quotes[symbol] = price
            except (KeyError, TypeError, ValueError, OverflowError, AttributeError):
                unavailable.append(symbol)
        return {"source": "dhan", "quotes": quotes, "unavailable": unavailable,
                "freshness": "unverified", "live_orders_enabled": False}

    @app.post("/dhan/intraday")
    def dhan_intraday(body: DhanIntradayRequest, x_botking_key: Optional[str] = Header(default=None)):
        """Read-only historical candles; reject unverifiable and malformed responses."""
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        if body.to_date < body.from_date or (body.to_date - body.from_date).days > 5:
            raise HTTPException(422, "Invalid Dhan date range")
        india_today = datetime.now(timezone(timedelta(hours=5, minutes=30))).date()
        if body.to_date > india_today:
            raise HTTPException(422, "Future candles are unavailable")
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        try:
            token = Path("/etc/bot-king/dhan-token").read_text(encoding="utf-8").strip()
        except OSError:
            raise HTTPException(503, "Dhan token file unavailable") from None
        if not client or not token:
            raise HTTPException(503, "Dhan credentials not configured")
        if body.symbol not in DHAN_VERIFIED_INSTRUMENTS:
            raise HTTPException(422, "Dhan instrument mapping not verified")
        segment, sid, instrument = DHAN_VERIFIED_INSTRUMENTS[body.symbol]
        payload = {
            "securityId": str(sid), "exchangeSegment": segment, "instrument": instrument,
            "interval": str(body.interval),
            "fromDate": body.from_date.isoformat() + " 09:15:00",
            "toDate": body.to_date.isoformat() + " 15:30:00",
        }
        try:
            result = DhanFeed(client, token).intraday(payload)
            keys = ("open", "high", "low", "close", "volume", "timestamp")
            if result.get("status") == "failure":
                raise ValueError("Provider failure")
            arrays = [result[k] for k in keys]
            if not all(isinstance(a, list) for a in arrays):
                raise ValueError("Malformed candles")
            n = len(arrays[0])
            if not n or n > 5000 or any(len(a) != n for a in arrays):
                raise ValueError("Malformed candle lengths")
            bars = []
            for row in zip(*arrays):
                o, h, l, close, vol, ts = row
                if any(isinstance(v, bool) for v in row):
                    raise ValueError("Invalid candle values")
                o, h, l, close, vol, ts = map(float, row)
                if (not all(math.isfinite(v) for v in (o, h, l, close, vol, ts))
                        or min(o, h, l, close) <= 0 or vol < 0
                        or h < max(o, close, l) or l > min(o, close, h)
                        or ts <= 0):
                    raise ValueError("Invalid OHLC data")
                bars.append([int(ts), o, h, l, close, vol])
            if any(bars[i][0] >= bars[i + 1][0] for i in range(len(bars) - 1)):
                raise ValueError("Candles out of order")
        except DhanFeedError:
            raise HTTPException(502, "Dhan historical data unavailable or token expired") from None
        except (KeyError, ValueError, TypeError, OverflowError, AttributeError):
            raise HTTPException(502, "Invalid Dhan historical response") from None
        return {"symbol": body.symbol, "source": "dhan", "interval": str(body.interval) + "m",
                "bars": bars, "freshness": "historical_unverified",
                "live_orders_enabled": False}

    @app.get("/health")
    def health():
        return {
            "status": "ok",
            "service": "BOT KING",
            "protocol": 1,
            "broker_connected": bool(state["token"] and feed.connected
                                     and clock() - state["issued"] < 8 * 3600
                                     and clock() - state["last"] < 7200),
            "live_orders_enabled": False
        }

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

    @app.post("/v1/ping")
    def ping(authorization: Optional[str] = Header(default=None)):
        with lock:
            authorized(authorization)
        return {"status": "alive", "session_active": True}

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
