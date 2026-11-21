"""Separate B2 clone-only Oracle login gateway, SSK authenticated and read-only.

Never reuse/deploy the old V2 pilot or modify the running V1 service.
Owner operates this on 127.0.0.1:8002 behind a reviewed HTTPS proxy. No
market quote/candle endpoints or broker trading orders are added here.
"""
from __future__ import annotations

import hmac
import secrets
import tempfile
import urllib.parse
import urllib.request
import urllib.error
import json
import logging
import math
import re
import threading
import time
from datetime import date, datetime, timedelta, timezone
import os
import stat
from pathlib import Path
from typing import Optional
from pydantic import BaseModel
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse

KEY_ENV = "BOTKING_CLONE_V2_SSK_FILE"
PROTOCOL = "botking-clone-v2"
DIAGNOSTIC_LOGGER = logging.getLogger("botking.clone.market")


def private_ssk(path):
    """Load an operator-protected key without exposing bytes in logs."""
    if (type(path) is not str or not path.startswith("/home/opc/")
            or not Path(path).is_absolute() or ".." in Path(path).parts):
        raise ValueError("Clone V2 private SSK path required")
    p = Path(path)
    if (p.is_symlink() or not p.is_file() or p.parent.is_symlink()
            or stat.S_IMODE(p.parent.stat().st_mode) & 0o077
            or stat.S_IMODE(p.stat().st_mode) & 0o077
            or p.stat().st_size < 32 or p.stat().st_size > 1024):
        raise ValueError("Clone V2 private SSK missing or unprotected")
    key = p.read_bytes().strip()
    if len(key) < 32 or len(key) > 512 or any(c < 33 or c > 126 for c in key):
        raise ValueError("Clone V2 SSK format invalid")
    return key




class MarketCandles(BaseModel):
    symbol: str
    interval: int
    from_date: date
    to_date: date


class MarketUnderlying(BaseModel):
    symbol: str


class MarketOptionChain(BaseModel):
    symbol: str
    expiry: date


class MarketRequest(BaseModel):
    symbols: list


def load_equity_registry(path):
    """Validate independently; never trust app-supplied security IDs."""
    try:
        target = Path(path)
        if target.is_symlink() or target.stat().st_size > 4_000_000:
            return {}
        obj = json.loads(target.read_text(encoding="utf-8"))
        entries = obj["equities"]
        if (obj.get("schema_version") != 1 or obj.get("source") != "dhan_instrument_master"
                or not isinstance(entries, dict) or not 300 <= len(entries) <= 10000
                or obj.get("equity_count") != len(entries)):
            return {}
        out, used = {}, set()
        for symbol, row in entries.items():
            sid = row.get("security_id") if isinstance(row, dict) else None
            if (not isinstance(symbol, str) or not re.fullmatch(r"[A-Z0-9&_-]{1,32}", symbol)
                    or row.get("segment") != "NSE_EQ" or row.get("instrument") != "EQUITY"
                    or type(sid) is not int or sid <= 0 or sid in used):
                return {}
            used.add(sid)
            out[symbol] = ("NSE_EQ", sid)
        return out
    except (OSError, ValueError, TypeError, KeyError, UnicodeError):
        return {}


