"""Single-file monolithic BOT KING gateway v2.3.0
- Extended 2-Hour Idle Session Timeout
- Dedicated Heartbeat / Ping Support
- Hardened Single-Owner Security
"""
import asyncio
import hmac
import json
import logging
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
from zoneinfo import ZoneInfo
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
    from .dhan_feed import DhanFeed, DhanFeedError, DhanRateLimitError
except ImportError:  # Direct execution on the Oracle backend directory
    from dhan_feed import DhanFeed, DhanFeedError, DhanRateLimitError
from pathlib import Path

_dhan_auth_logger = logging.getLogger("botking.dhan.auth")


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
    dhan_session_file = os.environ.get("DHAN_SESSION_FILE", "").strip()

    def valid_dhan_expiry(expiry):
        try:
            expires = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
            if expires.tzinfo is None:
                expires = expires.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
            return datetime.now(timezone.utc) < expires.astimezone(timezone.utc)
        except (AttributeError, TypeError, ValueError, OverflowError):
            return False

    def persist_dhan_session():
        """Optional owner-only storage; fail closed if durable storage fails."""
        if not dhan_session_file:
            return
        target = Path(dhan_session_file)
        if not target.is_absolute():
            raise OSError("DHAN_SESSION_FILE must be absolute")
        payload = json.dumps(dhan_session).encode("utf-8")
        temporary = target.with_name(target.name + ".tmp-" + secrets.token_hex(8))
        try:
            fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, target)
        finally:
            temporary.unlink(missing_ok=True)

    if dhan_session_file:
        try:
            session_path = Path(dhan_session_file)
            if not session_path.is_absolute():
                raise OSError("DHAN_SESSION_FILE must be absolute")
            stat = session_path.stat()
            if stat.st_mode & 0o077 or stat.st_uid != os.geteuid():
                raise OSError("Dhan session file has unsafe permissions or owner")
            restored = json.loads(session_path.read_text(encoding="utf-8"))
            if (isinstance(restored, dict) and isinstance(restored.get("access_token"), str)
                    and restored["access_token"] and valid_dhan_expiry(restored.get("expires_at"))):
                dhan_session.update(access_token=restored["access_token"],
                                    expires_at=restored["expires_at"])
        except (OSError, ValueError, TypeError):
            pass


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
        # Opt-in 226 ingestion. Disabled until deployed and verified on Oracle.
        ingest_enabled = os.environ.get("BOTKING_226_INGEST_ENABLED", "0") == "1"
        try:
            ingest_interval = max(60, min(900, int(os.environ.get("BOTKING_226_INGEST_SECONDS", "90"))))
        except ValueError:
            ingest_interval = 90

        async def ingest_quotes():
            # One server-side batch request per interval; clients only read cache.
            await asyncio.sleep(5)
            while True:
                try:
                    await asyncio.to_thread(dhan_ltp_batch, pairing_key)
                except HTTPException as exc:
                    with snapshot_lock:
                        snapshot_cache["error"] = f"upstream_http_{exc.status_code}"
                    # Honor rate-limit cooldown rather than multiplying requests.
                    if exc.status_code == 429:
                        await asyncio.sleep(max(ingest_interval, 120))
                        continue
                except Exception:
                    logging.getLogger("botking.226.ingest").exception("Dhan snapshot ingest failed")
                    with snapshot_lock:
                        snapshot_cache["error"] = "ingest_unavailable"
                await asyncio.sleep(ingest_interval)

        ingest_task = asyncio.create_task(ingest_quotes()) if ingest_enabled else None
        try:
            yield
        finally:
            task.cancel()
            if ingest_task is not None:
                ingest_task.cancel()
            with suppress(asyncio.CancelledError):
                await task
            if ingest_task is not None:
                with suppress(asyncio.CancelledError):
                    await ingest_task
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
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else "unknown"
                _dhan_auth_logger.warning("Dhan token exchange rejected: HTTP status=%s; verify OAuth app key/secret pairing, callback registration, and single-use consent token (response body suppressed)", status)
                raise HTTPException(502, "Dhan authentication failed") from None
            except requests.Timeout:
                _dhan_auth_logger.warning("Dhan token exchange timed out")
                raise HTTPException(502, "Dhan authentication failed") from None
            except requests.ConnectionError:
                _dhan_auth_logger.warning("Dhan token exchange connection failed")
                raise HTTPException(502, "Dhan authentication failed") from None
            except requests.RequestException:
                _dhan_auth_logger.warning("Dhan token exchange request failed")
                raise HTTPException(502, "Dhan authentication failed") from None
            except (ValueError, TypeError, AttributeError):
                _dhan_auth_logger.warning("Dhan token exchange returned invalid JSON, token, or client ID")
                raise HTTPException(502, "Dhan authentication failed") from None
            expiry = str(result.get("expiryTime", ""))
            try:
                expiry_dt = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                if expiry_dt.tzinfo is None:
                    expiry_dt = expiry_dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                if datetime.now(timezone.utc) >= expiry_dt.astimezone(timezone.utc):
                    raise ValueError("Expired token")
            except (TypeError, ValueError, OverflowError):
                raise HTTPException(502, "Dhan returned invalid token expiry") from None
            previous = dhan_session.copy()
            dhan_session.update(access_token=token, expires_at=expiry)
            try:
                persist_dhan_session()
            except OSError:
                dhan_session.update(previous)
                raise HTTPException(503, "Secure Dhan session storage unavailable") from None
        return HTMLResponse(
            "<!doctype html><html><head><meta name='referrer' content='no-referrer'></head>"
            "<body><h2>BOT KING: Dhan login successful</h2>"
            "<p>You may close this page. Trading remains disabled.</p></body></html>",
            headers=headers,
        )

    def dhan_market_token():
        """Use a non-expired consent token, otherwise a provisioned read-only token."""
        with lock:
            active = dhan_session["access_token"]
            expiry = dhan_session["expires_at"]
            if active and expiry:
                try:
                    expires = datetime.fromisoformat(expiry.replace("Z", "+00:00"))
                    if expires.tzinfo is None:
                        # Dhan documents OAuth expiryTime as an IST timestamp.
                        expires = expires.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                    if datetime.now(timezone.utc) >= expires.astimezone(timezone.utc):
                        active = ""
                except (TypeError, ValueError, OverflowError):
                    active = ""
            elif active:
                # An unparseable/missing expiry cannot prove a token is still valid.
                active = ""
            if not active and dhan_session["access_token"]:
                dhan_session.update(access_token="", expires_at="")
        if active:
            return active
        try:
            return Path("/etc/bot-king/dhan-token").read_text(encoding="utf-8").strip()
        except OSError:
            return ""

    @app.get("/dhan/status")
    def dhan_status(x_botking_key: Optional[str] = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        # A manually provisioned read-only token may be usable even when the
        # interactive Dhan consent flow has not populated dhan_session.
        # Never expose token contents, paths or account credentials.
        token_configured = bool(dhan_market_token())
        market_data_configured = bool(os.environ.get("DHAN_CLIENT_ID", "").strip()) and token_configured
        with lock:
            # dhan_market_token() has already cleared an expired OAuth session.
            # A legacy token file is only configured, not authenticated.
            authenticated = bool(dhan_session["access_token"]) and valid_dhan_expiry(dhan_session["expires_at"])
            expiry_minutes = None
            if authenticated:
                parsed_expiry = datetime.fromisoformat(dhan_session["expires_at"].replace("Z", "+00:00"))
                if parsed_expiry.tzinfo is None:
                    parsed_expiry = parsed_expiry.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                expiry_minutes = max(0, int((parsed_expiry.astimezone(timezone.utc) - datetime.now(timezone.utc)).total_seconds() / 60))
            return {"authenticated": authenticated,
                    "oauth_minutes_remaining": expiry_minutes,
                    "oauth_expiry_warning": authenticated and expiry_minutes <= 120,
                    "market_data_configured": market_data_configured,
                    "login_pending": bool(dhan_pending["active"] and clock() < dhan_pending["until"]),
                    "expires_at": dhan_session["expires_at"] if authenticated else "",
                    "token_source": "oauth_consent" if authenticated else ("provisioned_unverified" if token_configured else "none"),
                    "renewal_supported": False,
                    "reauthentication_required": not authenticated,
                    "token_validity": "expiry_checked" if authenticated else ("unverified" if token_configured else "missing"),
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
        token = dhan_market_token()
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
        except DhanRateLimitError:
            raise HTTPException(429, "Dhan market data rate limited; retry later", headers={"Retry-After": "30"}) from None
        except DhanFeedError:
            raise HTTPException(502, "Dhan market data unavailable or token expired") from None
        except (ValueError, TypeError, KeyError, OverflowError, AttributeError):
            raise HTTPException(502, "Invalid Dhan quote response") from None
        return {"symbol": body.symbol, "source": "dhan", "exchange_segment": segment,
                "security_id": str(sid), "ltp": price, "freshness": "unverified",
                "live_orders_enabled": False}

    # BOT KING 226: server-owned bounded snapshot cache, no Dhan calls per mobile read.
    # Cache is process-local until the persistent ingest worker is deployed.
    snapshot_lock = threading.RLock()
    snapshot_cache = {"quotes": {}, "unavailable": [], "observed_at": "", "updated_monotonic": 0.0, "error": "not_collected"}
    snapshot_refresh_lock = threading.Lock()

    @app.get("/v2/snapshot")
    def botking_snapshot(x_botking_key: Optional[str] = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        with snapshot_lock:
            age = max(0.0, clock() - snapshot_cache["updated_monotonic"]) if snapshot_cache["updated_monotonic"] else None
            return {"protocol": 2, "source": "dhan", "quotes": dict(snapshot_cache["quotes"]),
                    "unavailable": list(snapshot_cache["unavailable"]), "observed_at": snapshot_cache["observed_at"],
                    "age_seconds": round(age, 1) if age is not None else None,
                    "freshness": "unverified" if age is not None and age <= 30 else "stale_or_missing",
                    "error": snapshot_cache["error"], "live_orders_enabled": False}

    @app.post("/dhan/ltp-batch")
    def dhan_ltp_batch(x_botking_key: Optional[str] = Header(default=None)):
        """One read-only Dhan request for the verified equity watchlist."""
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        token = dhan_market_token()
        if not client or not token:
            raise HTTPException(503, "Dhan credentials not configured")
        ids = [sid for segment, sid, _ in DHAN_VERIFIED_INSTRUMENTS.values() if segment == "NSE_EQ"]
        try:
            data = DhanFeed(client, token)._post("/marketfeed/ltp", {"NSE_EQ": ids})
        except DhanRateLimitError:
            raise HTTPException(429, "Dhan market data rate limited; retry later", headers={"Retry-After": "30"}) from None
        except DhanFeedError as exc:
            # Classify safe adapter errors without exposing upstream bodies or tokens.
            reason = str(exc).lower()
            if "credentials are not configured" in reason:
                raise HTTPException(503, "Dhan credentials not configured") from None
            if "token expired or data access not entitled" in reason:
                raise HTTPException(502, "Dhan token expired or market data not entitled") from None
            if "rejected market data request" in reason:
                raise HTTPException(502, "Dhan rejected batch quote request; check entitlement and instruments") from None
            if "response exceeds size limit" in reason or "invalid dhan response" in reason:
                raise HTTPException(502, "Dhan batch response malformed or too large") from None
            if "market data request failed" in reason:
                raise HTTPException(502, "Dhan batch network request failed") from None
            raise HTTPException(502, "Dhan batch market data unavailable") from None
        entries = data.get("data", {}).get("NSE_EQ", {})
        if data.get("status") != "success" or not isinstance(entries, dict):
            raise HTTPException(502, "Invalid Dhan batch quote response")
        if not entries:
            raise HTTPException(502, "Dhan returned no market data for verified NSE equities")
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
        with snapshot_lock:
            snapshot_cache.update(quotes=dict(quotes), unavailable=list(unavailable),
                                  observed_at=datetime.now(timezone.utc).isoformat(),
                                  updated_monotonic=clock(), error=None)
        return {"source": "dhan", "quotes": quotes, "unavailable": unavailable,
                "freshness": "unverified", "live_orders_enabled": False}

    # Historical candles are cached only after provider validation succeeds.
    candle_cache = {}
    candle_lock = threading.RLock()
    candle_cache_max_entries = 100
    candle_cache_file = os.environ.get("BOTKING_CANDLE_CACHE_FILE", "").strip()

    # Persistence is opt-in; never trust or serve unvalidated disk contents.
    if candle_cache_file:
        try:
            disk_path = Path(candle_cache_file)
            if not disk_path.is_absolute() or disk_path.is_symlink():
                raise ValueError("Cache path must be an absolute regular path")
            if disk_path.is_file() and disk_path.stat().st_size <= 5_000_000:
                stored = json.loads(disk_path.read_text(encoding="utf-8"))
                if isinstance(stored, dict) and stored.get("version") == 1:
                    for item in stored.get("entries", [])[:candle_cache_max_entries]:
                        if not isinstance(item, dict):
                            continue
                        symbol, interval = item.get("symbol"), item.get("interval")
                        bars = item.get("bars")
                        if (symbol not in DHAN_VERIFIED_INSTRUMENTS or
                                interval not in ("1", "5", "15", "25", "60") or
                                not isinstance(bars, list) or not 0 < len(bars) <= 5000):
                            continue
                        try:
                            dates = (date.fromisoformat(item["from_date"]),
                                     date.fromisoformat(item["to_date"]))
                            observed = datetime.fromisoformat(item["observed_at"])
                            if dates[1] < dates[0] or observed.tzinfo is None:
                                continue
                            previous = 0
                            for bar in bars:
                                if not isinstance(bar, list) or len(bar) != 6:
                                    raise ValueError("Invalid candle")
                                ts, o, h, low, close, vol = bar
                                if (any(isinstance(v, bool) or not isinstance(v, (int, float))
                                        or not math.isfinite(v) for v in bar)
                                        or ts <= previous or min(o, h, low, close) <= 0
                                        or vol < 0 or h < max(o, low, close)
                                        or low > min(o, h, close)):
                                    raise ValueError("Invalid candle")
                                previous = ts
                        except (ValueError, TypeError, KeyError, OverflowError):
                            continue
                        candle_cache[(symbol, interval)] = {
                            "bars": [list(bar) for bar in bars],
                            "from_date": item["from_date"], "to_date": item["to_date"],
                            "observed_at": item["observed_at"]}
        except (OSError, ValueError, TypeError, UnicodeError):
            logging.getLogger(__name__).warning("Candle cache recovery unavailable")

    def persist_candle_cache():
        if not candle_cache_file:
            return
        target = Path(candle_cache_file)
        if not target.is_absolute() or target.is_symlink():
            return
        entries = [dict(symbol=symbol, interval=interval, **entry)
                   for (symbol, interval), entry in candle_cache.items()]
        payload = json.dumps({"version": 1, "entries": entries}, separators=(",", ":")).encode()
        if len(payload) > 5_000_000:
            return
        temporary = target.with_name(target.name + ".tmp-" + secrets.token_hex(8))
        try:
            fd = os.open(str(temporary), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "wb") as output:
                output.write(payload)
                output.flush()
                os.fsync(output.fileno())
            os.replace(str(temporary), str(target))
        except OSError:
            logging.getLogger(__name__).warning("Candle cache persistence unavailable")
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


    @app.get("/v2/candles/{symbol}/{interval}")
    def cached_candles(symbol: str, interval: str, x_botking_key: Optional[str] = Header(default=None)):
        if not x_botking_key or not hmac.compare_digest(x_botking_key.encode(), pairing_key.encode()):
            raise HTTPException(403, "Server access denied")
        if symbol not in DHAN_VERIFIED_INSTRUMENTS or interval not in ("1", "5", "15", "25", "60"):
            raise HTTPException(422, "Unsupported candle instrument or interval")
        with candle_lock:
            entry = candle_cache.get((symbol, interval))
            if entry is None:
                return {"symbol": symbol, "interval": interval + "m", "bars": [],
                        "source": "dhan", "freshness": "stale_or_missing",
                        "observed_at": None, "from_date": None, "to_date": None,
                        "live_orders_enabled": False}
            return {"symbol": symbol, "interval": interval + "m",
                    "bars": [list(bar) for bar in entry["bars"]], "source": "dhan",
                    "freshness": "historical_unverified", "observed_at": entry["observed_at"],
                    "from_date": entry["from_date"], "to_date": entry["to_date"],
                    "live_orders_enabled": False}

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
        token = dhan_market_token()
        if not client or not token:
            raise HTTPException(503, "Dhan credentials not configured")
        if body.symbol not in DHAN_VERIFIED_INSTRUMENTS:
            raise HTTPException(422, "Dhan instrument mapping not verified")
        segment, sid, instrument = DHAN_VERIFIED_INSTRUMENTS[body.symbol]
        payload = {
            "securityId": str(sid), "exchangeSegment": segment, "instrument": instrument,
            "interval": str(body.interval),
            "fromDate": body.from_date.isoformat() + " 09:15:00",
            "toDate": (body.to_date + timedelta(days=1)).isoformat() + " 00:00:00",
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
            if n == 0 and all(len(a) == 0 for a in arrays):
                return {"symbol": body.symbol, "source": "dhan",
                        "interval": str(body.interval) + "m", "bars": [],
                        "freshness": "no_candles_available",
                        "live_orders_enabled": False}
            if n > 5000 or any(len(a) != n for a in arrays):
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
        except DhanRateLimitError:
            raise HTTPException(429, "Dhan historical data rate limited; retry later",
                                headers={"Retry-After": "30"}) from None
        except DhanFeedError:
            raise HTTPException(502, "Dhan historical data unavailable or token expired") from None
        except (KeyError, ValueError, TypeError, OverflowError, AttributeError):
            raise HTTPException(502, "Invalid Dhan historical response") from None
        if bars:
            with candle_lock:
                key = (body.symbol, str(body.interval))
                # The cache holds the latest validated request window, not a merged history.
                candle_cache.pop(key, None)
                candle_cache[key] = {
                    "bars": [list(bar) for bar in bars],
                    "from_date": body.from_date.isoformat(),
                    "to_date": body.to_date.isoformat(),
                    "observed_at": datetime.now(timezone.utc).isoformat(),
                }
                while len(candle_cache) > candle_cache_max_entries:
                    candle_cache.pop(next(iter(candle_cache)))
                persist_candle_cache()
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