def create_app(*, key_bytes=None, market_feed_factory=None, market_registry=None,
               consent_config_factory=None):
    """Fail closed at startup if owner has not provisioned a protected key."""
    if key_bytes is None:
        key_bytes = private_ssk(os.environ.get(KEY_ENV))
    if (type(key_bytes) is not bytes or not 32 <= len(key_bytes) <= 512
            or any(c < 33 or c > 126 for c in key_bytes)):
        raise ValueError("Approved Clone V2 SSK required")
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)


    indices = {"NIFTY": ("IDX_I", 13), "BANKNIFTY": ("IDX_I", 25),
               "SENSEX": ("BSE_I", 51)}
    registry = (market_registry if market_registry is not None else
                load_equity_registry(os.environ.get("BOTKING_CLONE_DHAN_REGISTRY",
                "/opt/bot-king-backups/registry-audit/dhan_equity_registry.json")))
    known = dict(registry)
    known.update(indices)
    # FINNIFTY is an options underlying (Dhan IDX_I/27), not a fourth
    # dashboard index. Keep it out of the three-index quote/candle lanes.
    option_known = dict(known)
    option_known["FINNIFTY"] = ("IDX_I", 27)
    market_lock = threading.Lock()
    market_cache = {}
    last_request = [0.0]
    provider_cooldown_until = [0.0]
    # Clone-owned candle single-flight and validated, date-scoped history cache.
    # Kept independent of V1 server and files; only successful nonempty bars.
    candle_cache = {}
    candle_cache_lock = threading.RLock()
    candle_miss_locks = tuple(threading.RLock() for _ in range(32))
    candle_cache_ttl_seconds = 180
    candle_cache_max_entries = 100

    def market_diagnostic(route, symbol, stage, category):
        """Fixed-enum, index-only observations: never emit untrusted content."""
        if (route not in ("quotes", "candles", "option_expiries", "option_chain")
                or symbol not in ("NIFTY", "BANKNIFTY", "SENSEX", "FINNIFTY")
                or stage not in ("provider", "shape", "mapping", "validation", "cooldown")
                or category not in ("missing_segment", "missing_security_id",
                                    "invalid_price", "invalid_shape", "invalid_bars",
                                    "rate_limited", "auth_unavailable", "upstream_error")):
            return
        DIAGNOSTIC_LOGGER.warning(
            "clone_market_diagnostic route=%s symbol=%s stage=%s category=%s",
            route, symbol, stage, category)

    # Clone-owned, optional browser-consent flow; NEVER borrow V1's HTTP auth.
    # Server must have a separately approved Dhan callback pointing here.
    consent_lock = threading.RLock()
    consent_pending = {"until": 0.0, "active": False}
    consent_cooldown_until = [0.0]

    def clone_oauth_config():
        if consent_config_factory is not None:
            return consent_config_factory()
        # Owner has retired V1 as a target app. Reuse its registered Dhan OAuth
        # redirect under an EXPLICIT Clone-only cutover setting. Changing the
        # broker developer-app callback or generating another app is unnecessary.
        if os.environ.get("BOTKING_CLONE_DHAN_CALLBACK_APPROVED") != "1":
            raise HTTPException(503, "Clone Dhan callback handoff not approved")
        callback = os.environ.get("BOTKING_CLONE_DHAN_CALLBACK_URL", "")
        expected = "https://botkingrajesh.duckdns.org/dhan/callback"
        if callback != expected:
            raise HTTPException(503, "Registered V1 callback handoff not configured")
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        app_id = os.environ.get("BOTKING_CLONE_DHAN_APP_ID", "").strip()
        secret = os.environ.get("BOTKING_CLONE_DHAN_APP_SECRET", "").strip()
        location = os.environ.get("BOTKING_CLONE_DHAN_TOKEN_FILE", "")
        if (not client or not app_id or not secret or
                not location.startswith("/home/opc/")):
            raise HTTPException(503, "Clone Dhan browser authorization not configured")
        return client, app_id, secret, Path(location)

    def clone_token_path(target):
        if (target.is_symlink() or not target.is_file() or
                stat.S_IMODE(target.stat().st_mode) & 0o077 or
                target.stat().st_uid != os.geteuid()):
            raise HTTPException(503, "Clone token storage is not secure")

    class NoBrokerRedirect(urllib.request.HTTPRedirectHandler):
        # Never forward any broker app secret or access token through a redirect.
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None

    def broker_json(request):
        try:
            with urllib.request.build_opener(
                urllib.request.ProxyHandler({}),
                urllib.request.HTTPSHandler(),
                NoBrokerRedirect()
            ).open(request, timeout=15) as response:
                if response.status != 200:
                    raise ValueError("Bad broker response")
                payload = response.read(100001)
            if len(payload) > 100000:
                raise ValueError("Oversized broker response")
            data = json.loads(payload)
            if not isinstance(data, dict):
                raise ValueError("Invalid broker response")
            return data
        except (urllib.error.URLError, OSError, ValueError, UnicodeError):
            raise HTTPException(502, "Dhan browser authorization unavailable") from None

    @app.post("/clone-v2/dhan/start")
    def clone_dhan_start(x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        client, app_id, secret, target = clone_oauth_config()
        clone_token_path(target)
        with consent_lock:
            now = time.monotonic()
            if consent_pending["active"] and now < consent_pending["until"]:
                raise HTTPException(409, "Clone Dhan login already pending")
            if now < consent_cooldown_until[0]:
                raise HTTPException(429, "Clone consent request paced")
            consent_cooldown_until[0] = now + 8
            request = urllib.request.Request(
                "https://auth.dhan.co/app/generate-consent?"+
                urllib.parse.urlencode({"client_id": client}),
                headers={"app_id": app_id, "app_secret": secret,
                         "Accept": "application/json"},
                data=b"", method="POST")
            result = broker_json(request)
            consent = result.get("consentAppId")
            if not isinstance(consent, str) or not 1 <= len(consent) <= 200:
                raise HTTPException(502, "Dhan consent ID unavailable")
            consent_pending.update(active=True, until=time.monotonic()+300)
        login_url = ("https://auth.dhan.co/login/consentApp-login?"+
                     urllib.parse.urlencode({"consentAppId": consent}))
        return JSONResponse(
            {"login_url": login_url, "expires_in": 300,
             "live_orders_enabled": False}, headers={"Cache-Control": "no-store"})

    # Exact legacy Dhan redirect accepted by Clone only after HTTPS cutover.
    # Nginx exact-match /dhan/callback must route here, NOT V1 port 8000.
    @app.get("/dhan/callback", response_class=HTMLResponse)
    @app.get("/clone-v2/dhan/callback", response_class=HTMLResponse)
    def clone_dhan_callback(tokenId: Optional[str] = None):
        headers={"Cache-Control": "no-store", "Referrer-Policy": "no-referrer"}
        with consent_lock:
            now=time.monotonic()
            if not consent_pending["active"] or now >= consent_pending["until"]:
                raise HTTPException(403, "No active Clone Dhan authorization")
            # Single use, including failure: never replay tokenIds.
            consent_pending.update(active=False, until=0.0)
            if not isinstance(tokenId, str) or not 1 <= len(tokenId) <= 2048:
                raise HTTPException(400, "Invalid Dhan callback")
            client, app_id, secret, target = clone_oauth_config()
            clone_token_path(target)
            url=("https://auth.dhan.co/app/consumeApp-consent?"+
                 urllib.parse.urlencode({"tokenId": tokenId}))
            request=urllib.request.Request(url, headers={
                "app_id":app_id, "app_secret":secret, "Accept":"application/json"
            }, method="GET")
            result=broker_json(request)
            new_token=result.get("accessToken")
            expiry=result.get("expiryTime")
            if (not isinstance(new_token, str) or len(new_token) < 20
                    or str(result.get("dhanClientId")) != client):
                raise HTTPException(502, "Dhan authenticated account mismatch")
            try:
                from zoneinfo import ZoneInfo
                dt=datetime.fromisoformat(str(expiry).replace("Z","+00:00"))
                if dt.tzinfo is None:
                    dt=dt.replace(tzinfo=ZoneInfo("Asia/Kolkata"))
                if dt.astimezone(timezone.utc) <= datetime.now(timezone.utc):
                    raise ValueError()
            except (ValueError, TypeError, OverflowError):
                raise HTTPException(502, "Dhan token expiry not verified") from None
            # Dhan callback success alone is not verified market permission.
            # Validate the new token against the official profile before replacing.
            verified=broker_json(urllib.request.Request(
                "https://api.dhan.co/v2/profile",
                headers={"access-token":new_token, "Accept":"application/json"},
                method="GET"))
            if str(verified.get("dhanClientId")) != client:
                raise HTTPException(502,"New Dhan token profile/account unverified")
            if str(verified.get("dataPlan","")).lower() != "active":
                raise HTTPException(424,"Dhan market-data subscription not active")
            # Atomic clone-private write; V1 token and V1 OAuth are untouched.
            temp=None
            st=target.stat()
            try:
                fd,temp=tempfile.mkstemp(prefix=".clone-dhan-token-", dir=str(target.parent))
                os.fchmod(fd, 0o600)
                os.fchown(fd, st.st_uid, st.st_gid)
                with os.fdopen(fd,"w",encoding="utf-8") as out:
                    out.write(new_token+chr(10))
                    out.flush()
                    os.fsync(out.fileno())
                os.replace(temp,target)
                temp=None
                directory_fd=os.open(str(target.parent),os.O_RDONLY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
            except OSError:
                raise HTTPException(503,"Clone private Dhan session could not be saved") from None
            finally:
                if temp is not None:
                    Path(temp).unlink(missing_ok=True)
        return HTMLResponse(
            "<!doctype html><html><head><meta name='referrer' content='no-referrer'></head>"+
            "<body><h2>BOT KING Clone: Dhan login successful</h2>"+
            "<p>Return to BOT KING Clone and press Connect Clone V2 (SSK). "+
            "Trading orders remain disabled.</p></body></html>",
            headers=headers)


    def authorized(key):
        if (not isinstance(key, str) or len(key) > 1024
                or not hmac.compare_digest(key.encode("utf-8"), key_bytes)):
            raise HTTPException(403, "Clone V2 server access denied")

    def provider():
        if market_feed_factory is not None:
            return market_feed_factory()
        from dhan_feed import DhanFeed
        client = os.environ.get("DHAN_CLIENT_ID", "").strip()
        location = os.environ.get("BOTKING_CLONE_DHAN_TOKEN_FILE", "")
        if not client or not location.startswith("/home/opc/"):
            raise HTTPException(503, "Clone Dhan credentials unavailable")
        target = Path(location)
        if (target.is_symlink() or not target.is_file()
                or stat.S_IMODE(target.stat().st_mode) & 0o077):
            raise HTTPException(503, "Clone Dhan token file unavailable")
        token = target.read_text(encoding="utf-8").strip()
        if not token:
            raise HTTPException(503, "Clone Dhan token unavailable")
        return DhanFeed(client, token)

    @app.get("/clone-v2/status")
    def status(x_botking_key: Optional[str] = Header(default=None)):
        # Constant-time authorization, including unknown or malformed keys.
        if (not isinstance(x_botking_key, str)
                or len(x_botking_key) > 1024
                or not hmac.compare_digest(
                    x_botking_key.encode("utf-8"), key_bytes)):
            raise HTTPException(403, "Clone V2 server access denied")
        return JSONResponse(
            {"protocol": PROTOCOL, "authenticated": True, "read_only": True,
             "live_orders_enabled": False, "pipeline": "dhan-oracle-clone",
             "status": "ready"},
            headers={"Cache-Control": "no-store"})

    @app.get("/clone-v2/health")
    def health():
        # Health is not proof of authorization or live market data.
        return JSONResponse(
            {"status": "gateway_process_ready", "live_data_verified": False,
             "live_orders_enabled": False},
            headers={"Cache-Control": "no-store"})


    @app.post("/clone-v2/market/quotes")
    def market_quotes(body: MarketRequest,
                      x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        symbols = body.symbols
        if (not isinstance(symbols, list) or not 1 <= len(symbols) <= 73
                or len(symbols) != len(set(s for s in symbols if isinstance(s, str)))
                or any(not isinstance(s, str) or s not in known for s in symbols)
                or sum(s not in indices for s in symbols) > 70):
            raise HTTPException(422, "Invalid or duplicate clone selection")
        selection = tuple(sorted(symbols))
        with market_lock:
            now = time.monotonic()
            cache = market_cache.get(selection)
            # Only a COMPLETE three-index batch gets V1-parity 60s reuse.
            # Incomplete SENSEX/BANKNIFTY/NIFTY batches keep 20s recovery.
            full_index_batch = selection == tuple(sorted(indices))
            cache_ttl = (60 if full_index_batch and cache
                         and not cache[1].get("unavailable") else 20)
            if cache and 0 <= now - cache[0] < cache_ttl:
                return JSONResponse(cache[1], headers={"Cache-Control": "no-store"})
            if now < provider_cooldown_until[0]:
                for sym in symbols:
                    market_diagnostic("quotes", sym, "cooldown", "rate_limited")
                raise HTTPException(429, "Clone Dhan provider cooldown",
                                    headers={"Retry-After": "30"})
            if now - last_request[0] < 1.05:
                for sym in symbols:
                    market_diagnostic("quotes", sym, "cooldown", "rate_limited")
                raise HTTPException(429, "Clone quote lane paced",
                                    headers={"Retry-After": "2"})
            last_request[0] = now
            try:
                result = provider().batch_ltp([known[s] for s in symbols])
            except HTTPException:
                raise
            except Exception as exc:
                try:
                    from .dhan_feed import DhanRateLimitError, DhanFeedError
                except ImportError:
                    from dhan_feed import DhanRateLimitError, DhanFeedError
                if (isinstance(exc, DhanFeedError) and
                        "token expired or data access not entitled" in str(exc)):
                    category="auth_unavailable"
                elif isinstance(exc, DhanRateLimitError):
                    category="rate_limited"
                else:
                    category="upstream_error"
                for sym in symbols:
                    market_diagnostic("quotes", sym, "provider", category)
                if category=="auth_unavailable":
                    raise HTTPException(
                        424, "Dhan browser authorization or data permission required") from None
                if category=="rate_limited":
                    provider_cooldown_until[0] = time.monotonic() + 30
                    raise HTTPException(429, "Clone Dhan quota cooldown",
                                        headers={"Retry-After": "30"}) from None
                raise HTTPException(502, "Clone read-only Dhan quote unavailable") from None
            if not isinstance(result, dict) or result.get("status") != "success" or not isinstance(result.get("data"), dict):
                for sym in symbols:
                    market_diagnostic("quotes", sym, "shape", "invalid_shape")
                raise HTTPException(502, "Invalid clone Dhan quote response")
            quotes = {}
            for symbol in symbols:
                seg, sid = known[symbol]
                segment_data=result["data"].get(seg)
                if not isinstance(segment_data, dict):
                    market_diagnostic("quotes", symbol, "mapping", "missing_segment")
                elif not isinstance(segment_data.get(str(sid)), dict):
                    market_diagnostic("quotes", symbol, "mapping", "missing_security_id")
                try:
                    raw = result["data"][seg][str(sid)]["last_price"]
                    if type(raw) not in (int, float) or not math.isfinite(raw) or raw <= 0:
                        market_diagnostic("quotes", symbol, "validation", "invalid_price")
                        continue
                    quotes[symbol] = {"symbol": symbol, "ltp": float(raw),
                                      "source": "dhan", "freshness": "unverified"}
                except (KeyError, TypeError, ValueError, OverflowError):
                    if isinstance(segment_data, dict) and isinstance(segment_data.get(str(sid)), dict):
                        market_diagnostic("quotes", symbol, "validation", "invalid_price")
            if not quotes:
                raise HTTPException(502, "No validated clone quotes")
            payload = {"source": "dhan", "quotes": quotes,
                       "unavailable": [s for s in symbols if s not in quotes],
                       "freshness": "unverified", "live_orders_enabled": False}
            market_cache[selection] = (time.monotonic(), payload)
            # Share repeated selections across 1–4 phones, bounded by demand.
            if len(market_cache) > 16:
                market_cache.pop(min(market_cache, key=lambda k: market_cache[k][0]))
            return JSONResponse(payload, headers={"Cache-Control": "no-store"})


    @app.post("/clone-v2/market/verify")
    def market_verify(body: MarketUnderlying,
                      x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if body.symbol not in registry:
            raise HTTPException(422, "Clone equity mapping not verified")
        return JSONResponse({"symbol": body.symbol, "source": "dhan_registry",
                             "verified": True, "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    def provider_read_error(exc, unavailable_message):
        """Classify provider throttling without exposing credentials or responses."""
        try:
            from .dhan_feed import DhanRateLimitError, DhanFeedError
        except ImportError:
            from dhan_feed import DhanRateLimitError, DhanFeedError
        if isinstance(exc, DhanRateLimitError):
            raise HTTPException(
                429, "Clone Dhan provider cooldown",
                headers={"Retry-After": "30"}) from None
        if (isinstance(exc, DhanFeedError) and
                "token expired or data access not entitled" in str(exc)):
            raise HTTPException(
                424, "Dhan browser authorization or data permission required") from None
        raise HTTPException(502, unavailable_message) from None


    @app.post("/clone-v2/market/candles")
    def market_candles(body: MarketCandles,
                       x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if (body.symbol not in known or body.interval not in (1, 5, 15, 25, 60)
                or body.from_date > body.to_date
                or (body.to_date - body.from_date).days > 5
                or body.to_date > datetime.now(timezone(timedelta(hours=5, minutes=30))).date()):
            raise HTTPException(422, "Invalid Clone Dhan candle selection")
        cache_key = (body.symbol, body.interval, body.from_date, body.to_date)
        # A lock stripe coalesces concurrent same-request misses across 1–4 phones.
        # Recheck inside lock so only one provider fetch runs for a matching key.
        miss_lock = candle_miss_locks[hash(cache_key) % len(candle_miss_locks)]
        with miss_lock:
            with candle_cache_lock:
                cached = candle_cache.get(cache_key)
                if cached and 0 <= time.monotonic() - cached[0] < candle_cache_ttl_seconds:
                    return JSONResponse(cached[1], headers={"Cache-Control": "no-store"})
            segment, sid = known[body.symbol]
            instrument = "INDEX" if body.symbol in indices else "EQUITY"
            args = {"securityId": str(sid), "exchangeSegment": segment,
                    "instrument": instrument, "interval": str(body.interval),
                    "fromDate": body.from_date.isoformat() + " 09:15:00",
                    "toDate": (body.to_date + timedelta(days=1)).isoformat() + " 00:00:00"}
            try:
                result = provider().intraday(args)
            except HTTPException:
                raise
            except Exception as exc:
                try:
                    from .dhan_feed import DhanRateLimitError, DhanFeedError
                except ImportError:
                    from dhan_feed import DhanRateLimitError, DhanFeedError
                category=("rate_limited" if isinstance(exc, DhanRateLimitError)
                          else "auth_unavailable" if isinstance(exc, DhanFeedError)
                          and "token expired or data access not entitled" in str(exc)
                          else "upstream_error")
                market_diagnostic("candles", body.symbol, "provider", category)
                provider_read_error(exc, "Clone Dhan candles unavailable")
            try:
                fields = ["timestamp", "open", "high", "low", "close", "volume"]
                arrays = [result[key] for key in fields]
                if (result.get("status") == "failure" or
                        any(not isinstance(v, list) for v in arrays) or
                        any(len(a) != len(arrays[0]) for a in arrays) or
                        len(arrays[0]) > 5000):
                    raise ValueError()
                bars = []
                for ts, op, high, low, close, vol in zip(*arrays):
                    if any(type(v) not in (int, float) for v in (ts, op, high, low, close, vol)):
                        raise ValueError()
                    vals = (float(ts), float(op), float(high), float(low), float(close), float(vol))
                    if (not all(math.isfinite(v) for v in vals) or ts <= 0
                            or min(op, high, low, close) <= 0 or vol < 0
                            or high < max(op, low, close) or low > min(op, high, close)):
                        raise ValueError()
                    bars.append([int(ts), float(op), float(high), float(low),
                                 float(close), float(vol)])
                if any(bars[i][0] >= bars[i + 1][0] for i in range(len(bars)-1)):
                    raise ValueError()
            except (KeyError, TypeError, ValueError, OverflowError):
                market_diagnostic("candles", body.symbol, "validation", "invalid_bars")
                raise HTTPException(502, "Clone Dhan candle response invalid") from None
            payload = {
                "source": "dhan", "symbol": body.symbol,
                "interval": str(body.interval) + "m", "bars": bars,
                "last_candle_timestamp": bars[-1][0] if bars else None,
                "freshness": "historical_unverified" if bars else "no_candles_available",
                "live_orders_enabled": False}
            if bars:
                with candle_cache_lock:
                    candle_cache[cache_key] = (time.monotonic(), payload)
                    if len(candle_cache) > candle_cache_max_entries:
                        candle_cache.pop(min(candle_cache, key=lambda k: candle_cache[k][0]))
            return JSONResponse(payload, headers={"Cache-Control": "no-store"})

    @app.post("/clone-v2/market/options/expiries")
    def market_option_expiries(body: MarketUnderlying,
                               x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if body.symbol not in option_known or option_known[body.symbol][0] not in ("IDX_I", "BSE_I", "NSE_EQ"):
            raise HTTPException(422, "Unmapped Clone option underlying")
        try:
            dates = provider().option_expiries(*option_known[body.symbol])
        except HTTPException:
            raise
        except Exception as exc:
            provider_read_error(exc, "Clone Dhan option expiry unavailable")
        if not isinstance(dates, list) or not dates:
            raise HTTPException(422, "No verified Clone listed expiry")
        return JSONResponse({"source": "dhan", "symbol": body.symbol,
                             "expiries": dates, "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    @app.post("/clone-v2/market/options/chain")
    def market_option_chain(body: MarketOptionChain,
                            x_botking_key: Optional[str] = Header(default=None)):
        authorized(x_botking_key)
        if (body.symbol not in option_known or
                option_known[body.symbol][0] not in ("IDX_I", "BSE_I", "NSE_EQ") or
                body.expiry < datetime.now(timezone(timedelta(hours=5, minutes=30))).date()):
            raise HTTPException(422, "Invalid Clone option underlying or expiry")
        try:
            try:
                from .dhan_option_metrics import (calculate_option_metrics, listed_atm_window,
                                                  OptionMetricsUnavailable)
            except ImportError:
                from dhan_option_metrics import (calculate_option_metrics, listed_atm_window,
                                                 OptionMetricsUnavailable)
            raw = provider().option_chain(*option_known[body.symbol], body.expiry.isoformat())
            metrics = calculate_option_metrics(raw)
            raw_data = raw.get("data", {})
            spot = raw_data.get("last_price") if isinstance(raw_data, dict) else None
            window, window_status = None, "underlying_spot_unavailable"
            if type(spot) in (int, float) and math.isfinite(spot) and spot > 0:
                window_status = "listed_window_unavailable"
                try:
                    window = listed_atm_window(raw, spot=spot)
                    window_status = "available"
                except OptionMetricsUnavailable:
                    pass
        except HTTPException:
            raise
        except Exception as exc:
            provider_read_error(exc, "Clone Dhan option chain unavailable")
        return JSONResponse({"source": "dhan", "symbol": body.symbol,
                             "expiry": body.expiry.isoformat(), **metrics,
                             "atm_window": window, "atm_window_status": window_status,
                             "live_orders_enabled": False},
                            headers={"Cache-Control": "no-store"})

    return app
